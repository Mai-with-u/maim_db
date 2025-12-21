import os
import sys
import time
import logging
import asyncio
import aiohttp
import uuid

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

# 并发数配置
CONCURRENCY = 3

async def run_single_user_flow(user_index: int, maimconfig_url: str, ws_url: str):
    """Execution flow for a single simulated user"""
    print(f"[User {user_index}] Starting flow...")
    
    # 唯一标识
    ts = int(time.time())
    unique_suffix = f"{ts}_{user_index}_{uuid.uuid4().hex[:4]}"
    tenant_name = f"test_tenant_{unique_suffix}"
    
    api_key_id = None
    agent_id = None
    tenant_id = None

    try:
        async with aiohttp.ClientSession() as session:
            # 1. 创建 Tenant
            tenant_payload = {
                "tenant_name": tenant_name,
                "tenant_type": "personal",
                "description": f"integration test user {user_index}",
                "contact_email": None,
                "tenant_config": {},
            }
            async with session.post(f"{maimconfig_url}/tenants", json=tenant_payload) as resp:
                assert resp.status in (200, 201), f"[User {user_index}] Create tenant failed: {resp.status}"
                tenant_resp = await resp.json()
            tenant_id = tenant_resp.get("data", {}).get("id")
            assert tenant_id, f"[User {user_index}] No tenant_id returned"

            # 2. 创建 Agent
            agent_payload = {
                "tenant_id": tenant_id,
                "name": f"agent_{unique_suffix}",
                "description": "test agent",
                "template_id": None,
                "config": {
                    "persona": "integration_test_bot",
                    "custom_setting": "integration_test_value"
                },
            }
            async with session.post(f"{maimconfig_url}/agents", json=agent_payload) as resp:
                assert resp.status in (200, 201), f"[User {user_index}] Create agent failed: {resp.status}"
                agent_resp = await resp.json()
            agent_id = agent_resp.get("data", {}).get("id")
            assert agent_id, f"[User {user_index}] No agent_id returned"

            # 3. 创建 API Key
            api_key_payload = {
                "tenant_id": tenant_id,
                "agent_id": agent_id,
                "name": f"key_{unique_suffix}",
                "description": "integration test key",
                "permissions": [],
                "expires_at": None,
            }
            async with session.post(f"{maimconfig_url}/api-keys", json=api_key_payload) as resp:
                assert resp.status in (200, 201), f"[User {user_index}] Create API Key failed: {resp.status}"
                api_key_resp = await resp.json()
            api_key_data = api_key_resp.get("data", {})
            api_key_id = api_key_data.get("api_key_id")
            api_key_value = api_key_data.get("api_key")
            assert api_key_id and api_key_value, f"[User {user_index}] No API Key returned"

        # 4. WebSocket 连接与消息发送
        client_config = create_client_config(ws_url, api_key_value, platform="test")
        client = WebSocketClient(client_config)
        response_queue = asyncio.Queue()

        async def on_message(message: APIMessageBase, metadata: dict):
            await response_queue.put(message)

        if client.default_config:
            client.default_config.on_message = on_message

        await client.start()
        connected = await client.connect()
        assert connected, f"[User {user_index}] Cannot connect to WS"

        try:
            user_info = UserInfo(user_id=f"u_{unique_suffix}", user_nickname=f"Tester_{user_index}", platform="test")
            sender_info = SenderInfo(user_info=user_info)
            msg_info = BaseMessageInfo(
                platform="test", message_id=f"msg_{unique_suffix}", time=time.time(), sender_info=sender_info
            )
            seg = Seg(type="text", data=f"你好 (User {user_index})")
            
            # 使用 message_dim 传递 API Key
            md = MessageDim.from_dict({"api_key": api_key_value, "platform": "test"})
            api_msg = APIMessageBase(message_info=msg_info, message_segment=seg, message_dim=md)

            print(f"[User {user_index}] Sending message...")
            sent = await client.send_message(api_msg)
            assert sent, f"[User {user_index}] Send message failed"

            try:
                reply = await asyncio.wait_for(response_queue.get(), timeout=60.0)
                print(f"[User {user_index}] Received reply: {reply.message_segment.data}")
            except asyncio.TimeoutError:
                print(f"[User {user_index}] Wait for reply timeout")
                raise

        finally:
            await client.disconnect()
            await client.stop()

    except Exception as e:
        print(f"[User {user_index}] FAILED: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        # Cleanup
        if tenant_id: # Only verify cleanup if we created something
             async with aiohttp.ClientSession() as session:
                try:
                    if api_key_id:
                        async with session.delete(f"{maimconfig_url}/api-keys/{api_key_id}") as resp:
                            if resp.status in (200, 204):
                                print(f"[User {user_index}] Deleted API Key: {api_key_id}")
                            else:
                                print(f"[User {user_index}] Failed to delete API Key {api_key_id}: {resp.status}")

                    if agent_id:
                        async with session.delete(f"{maimconfig_url}/agents/{agent_id}") as resp:
                            if resp.status in (200, 204):
                                print(f"[User {user_index}] Deleted Agent: {agent_id}")
                            else:
                                print(f"[User {user_index}] Failed to delete Agent {agent_id}: {resp.status}")

                    if tenant_id:
                        async with session.delete(f"{maimconfig_url}/tenants/{tenant_id}") as resp:
                            if resp.status in (200, 204):
                                print(f"[User {user_index}] Deleted Tenant: {tenant_id}")
                            else:
                                print(f"[User {user_index}] Failed to delete Tenant {tenant_id}: {resp.status}")
                except Exception as e:
                    print(f"[User {user_index}] Cleanup failed: {e}")

    print(f"[User {user_index}] Flow completed successfully")
    return True

async def main():
    # 自定义异常处理器
    def ignore_asyncio_noise(loop, context):
        message = context.get("message", "")
        if "Event loop is closed" in message or "Task was destroyed" in message:
            return
        if "connection_loop" in str(context.get("future", "")):
            return
        loop.default_exception_handler(context)

    loop = asyncio.get_running_loop()
    loop.set_exception_handler(ignore_asyncio_noise)

    # 初始化 maim_db
    try:
        init_database()
    except Exception:
        pass

    maimconfig_url = os.getenv("MAIMCONFIG_API_URL", "http://localhost:8000/api/v2")
    ws_url = os.getenv("MAIM_MESSAGE_WS_URL", "ws://localhost:18042/ws")

    print(f"Starting concurrent test with {CONCURRENCY} users...")
    tasks = [run_single_user_flow(i, maimconfig_url, ws_url) for i in range(CONCURRENCY)]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Check results
    failed_count = 0
    for i, res in enumerate(results):
        if isinstance(res, Exception):
            print(f"User {i} failed with exception: {res}")
            failed_count += 1
        elif not res:
            print(f"User {i} failed (returned False/None)")
            failed_count += 1
    
    if failed_count > 0:
        print(f"❌ Test FAILED with {failed_count}/{CONCURRENCY} failures")
        sys.exit(1)
    else:
        print("✅ All concurrent flows passed successfully")

if __name__ == "__main__":
    asyncio.run(main())
