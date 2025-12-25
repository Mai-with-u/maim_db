#!/usr/bin/env python3
"""
回复验证脚本 - 使用API Key连接回复后端并发送测试问好消息

用法：
    python verify_reply_with_key.py <API_KEY>

示例：
    python verify_reply_with_key.py maim_xxx...

依赖：
    - maim_message客户端库
    - MaiMBot回复后端正在运行
"""

import argparse
import asyncio
import logging
import os
import sys
import time
import uuid

# Mute noisy logs
logging.getLogger("asyncio").setLevel(logging.CRITICAL)
logging.getLogger("websockets").setLevel(logging.CRITICAL)

# Ensure local source code is importable
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
MAIM_DB_SRC = os.path.join(ROOT, 'maim_db', 'src')
MAIM_MESSAGE_SRC = os.path.join(ROOT, 'maim_message', 'src')
for p in (MAIM_DB_SRC, MAIM_MESSAGE_SRC):
    if p not in sys.path:
        sys.path.insert(0, p)

# Imports from project
from maim_message.api_message_base import (
    APIMessageBase,
    BaseMessageInfo,
    MessageDim,
    Seg,
    SenderInfo,
    UserInfo,
)
from maim_message.client import create_client_config
from maim_message.client_ws_api import WebSocketClient

# Configuration
WS_URL = os.getenv("MAIM_MESSAGE_WS_URL", "ws://localhost:18042/ws")
TEST_MESSAGE = "你好，这是端到端验证测试消息！"


async def verify_reply(api_key: str, message: str = TEST_MESSAGE):
    """
    使用给定的API Key连接回复后端，发送测试消息并等待回复

    Args:
        api_key: MaimBot的API Key
        message: 要发送的测试消息，默认为问好消息

    Returns:
        bool: 测试是否通过
    """
    print("🚀 开始回复验证测试")
    print(f"   API Key : {api_key[:15]}...")
    print(f"   WS URL  : {WS_URL}")
    print(f"   测试消息: {message}")

    # Configure WebSocket Client
    client_config = create_client_config(WS_URL, api_key, platform="test")
    client = WebSocketClient(client_config)
    response_queue = asyncio.Queue()

    async def on_message(msg: APIMessageBase, metadata: dict):
        await response_queue.put(msg)

    if client.default_config:
        client.default_config.on_message = on_message

    # Start Client
    await client.start()
    connected = await client.connect()
    if not connected:
        print("❌ 无法连接到WebSocket服务器")
        return False
    print("   ✅ WebSocket连接成功")

    success = False
    try:
        # Construct Message
        ts = time.time()
        session_id = uuid.uuid4().hex[:8]

        user_info = UserInfo(
            user_id=f"u_{session_id}",
            user_nickname=f"验证测试用户_{session_id}",
            platform="test"
        )
        sender_info = SenderInfo(user_info=user_info)
        msg_info = BaseMessageInfo(
            platform="test",
            message_id=f"msg_{ts}",
            time=ts,
            sender_info=sender_info
        )
        seg = Seg(type="text", data=message)

        # Pass API Key in MessageDim for auth
        md = MessageDim.from_dict({"api_key": api_key, "platform": "test"})
        api_msg = APIMessageBase(message_info=msg_info, message_segment=seg, message_dim=md)

        print(f"   📤 发送消息: {message}")
        sent = await client.send_message(api_msg)
        if not sent:
            print("❌ 消息发送失败")
            return False

        # Wait for Reply
        print("   ⏳ 等待回复...")
        try:
            reply = await asyncio.wait_for(response_queue.get(), timeout=30.0)
            reply_text = reply.message_segment.data if reply.message_segment else ""
            print(f"   📩 收到回复: {reply_text}")

            if reply_text:
                print("\n✅ 回复验证测试通过！")
                success = True
            else:
                print("\n❌ 收到空回复")
                success = False

        except asyncio.TimeoutError:
            print("\n❌ 等待回复超时 (30秒)")
            success = False

    finally:
        await client.disconnect()
        await client.stop()

    return success


def main():
    parser = argparse.ArgumentParser(
        description="使用API Key验证Bot回复功能",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python verify_reply_with_key.py maim_abc123def456...
  python verify_reply_with_key.py maim_abc123 --message "你好吗？"

环境变量:
  MAIM_MESSAGE_WS_URL  WebSocket服务地址 (默认: ws://localhost:18042/ws)
        """
    )
    parser.add_argument(
        "api_key",
        help="MaimBot的API Key"
    )
    parser.add_argument(
        "--message", "-m",
        default=TEST_MESSAGE,
        help=f"测试消息内容 (默认: {TEST_MESSAGE})"
    )
    args = parser.parse_args()

    success = asyncio.run(verify_reply(args.api_key, args.message))
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
