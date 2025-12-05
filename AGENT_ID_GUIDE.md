# Agent ID 自动写入机制验证指南

## 概述

本指南详细说明如何验证和调试ORM基座替换中的agent_id自动写入机制，确保多租户数据隔离正常工作。

## 🔍 Agent ID 自动写入机制

### 核心组件

1. **BusinessBaseModel** - 支持多租户的基类
2. **上下文管理器** - 线程安全的agent_id传递
3. **方法重写** - save(), create(), select()的自动处理

### 自动写入流程

```mermaid
graph TD
    A[业务操作] --> B{检查SaaS模式}
    B -->|是| C[使用BusinessBaseModel]
    B -->|否| D[使用原BaseModel]

    C --> E[save()方法]
    E --> F{检查agent_id}
    F -->|为空| G[从上下文获取]
    F -->|已设置| H[直接保存]
    G --> I[设置agent_id]
    I --> H

    C --> J[create()方法]
    J --> K{查询中有agent_id}
    K -->|否| L[添加当前agent_id]
    K -->|是| M[直接创建]
    L --> M

    C --> N[select()方法]
    N --> O[添加WHERE agent_id过滤]
    O --> P[返回查询]
```

## ✅ 验证步骤

### 1. 检查模型继承关系

```python
from src.common.database.database_model import BaseModel, ChatStreams

# 检查BaseModel类型
print(f"BaseModel: {BaseModel}")
print(f"是否包含agent_id字段: {hasattr(BaseModel, 'agent_id')}")

# 检查业务模型
print(f"ChatStreams继承: {ChatStreams.__bases__}")
print(f"ChatStreams是否有agent_id: {hasattr(ChatStreams, 'agent_id')}")
```

**预期结果:**
- SQLite模式: BaseModel不包含agent_id
- SaaS模式: BaseModel = BusinessBaseModel，包含agent_id

### 2. 验证上下文管理器

```python
from src.core.context_manager import agent_context_manager, get_current_agent_id

# 测试上下文管理
test_agent_id = "agent_test_123"

with agent_context_manager(test_agent_id):
    current_id = get_current_agent_id()
    print(f"当前agent_id: {current_id}")  # 应该是 "agent_test_123"
```

### 3. 测试自动写入机制

```python
# 模拟业务操作
with agent_context_manager("agent_demo_456"):
    # 创建记录
    try:
        message = Messages.create(
            chat_id="test_chat_001",
            processed_text="Hello World",
            user_message="Hello",
            assistant_message="Hi there!"
        )
        print(f"创建成功，agent_id: {message.agent_id}")
    except Exception as e:
        print(f"创建失败: {e}")
```

### 4. 验证查询过滤

```python
with agent_context_manager("agent_test_789"):
    # 查询记录 - 应该自动添加agent_id过滤
    messages = Messages.select()

    # 检查生成的SQL查询
    print(f"查询SQL: {str(messages)}")

    # 应该包含: WHERE agent_id = 'agent_test_789'
```

## 🐛 调试指南

### 常见问题

#### 1. agent_id字段不存在

**症状:** `AttributeError: 'BusinessBaseModel' object has no attribute 'agent_id'`

**原因:** BaseModel没有正确替换为BusinessBaseModel

**解决方案:**
```python
# 检查SAAS_MODE标志
from src.common.database.database import SAAS_MODE
print(f"SAAS_MODE: {SAAS_MODE}")

# 检查导入路径
import sys
sys.path.append('/path/to/maim_db/src')
from core.models import BusinessBaseModel
```

#### 2. 上下文agent_id为空

**症状:** `ValueError: 业务模型必须设置 agent_id`

**原因:** 没有在上下文中设置agent_id

**解决方案:**
```python
# 确保使用上下文管理器
with agent_context_manager("your_agent_id"):
    # 在这里进行数据库操作
    pass
```

#### 3. 查询没有agent_id过滤

**症状:** 返回其他租户的数据

**原因:** select()方法没有被正确重写

**解决方案:**
```python
# 检查当前模型类型
from src.common.database.database_model import Messages
print(f"Messages类型: {Messages}")
print(f"select方法: {Messages.select}")

# 确认是BusinessBaseModel的子类
from core.models import BusinessBaseModel
print(f"是否继承BusinessBaseModel: {issubclass(Messages, BusinessBaseModel)}")
```

### 调试工具

#### 1. 检查当前模式

```python
def debug_current_mode():
    from src.common.database.database import SAAS_MODE, db

    print(f"=== 当前模式调试 ===")
    print(f"SAAS_MODE: {SAAS_MODE}")
    print(f"数据库类型: {type(db).__name__}")

    if SAAS_MODE:
        print("✅ SaaS模式已启用")
    else:
        print("❌ SQLite模式（回退）")

debug_current_mode()
```

#### 2. 验证agent_id字段

