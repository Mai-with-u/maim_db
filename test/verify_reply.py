
import asyncio
import aiohttp
import sys
import json
import time

async def main():
    if len(sys.argv) < 2:
        print("Usage: python verify_reply.py <API_KEY>")
        sys.exit(1)

    api_key = sys.argv[1]
    url = f"ws://localhost:18042/api/ws?api_key={api_key}"
    
    print(f"Connecting to {url}...")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(url) as ws:
                print("Connected!")
                
                # Construct a standard maim_message payload
                payload = {
                    "message_info": {
                        "platform": "test_script",
                        "message_id": f"test_{int(time.time())}",
                        "time": time.time(),
                        "user_info": {
                            "user_id": "e2e_tester",
                            "user_nickname": "E2E Tester",
                            "platform": "test_script"
                        },
                        "group_info": {
                            "group_id": "e2e_group",
                            "platform": "test_script"
                        },
                        "additional_config": {
                            # Also inject key here just in case query param isn't enough
                            "api_key": api_key,
                            "api_platform": "test_script"
                        }
                    },
                    "message_segment": {
                        "type": "seglist",
                        "data": [
                            {"type": "text", "data": "Hello. This is an E2E verification message."}
                        ]
                    },
                    "message_dim": {
                         "api_key": api_key,
                         "platform": "test_script"
                    }
                }
                
                print("Sending 'Hello' message...")
                await ws.send_json(payload)
                
                # Wait for reply
                print("Waiting for reply...")
                timeout = 30
                start_time = time.time()
                
                while time.time() - start_time < timeout:
                    try:
                        msg = await asyncio.wait_for(ws.receive(), timeout=5.0)
                        
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            data = json.loads(msg.data)
                            print(f"Received message: {data}")
                            
                            # Basic validation: check if it's a reply
                            # Note: Reply structure might vary, but usually has message_segment
                            if "message_segment" in data:
                                segs = data["message_segment"]["data"]
                                text = "".join([s["data"] for s in segs if s["type"] == "text"])
                                print(f"Reply Text: {text}")
                                if text:
                                    print("TEST PASSED: Received non-empty reply.")
                                    return
                        elif msg.type == aiohttp.WSMsgType.CLOSED:
                            print("Connection closed by server.")
                            break
                        elif msg.type == aiohttp.WSMsgType.ERROR:
                            print("Connection error.")
                            break
                            
                    except asyncio.TimeoutError:
                        print("Waiting...")
                        continue
                
                print("Timeout waiting for reply.")
                sys.exit(1)

    except Exception as e:
        print(f"Test Failed with exception: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
