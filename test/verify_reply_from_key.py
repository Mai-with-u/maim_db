
import os
import sys
import time
import logging
import asyncio
import argparse
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
from maim_message.client import create_client_config
from maim_message.client_ws_api import WebSocketClient
from maim_message.api_message_base import APIMessageBase, BaseMessageInfo, Seg, MessageDim, UserInfo, SenderInfo

# Configuration
WS_URL = os.getenv("MAIM_MESSAGE_WS_URL", "ws://localhost:18042/ws")

async def verify_reply(api_key: str):
    print(f"🚀 Starting Reply Verification with API Key: {api_key[:10]}...")
    print(f"   WS URL : {WS_URL}")

    # Configure WebSocket Client
    client_config = create_client_config(WS_URL, api_key, platform="test")
    client = WebSocketClient(client_config)
    response_queue = asyncio.Queue()

    async def on_message(message: APIMessageBase, metadata: dict):
        await response_queue.put(message)

    if client.default_config:
        client.default_config.on_message = on_message

    # Start Client
    await client.start()
    connected = await client.connect()
    if not connected:
        print("❌ Failed to connect to WebSocket Server")
        sys.exit(1)
    print("   ✅ Connected to WebSocket")

    try:
        # Construct Message
        ts = time.time()
        username = f"verify_user_{uuid.uuid4().hex[:4]}"
        user_info = UserInfo(user_id=f"u_{username}", user_nickname=f"Tester_{username}", platform="test")
        sender_info = SenderInfo(user_info=user_info)
        msg_info = BaseMessageInfo(
            platform="test", message_id=f"msg_{ts}", time=ts, sender_info=sender_info
        )
        seg = Seg(type="text", data="Hello") # Simple check
        
        # IMPORTANT: Pass API Key in MessageDim for auth
        md = MessageDim.from_dict({"api_key": api_key, "platform": "test"})
        api_msg = APIMessageBase(message_info=msg_info, message_segment=seg, message_dim=md)

        print("   📤 Sending message: Hello")
        sent = await client.send_message(api_msg)
        if not sent:
            print("❌ Failed to send message")
            sys.exit(1)

        # Wait for Reply
        print("   ⏳ Waiting for reply...")
        try:
            reply = await asyncio.wait_for(response_queue.get(), timeout=30.0)
            reply_text = reply.message_segment.data
            print(f"   📩 Received reply: {reply_text}")
            
            if reply_text:
                 print("\n✅ REPLY VERIFICATION PASSED!")
            else:
                 print("\n❌ Received empty reply")
                 sys.exit(1)

        except asyncio.TimeoutError:
            print("\n❌ Timed out waiting for bot reply")
            sys.exit(1)

    finally:
        await client.disconnect()
        await client.stop()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Verify Bot Reply with API Key")
    parser.add_argument("api_key", help="The API Key to use for verification")
    args = parser.parse_args()
    
    asyncio.run(verify_reply(args.api_key))
