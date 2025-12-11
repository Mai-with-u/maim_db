from maim_message.api_message_base import BaseMessageInfo
import inspect

print(f"Fields: {BaseMessageInfo.__dataclass_fields__.keys()}")
try:
    obj = BaseMessageInfo(platform="test", message_id="1", time=1.0)
    print(f"Has user_info? {hasattr(obj, 'user_info')}")
    obj.user_info = "test"
    print("Can set user_info")
except Exception as e:
    print(f"Error: {e}")
