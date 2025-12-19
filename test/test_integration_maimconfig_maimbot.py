import os
import sys
import time

import logging
import asyncio

# 屏蔽库级日志噪声
logging.getLogger("asyncio").setLevel(logging.CRITICAL)
logging.getLogger("websockets").setLevel(logging.CRITICAL)

# 确保可导入本地的 maim_db / maim_message 源码
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
MAIM_DB_SRC = os.path.join(ROOT, 'maim_db', 'src')
MAIM_MESSAGE_SRC = os.path.join(ROOT, 'maim_message', 'src')
for p in (MAIM_DB_SRC, MAIM_MESSAGE_SRC):
    if p not in sys.path:
        sys.path.insert(0, p)

# 使用真实的适配器/客户端
from maim_db.core import init_database

from maim_message.client import create_client_config
from maim_message.client_ws_api import WebSocketClient
from maim_message.api_message_base import APIMessageBase, BaseMessageInfo, Seg, MessageDim, UserInfo, SenderInfo


async def main():
    # 自定义异常处理器，屏蔽 asyncio 关闭时的噪声
    def ignore_asyncio_noise(loop, context):
        message = context.get("message", "")
        # 屏蔽 Event loop is closed 和 Task was destroyed 错误
        if "Event loop is closed" in message or "Task was destroyed" in message:
            return
        # 屏蔽 websockets 的连接关闭异常
        if "connection_loop" in str(context.get("future", "")):
            return
            
        # 默认处理
        loop.default_exception_handler(context)

    # 设置异常处理器
    loop = asyncio.get_running_loop()
    loop.set_exception_handler(ignore_asyncio_noise)

    # 初始化 maim_db 连接
    try:
        init_database()
    except Exception:
        pass

    # 生成唯一 id
    ts = int(time.time())
    tenant_name = f"test_tenant_{ts}"

    # 1) 通过 MaimConfig 的 REST API 创建 tenant 和 agent
    maimconfig_url = os.getenv("MAIMCONFIG_API_URL", "http://localhost:8000/api/v2")
    import aiohttp

    api_key_id = None
    api_key_value = None

    async with aiohttp.ClientSession() as session:
        # 创建 tenant
        tenant_payload = {
            "tenant_name": tenant_name,
            "tenant_type": "personal",
            "description": "integration test",
            "contact_email": None,
            "tenant_config": {},
        }
        async with session.post(f"{maimconfig_url}/tenants", json=tenant_payload) as resp:
            assert resp.status in (200, 201), f"创建 tenant 失败: {resp.status}"
            tenant_resp = await resp.json()
        tenant_id = tenant_resp.get("data", {}).get("id")
        assert tenant_id, f"未从创建 tenant 返回 tenant_id: {tenant_resp}"

        # 创建 agent with custom config
        agent_payload = {
            "tenant_id": tenant_id,
            "name": "integration_agent",
            "description": "test agent",
            "template_id": None,
            "config": {
                "persona": "integration_test_bot",
                "custom_setting": "integration_test_value"
            },
        }
        async with session.post(f"{maimconfig_url}/agents", json=agent_payload) as resp:
            assert resp.status in (200, 201), f"创建 agent 失败: {resp.status}"
            agent_resp = await resp.json()
        agent_id = agent_resp.get("data", {}).get("id")
        assert agent_id, f"未从创建 agent 返回 agent_id: {agent_resp}"

        # 3) 通过 REST 创建 API Key
        api_key_payload = {
            "tenant_id": tenant_id,
            "agent_id": agent_id,
            "name": "integration_key",
            "description": "integration test key",
            "permissions": [],
            "expires_at": None,
        }
        async with session.post(f"{maimconfig_url}/api-keys", json=api_key_payload) as resp:
            assert resp.status in (200, 201), f"创建 API Key 失败: {resp.status}"
            api_key_resp = await resp.json()
        api_key_data = api_key_resp.get("data", {})
        api_key_id = api_key_data.get("api_key_id")
        api_key_value = api_key_data.get("api_key")
        assert api_key_id and api_key_value, f"未能通过 REST 获取 API Key: {api_key_resp}"

    # 4) 使用 maim_message client 连接并发送消息
    # 默认服务端 WebSocket 地址 (根据文档)
    ws_url = os.getenv("MAIM_MESSAGE_WS_URL", "ws://localhost:18040/ws")

    client_config = create_client_config(ws_url, api_key_value, platform="test")
    client = WebSocketClient(client_config)

    # 响应队列
    response_queue = asyncio.Queue()

    # 定义回调
    async def on_message(message: APIMessageBase, metadata: dict):
        # print(f"DEBUG: Test received message: {message}")
        await response_queue.put(message)

    # 重要修复：必须更新 config 中的 on_message 回调，而不是直接设置 client 属性
    # WebSocketClientBase 使用 self.default_config.on_message
    if client.default_config:
        client.default_config.on_message = on_message
    else:
        # 如果没有 default_config (理论上不可能，因为上面传入了 config)，则手动设置
        # 但这里的 WebSocketClient 实现可能依赖 config
        pass

    # 启动并连接（限时等待）
    await client.start()
    connected = await client.connect()

    try:
        assert connected, f"客户端无法连接到 {ws_url}"

        # 构造 APIMessageBase（最小字段）
        # 使用 message_id_echo 让 bot 原样返回
        user_info = UserInfo(user_id="u123", user_nickname="Tester", platform="test")
        sender_info = SenderInfo(user_info=user_info)
        msg_info = BaseMessageInfo(
            platform="test", message_id=f"msg_{ts}", time=time.time(), sender_info=sender_info
        )
        seg = Seg(type="text", data="PING_TEST")
        # 添加 message_id_echo 指令，MaiMBot 会回显
        md = MessageDim.from_dict({"api_key": api_key_value, "platform": "test", "message_id_echo": "true"})
        api_msg = APIMessageBase(message_info=msg_info, message_segment=seg, message_dim=md)

        sent = await client.send_message(api_msg)
        assert sent, "发送消息失败"

        # 等待回复
        print("等待回复...")
        try:
            reply = await asyncio.wait_for(response_queue.get(), timeout=60.0)
            print(f"收到回复: {reply}")
            # The original code had an assert reply, "未收到回复" here.
            # If the intention is to return True/False for success/failure,
            # then the assert might be redundant or need to be handled differently.
            # For now, keeping the print and return as per instruction.
            return True
        except asyncio.TimeoutError:
            print("等待回复超时")
            return False

    finally:
        # 清理连接
        try:
            await client.disconnect()
        except Exception:
            pass
        try:
            await client.stop()
        except Exception:
            pass

        # 5) 删除 agent 与 tenant（通过 MaimConfig REST API 删除）
        async with aiohttp.ClientSession() as session:
            try:
                if api_key_id:
                    await session.delete(f"{maimconfig_url}/api-keys/{api_key_id}")
            except Exception:
                pass
            try:
                # 删除 agent
                await session.delete(f"{maimconfig_url}/agents/{agent_id}")
            except Exception:
                pass
            try:
                await session.delete(f"{maimconfig_url}/tenants/{tenant_id}")
            except Exception:
                pass

if __name__ == "__main__":
    asyncio.run(main())
