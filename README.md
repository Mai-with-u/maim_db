# AI Project Core - 统一数据库核心库

本库提供AI SaaS系统的统一数据库架构，支持多租户数据隔离和ORM基座替换。

## 核心特性

- **控制面与数据面分离**：系统级模型（User、Tenant、Agent等）与业务级模型（ChatHistory、Logs等）分离管理
- **多租户数据隔离**：基于agent_id实现自动数据隔离，无需修改业务代码
- **ORM基座替换**：支持通过替换BaseModel实现多租户改造，保持单用户版本业务逻辑不变
- **统一连接管理**：提供数据库连接池和配置管理
- **上下文管理**：线程安全的agent_id上下文传递

## 安装

```bash
pip install -e .
```

或从requirements安装：

```bash
pip install -r requirements.txt
```

## 快速开始

### 1. 环境配置

设置数据库连接环境变量：

```bash
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=ai_saas
export DB_USER=postgres
export DB_PASSWORD=your_password
```

### 2. 初始化数据库

```python
from ai_project_core import init_database, ALL_MODELS

# 连接数据库并创建所有表
init_database()
from ai_project_core.db_manager import db_manager
db_manager.create_tables(ALL_MODELS)
```

### 3. 使用系统模型（控制面）

```python
from ai_project_core import User, Tenant, Agent

# 创建租户
tenant = Tenant.create(name="demo_tenant", description="Demo租户")

# 创建用户
user = User.create(
    username="demo_user",
    email="demo@example.com",
    password_hash="hashed_password",
    tenant=tenant
)

# 创建Agent
agent = Agent.create(
    name="demo_agent",
    description="Demo Agent",
    user=user,
    tenant=tenant
)
```

### 4. 使用业务模型（数据面）

```python
from ai_project_core import ChatHistory, agent_context_manager

# 使用上下文管理器设置agent_id
with agent_context_manager(str(agent.id)):
    # 创建聊天记录 - 自动注入agent_id
    chat = ChatHistory.create(
        session_id="session_123",
        user_message="Hello",
        assistant_message="Hi there!",
        user_id="user_123"
    )

    # 查询 - 自动过滤agent_id
    chats = ChatHistory.select().where(ChatHistory.session_id == "session_123")
```

### 5. 在遗留代码中使用ORM替换

在遗留项目中，替换原有的BaseModel：

```python
# 遗留代码中的database_model.py
from ai_project_core import BusinessBaseModel as BaseModel

# 现有业务代码无需修改
class Message(BaseModel):
    content = TextField()
    # 其他字段...

# 现有业务逻辑保持不变
message = Message.create(content="Hello")
# 自动获得agent_id字段和多租户隔离
```

## 架构说明

### 目录结构

```
ai_project_core/
├── src/
│   └── core/
│       ├── database.py       # 统一的 Peewee Database 实例配置
│       ├── config.py         # 环境变量读取
│       ├── context_manager.py # 上下文管理
│       └── models/
│           ├── __init__.py   # 模型导出
│           ├── system.py     # 控制面模型: User, Tenant, ApiKey, Agent
│           └── business.py   # 数据面模型: ChatHistory, Logs (包含 agent_id)
```

### 模型分类

#### 控制面模型（System）
- `Tenant`: 租户信息
- `User`: 用户信息
- `Agent`: AI代理信息
- `ApiKey`: API密钥管理

#### 数据面模型（Business）
- `ChatHistory`: 聊天历史记录
- `ChatLogs`: 聊天日志
- `FileUpload`: 文件上传记录
- `UserSession`: 用户会话
- `SystemMetrics`: 系统指标

### 多租户隔离机制

1. **自动注入**：业务模型的`save()`和`create()`方法自动注入当前agent_id
2. **自动过滤**：业务模型的`select()`方法自动添加agent_id过滤条件
3. **上下文传递**：通过线程本地存储实现agent_id的上下文传递

## 开发指南

### 添加新的业务表

1. 在`business.py`中定义新模型，继承`BusinessBaseModel`
2. 运行数据库迁移创建物理表（确保包含agent_id列）
3. 在使用时通过上下文管理器设置agent_id

### 数据库迁移

所有数据库结构变更必须在ai_project_core项目中管理：

```python
# 迁移脚本示例
from peewee import *
from ai_project_core import database

# 添加新字段的迁移
migrator = PostgresqlMigrator(database)
migrate(
    migrator.add_column('chat_history', 'new_field', CharField(null=True))
)
```

## 注意事项

1. 禁止在微服务内部单独定义数据模型
2. 所有数据库结构变更必须在ai_project_core中管理
3. 遗留代码使用ORM替换时，注意配置.gitattributes保护替换文件
4. 生产环境建议使用连接池和适当的超时设置

## 许可证

MIT License