```python
def debug_agent_id_field():
    from src.common.database.database_model import BaseModel, ChatStreams

    print(f"=== Agent ID 字段调试 ===")

    # 检查BaseModel
    if hasattr(BaseModel, 'agent_id'):
        print(f"✅ BaseModel包含agent_id: {BaseModel.agent_id}")
    else:
        print("❌ BaseModel不包含agent_id")

    # 检查业务模型
    if hasattr(ChatStreams, 'agent_id'):
        print(f"✅ ChatStreams包含agent_id: {ChatStreams.agent_id}")
    else:
        print("❌ ChatStreams不包含agent_id")

debug_agent_id_field()
```

#### 3. 测试完整流程

```python
def debug_complete_flow():
    from src.common.database.database_model import Messages
    from src.core.context_manager import agent_context_manager

    print(f"=== 完整流程测试 ===")

    test_agent_id = "debug_agent_001"

    with agent_context_manager(test_agent_id):
        print(f"设置agent_id: {test_agent_id}")

        # 创建实例
        try:
            message = Messages(
                chat_id="debug_chat_001",
                processed_text="Debug message"
            )

            # 检查agent_id是否自动设置
            print(f"实例agent_id: {getattr(message, 'agent_id', '未设置')}")

            # 模拟保存
            message.save()
            print(f"保存后agent_id: {message.agent_id}")

        except Exception as e:
            print(f"流程测试失败: {e}")

debug_complete_flow()
```

## 🔧 生产环境验证

### 1. 数据库表结构验证

```sql
-- 检查表是否包含agent_id字段
SELECT table_name, column_name
FROM information_schema.columns
WHERE table_name IN ('chat_streams', 'messages', 'llm_usage')
AND column_name = 'agent_id';

-- 检查agent_id索引
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'messages'
AND indexdef LIKE '%agent_id%';
```

### 2. 数据隔离验证

```python
# 使用不同的agent_id创建数据
with agent_context_manager("agent_A"):
    messages_a = Messages.create(
        chat_id="shared_chat",
        processed_text="Agent A message"
    )

with agent_context_manager("agent_B"):
    messages_b = Messages.create(
        chat_id="shared_chat",
        processed_text="Agent B message"
    )

# 验证数据隔离
with agent_context_manager("agent_A"):
    messages_for_a = list(Messages.select())
    print(f"Agent A看到 {len(messages_for_a)} 条记录")

with agent_context_manager("agent_B"):
    messages_for_b = list(Messages.select())
    print(f"Agent B看到 {len(messages_for_b)} 条记录")

# 预期结果：每个agent只看到自己的数据
```

## 📊 性能监控

### 1. 查询性能检查

```python
import time

def monitor_query_performance():
    from src.common.database.database_model import Messages
    from src.core.context_manager import agent_context_manager

    with agent_context_manager("perf_test_agent"):
        # 测试查询性能
        start_time = time.time()
        messages = list(Messages.select().limit(100))
        end_time = time.time()

        print(f"查询100条记录耗时: {end_time - start_time:.4f}秒")
        print(f"返回记录数: {len(messages)}")

monitor_query_performance()
```

## 🎯 最佳实践

### 1. 上下文管理

```python
# 推荐：使用上下文管理器
with agent_context_manager("agent_id_123"):
    # 所有数据库操作
    result = Messages.select()
    message = Messages.create(...)

# 避免：手动设置agent_id
set_current_agent_id("agent_id_123")  # 容易忘记清除
try:
    # 数据库操作
    pass
finally:
    clear_current_agent_id()  # 需要手动清理
```

### 2. 错误处理

```python
from src.core.context_manager import get_current_agent_id
from src.common.database.database_model import Messages

def safe_create_message(**kwargs):
    """安全创建消息，包含完整的错误处理"""
    current_agent = get_current_agent_id()
    if not current_agent:
        raise ValueError("必须设置agent_id上下文")

    try:
        return Messages.create(**kwargs)
    except Exception as e:
        print(f"创建消息失败: {e}")
        raise
```

### 3. 测试策略

```python
# 单元测试示例
import unittest
from src.core.context_manager import agent_context_manager
from src.common.database.database_model import Messages

class TestAgentIdIsolation(unittest.TestCase):

    def setUp(self):
        self.agent_a = "test_agent_A"
        self.agent_b = "test_agent_B"

    def test_data_isolation(self):
        # 为agent A创建数据
        with agent_context_manager(self.agent_a):
            Messages.create(chat_id="test", processed_text="A's message")

        # 为agent B创建数据
        with agent_context_manager(self.agent_b):
            Messages.create(chat_id="test", processed_text="B's message")

        # 验证agent A只能看到自己的数据
        with agent_context_manager(self.agent_a):
            messages = list(Messages.select())
            self.assertEqual(len(messages), 1)
            self.assertEqual(messages[0].processed_text, "A's message")

        # 验证agent B只能看到自己的数据
        with agent_context_manager(self.agent_b):
            messages = list(Messages.select())
            self.assertEqual(len(messages), 1)
            self.assertEqual(messages[0].processed_text, "B's message")
```

通过本指南，您可以全面验证agent_id自动写入机制是否正常工作，确保多租户数据隔离的可靠性和安全性。