# MaimDB 数据库模型详解

## 📊 模型架构概览

MaimDB 现在包含四大类别的数据模型：

1. **V2系统模型** - 基于MaiMConfig设计的多租户架构
2. **Agent配置模型** - 结构化Agent配置管理系统
3. **业务模型** - 通用业务功能模型
4. **已弃用模型** - 向后兼容的旧版本模型

---

## 🏢 V2系统模型（核心多租户架构）

### BaseModel - 基础模型类
```python
class BaseModel(Model):
    """所有V2模型的基类"""
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)

    class Meta:
        database = get_database()
```

**特点：**
- 提供统一的时间戳字段
- 所有模型继承的基础类
- 自动数据库绑定

---

### Tenant - 租户模型
```python
class Tenant(BaseModel):
    id = CharField(primary_key=True, max_length=50)                    # 租户ID: tenant_xxx
    tenant_name = CharField(max_length=100, unique=True, index=True)  # 租户名称
    tenant_type = CharField(max_length=20, choices=[...])             # 租户类型
    description = TextField(null=True)                                 # 租户描述
    contact_email = CharField(max_length=255, null=True)              # 联系邮箱
    tenant_config = TextField(null=True)                               # JSON配置
    status = CharField(max_length=20, choices=[...])                   # 租户状态
    owner_id = CharField(max_length=50, null=True)                     # 所有者ID
    created_at = DateTimeField(default=datetime.utcnow)               # 创建时间
    updated_at = DateTimeField(default=datetime.utcnow)               # 更新时间
```

**枚举类型：**
- `TenantType`: `PERSONAL`（个人）, `ENTERPRISE`（企业）
- `TenantStatus`: `ACTIVE`（活跃）, `INACTIVE`（非活跃）, `SUSPENDED`（暂停）

**关系：**
- 一对多：Agents（一个租户多个AI助手）
- 一对多：ApiKeys（一个租户多个API密钥）

**使用场景：**
```python
# 创建企业租户
tenant = Tenant.create(
    id="tenant_company_001",
    tenant_name="示例科技公司",
    tenant_type="enterprise",
    contact_email="admin@company.com",
    tenant_config='{"max_agents": 100, "storage_quota": "1TB"}',
    status="active"
)
```

---

### Agent - AI助手模型
```python
class Agent(BaseModel):
    id = CharField(primary_key=True, max_length=50)                    # Agent ID: agent_xxx
    tenant_id = CharField(max_length=50, index=True)                   # 租户ID（外键）
    name = CharField(max_length=100)                                   # Agent名称
    description = TextField(null=True)                                 # Agent描述
    template_id = CharField(max_length=50, null=True)                  # 模板ID
    config = TextField(null=True)                                     # JSON配置
    status = CharField(max_length=20, choices=[...])                   # Agent状态
    created_at = DateTimeField(default=datetime.utcnow)               # 创建时间
    updated_at = DateTimeField(default=datetime.utcnow)               # 更新时间
```

**枚举类型：**
- `AgentStatus`: `ACTIVE`（活跃）, `INACTIVE`（非活跃）, `ARCHIVED`（已归档）

**关系：**
- 多对一：Tenant（属于某个租户）
- 一对多：ApiKeys（一个Agent多个API密钥）

**配置示例：**
```python
agent_config = {
    "persona": "专业、友好的客服助手",
    "bot_overrides": {
        "nickname": "小助手",
        "platform": "web"
    },
    "config_overrides": {
        "personality": {
            "reply_style": "专业礼貌",
            "interest": "客户服务"
        },
        "chat": {
            "max_context_size": 20,
            "response_timeout": 30,
            "temperature": 0.7
        }
    },
    "tags": ["客服", "技术支持", "AI助手"]
}
```

---

### ApiKey - API密钥模型
```python
class ApiKey(BaseModel):
    id = CharField(primary_key=True, max_length=50)                    # 密钥ID: key_xxx
    tenant_id = CharField(max_length=50, index=True)                   # 租户ID（外键）
    agent_id = CharField(max_length=50, index=True)                    # Agent ID（外键）
    name = CharField(max_length=100)                                   # 密钥名称
    description = TextField(null=True)                                 # 密钥描述
    api_key = CharField(max_length=255, unique=True, index=True)     # API密钥值
    permissions = TextField(null=True)                                 # JSON权限列表
    status = CharField(max_length=20, choices=[...])                   # 密钥状态
    expires_at = DateTimeField(null=True)                              # 过期时间
    last_used_at = DateTimeField(null=True)                            # 最后使用时间
    usage_count = IntegerField(default=0)                              # 使用次数
    created_at = DateTimeField(default=datetime.utcnow)               # 创建时间
    updated_at = DateTimeField(default=datetime.utcnow)               # 更新时间
```

**枚举类型：**
- `ApiKeyStatus`: `ACTIVE`（活跃）, `DISABLED`（禁用）, `EXPIRED`（已过期）

**权限示例：**
```python
permissions = ["chat", "config_read", "config_write", "analytics"]
```

**API密钥格式：**
```
mmc_{base64_encoded_data}
例如: mmc_dGVuYW50X2FnZW50XzEyMzRfcXdkZXJ0eV92MQ==
```

---

## 🎛️ Agent配置模型（结构化配置管理）

### AgentConfigBaseModel - 配置模型基类
```python
class AgentConfigBaseModel(Model):
    """Agent配置基础模型"""
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)

    class Meta:
        database = get_database()
```

**特点：**
- 统一的配置时间戳管理
- 所有Agent配置模型的基础类
- 自动数据库绑定

---

### PersonalityConfig - 人格配置模型
```python
class PersonalityConfig(AgentConfigBaseModel):
    id = CharField(primary_key=True, max_length=50)                    # 配置ID
    agent_id = CharField(max_length=50, index=True)                    # Agent ID
    personality = TextField()                                          # 人格核心描述
    reply_style = CharField(max_length=500, default="")               # 回复风格
    interest = CharField(max_length=500, default="")                  # 兴趣领域
    plan_style = CharField(max_length=500, default="")                # 群聊行为风格
    private_plan_style = CharField(max_length=500, default="")        # 私聊行为风格
    visual_style = CharField(max_length=500, default="")              # 视觉风格
    states = TextField(default="[]")                                   # 状态列表JSON
    state_probability = FloatField(default=0.0)                       # 状态切换概率
```

**用途：**
- 定义Agent的核心人格特征
- 管理多状态人格系统
- 配置不同场景下的行为风格

**状态系统示例：**
```python
states = [
    {"name": "正常", "keywords": ["你好", "帮助", "问题"]},
    {"name": "专注", "keywords": ["处理", "解决", "分析"]},
    {"name": "休息", "keywords": ["累了", "休息", "暂停"]}
]
```

---

### BotConfigOverrides - Bot基础配置覆盖模型
```python
class BotConfigOverrides(AgentConfigBaseModel):
    id = CharField(primary_key=True, max_length=50)                    # 配置ID
    agent_id = CharField(max_length=50, index=True)                    # Agent ID
    platform = CharField(max_length=50, default="")                   # 运行平台
    qq_account = CharField(max_length=50, default="")                  # QQ账号
    nickname = CharField(max_length=100, default="")                  # 机器人昵称
    platforms = TextField(default="[]")                                # 其他支持平台JSON
    alias_names = TextField(default="[]")                              # 别名列表JSON
```

**用途：**
- 配置Agent的基础运行参数
- 管理多平台支持
- 设置别名和昵称

---

### ChatConfigOverrides - 聊天配置覆盖模型
```python
class ChatConfigOverrides(AgentConfigBaseModel):
    id = CharField(primary_key=True, max_length=50)                    # 配置ID
    agent_id = CharField(max_length=50, index=True)                    # Agent ID
    max_context_size = IntegerField(default=18)                       # 上下文长度
    interest_rate_mode = CharField(max_length=20, default="fast")      # 兴趣计算模式
    planner_size = FloatField(default=1.5)                             # 规划器大小
    mentioned_bot_reply = BooleanField(default=True)                   # 提及回复
    auto_chat_value = FloatField(default=1.0)                          # 主动聊天频率
    enable_auto_chat_value_rules = BooleanField(default=True)          # 动态聊天频率
    at_bot_inevitable_reply = FloatField(default=1.0)                 # @回复必然性
    planner_smooth = FloatField(default=3.0)                           # 规划器平滑
    talk_value = FloatField(default=1.0)                               # 思考频率
    enable_talk_value_rules = BooleanField(default=True)               # 动态思考频率
    talk_value_rules = TextField(default="[]")                          # 思考频率规则JSON
    auto_chat_value_rules = TextField(default="[]")                    # 聊天频率规则JSON
```

**用途：**
- 精细控制聊天行为
- 配置上下文管理
- 管理主动交互策略

---

### MemoryConfigOverrides - 记忆配置覆盖模型
```python
class MemoryConfigOverrides(AgentConfigBaseModel):
    id = CharField(primary_key=True, max_length=50)                    # 配置ID
    agent_id = CharField(max_length=50, index=True)                    # Agent ID
    max_memory_number = IntegerField(default=100)                     # 记忆最大数量
    memory_build_frequency = IntegerField(default=1)                   # 记忆构建频率
```

**用途：**
- 配置长期记忆系统
- 控制记忆存储策略
- 管理记忆构建频率

---

### MoodConfigOverrides - 情绪配置覆盖模型
```python
class MoodConfigOverrides(AgentConfigBaseModel):
    id = CharField(primary_key=True, max_length=50)                    # 配置ID
    agent_id = CharField(max_length=50, index=True)                    # Agent ID
    enable_mood = BooleanField(default=True)                           # 启用情绪系统
    mood_update_threshold = FloatField(default=1.0)                    # 情绪更新阈值
    emotion_style = CharField(max_length=200, default="")              # 情感特征
```

**用途：**
- 管理情绪状态系统
- 配置情绪变化规则
- 设置情感表达风格

---

### EmojiConfigOverrides - 表情包配置覆盖模型
```python
class EmojiConfigOverrides(AgentConfigBaseModel):
    id = CharField(primary_key=True, max_length=50)                    # 配置ID
    agent_id = CharField(max_length=50, index=True)                    # Agent ID
    emoji_chance = FloatField(default=0.6)                             # 表情包概率
    max_reg_num = IntegerField(default=200)                            # 最大注册数量
    do_replace = BooleanField(default=True)                            # 是否替换
    check_interval = IntegerField(default=120)                         # 检查间隔
    steal_emoji = BooleanField(default=True)                           # 偷取表情包
    content_filtration = BooleanField(default=False)                   # 内容过滤
    filtration_prompt = CharField(max_length=200, default="")          # 过滤要求
```

**用途：**
- 配置表情包使用策略
- 管理表情包学习系统
- 设置内容过滤规则

---

### ToolConfigOverrides - 工具配置覆盖模型
```python
class ToolConfigOverrides(AgentConfigBaseModel):
    id = CharField(primary_key=True, max_length=50)                    # 配置ID
    agent_id = CharField(max_length=50, index=True)                    # Agent ID
    enable_tool = BooleanField(default=False)                          # 启用工具
```

**用途：**
- 控制工具系统启用状态
- 管理外部工具集成

---

### VoiceConfigOverrides - 语音配置覆盖模型
```python
class VoiceConfigOverrides(AgentConfigBaseModel):
    id = CharField(primary_key=True, max_length=50)                    # 配置ID
    agent_id = CharField(max_length=50, index=True)                    # Agent ID
    enable_asr = BooleanField(default=False)                           # 语音识别
```

**用途：**
- 配置语音功能
- 管理语音识别系统

---

### PluginConfigOverrides - 插件配置覆盖模型
```python
class PluginConfigOverrides(AgentConfigBaseModel):
    id = CharField(primary_key=True, max_length=50)                    # 配置ID
    agent_id = CharField(max_length=50, index=True)                    # Agent ID
    enable_plugins = BooleanField(default=True)                        # 启用插件
    tenant_mode_disable_plugins = BooleanField(default=True)           # 租户模式禁用
    allowed_plugins = TextField(default="[]")                          # 允许插件JSON
    blocked_plugins = TextField(default="[]")                          # 禁止插件JSON
```

**用途：**
- 管理插件系统
- 控制插件访问权限
- 配置多租户插件策略

---

### ExpressionConfigOverrides - 表达配置覆盖模型
```python
class ExpressionConfigOverrides(AgentConfigBaseModel):
    id = CharField(primary_key=True, max_length=50)                    # 配置ID
    agent_id = CharField(max_length=50, index=True)                    # Agent ID
    mode = CharField(max_length=20, default="classic")                # 表达模式
    learning_list = TextField(default="[]")                            # 表达学习配置JSON
    expression_groups = TextField(default="[]")                        # 表达学习互通组JSON
```

**用途：**
- 配置语言表达风格
- 管理表达学习系统
- 设置表达模式

---

### KeywordReactionConfigOverrides - 关键词反应配置覆盖模型
```python
class KeywordReactionOverrides(AgentConfigBaseModel):
    id = CharField(primary_key=True, max_length=50)                    # 配置ID
    agent_id = CharField(max_length=50, index=True)                    # Agent ID
    keyword_rules = TextField(default="[]")                            # 关键词规则JSON
    regex_rules = TextField(default="[]")                              # 正则规则JSON
```

**用途：**
- 配置关键词自动反应
- 管理正则表达式规则
- 设置智能触发机制

---

### RelationshipConfigOverrides - 关系配置覆盖模型
```python
class RelationshipConfigOverrides(AgentConfigBaseModel):
    id = CharField(primary_key=True, max_length=50)                    # 配置ID
    agent_id = CharField(max_length=50, index=True)                    # Agent ID
    enable_relationship = BooleanField(default=True)                   # 启用关系系统
```

**用途：**
- 管理用户关系系统
- 配置关系追踪功能

---

## 💼 业务模型（通用功能）

### BusinessBaseModel - 业务基础模型
```python
class BusinessBaseModel(Model):
    """业务模型基类"""
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)
```

---

### ChatHistory - 聊天历史模型
```python
class ChatHistory(BusinessBaseModel):
    session_id = CharField(max_length=100, index=True)                 # 会话ID
    user_id = CharField(max_length=100, index=True)                   # 用户ID
    message_type = CharField(max_length=20)                           # 消息类型
    content = TextField()                                             # 消息内容
    metadata = TextField(null=True)                                   # 元数据（JSON）
```

**用途：**
- 存储聊天对话记录
- 支持用户和Agent的对话
- 可扩展的元数据支持

---

### ChatLogs - 聊天日志模型
```python
class ChatLogs(BusinessBaseModel):
    session_id = CharField(max_length=100, index=True)                 # 会话ID
    agent_id = CharField(max_length=100, index=True)                  # Agent ID
    user_message = TextField()                                        # 用户消息
    agent_response = TextField()                                      # Agent响应
    response_time = FloatField(null=True)                            # 响应时间
    tokens_used = IntegerField(default=0)                            # 使用的token数
    error_message = TextField(null=True)                             # 错误信息
```

**用途：**
- 记录详细的聊天日志
- 性能监控和分析
- 错误追踪

---

### FileUpload - 文件上传模型
```python
class FileUpload(BusinessBaseModel):
    user_id = CharField(max_length=100, index=True)                   # 用户ID
    filename = CharField(max_length=255)                              # 文件名
    file_path = CharField(max_length=500)                             # 文件路径
    file_size = BigIntegerField()                                     # 文件大小
    mime_type = CharField(max_length=100)                            # MIME类型
    upload_status = CharField(max_length=20, default='pending')      # 上传状态
```

**用途：**
- 文件上传管理
- 文件存储追踪
- 上传状态监控

---

### SystemMetrics - 系统指标模型
```python
class SystemMetrics(BusinessBaseModel):
    metric_name = CharField(max_length=100, index=True)               # 指标名称
    metric_value = FloatField()                                       # 指标值
    metric_unit = CharField(max_length=20)                           # 指标单位
    tags = TextField(null=True)                                       # 标签（JSON）
```

**用途：**
- 系统性能监控
- 业务指标收集
- 数据分析支持

---

### UserSession - 用户会话模型
```python
class UserSession(BusinessBaseModel):
    user_id = CharField(max_length=100, index=True)                   # 用户ID
    session_token = CharField(max_length=255, unique=True)           # 会话令牌
    expires_at = DateTimeField()                                      # 过期时间
    last_activity = DateTimeField(default=datetime.utcnow)          # 最后活动时间
    ip_address = CharField(max_length=45, null=True)                # IP地址
    user_agent = TextField(null=True)                                 # 用户代理
```

**用途：**
- 用户会话管理
- 登录状态追踪
- 安全审计

---

## 🔄 已弃用模型（向后兼容）

### 旧版本系统模型
- `OldBaseModel` - 旧版基础模型
- `OldTenant` - 旧版租户模型
- `OldAgent` - 旧版Agent模型
- `OldApiKey` - 旧版API密钥模型
- `User` - 用户模型

**注意：** 这些模型仅用于向后兼容，新项目应使用V2模型。

---

## 📈 模型统计

| 模型类别 | 数量 | 主要用途 |
|---------|------|----------|
| V2系统模型 | 4个 | 多租户核心架构 |
| Agent配置模型 | 12个 | 结构化配置管理 |
| 业务模型 | 5个 | 通用业务功能 |
| 已弃用模型 | 5个 | 向后兼容 |
| **总计** | **26个** | **完整数据库架构** |

---

## 🔗 关系图

```
Tenant (租户)
├── Agent (AI助手) [一对多]
│   ├── ApiKey (API密钥) [一对多]
│   └── Agent配置模型 [一对多]
│       ├── PersonalityConfig (人格配置)
│       ├── BotConfigOverrides (Bot基础配置)
│       ├── ChatConfigOverrides (聊天配置)
│       ├── MemoryConfigOverrides (记忆配置)
│       ├── MoodConfigOverrides (情绪配置)
│       ├── EmojiConfigOverrides (表情包配置)
│       ├── ToolConfigOverrides (工具配置)
│       ├── VoiceConfigOverrides (语音配置)
│       ├── PluginConfigOverrides (插件配置)
│       ├── ExpressionConfigOverrides (表达配置)
│       ├── KeywordReactionConfigOverrides (关键词反应配置)
│       └── RelationshipConfigOverrides (关系配置)
└── ApiKey (直接API密钥) [一对多]

业务模型（独立）:
├── ChatHistory
├── ChatLogs
├── FileUpload
├── SystemMetrics
└── UserSession
```

---

## 💡 使用示例

### 创建完整的租户环境
```python
from maim_db.src.core.models import (
    Tenant, Agent, ApiKey, TenantType,
    PersonalityConfig, ChatConfigOverrides, PluginConfigOverrides
)

# 1. 创建租户
tenant = Tenant.create(
    id="tenant_demo_001",
    tenant_name="示例公司",
    tenant_type=TenantType.ENTERPRISE.value,
    description="示例企业租户"
)

# 2. 创建AI助手
agent = Agent.create(
    id="agent_demo_001",
    tenant_id=tenant.id,
    name="客服助手",
    description="专业的客户服务AI助手"
)

# 3. 创建API密钥
api_key = ApiKey.create(
    id="key_demo_001",
    tenant_id=tenant.id,
    agent_id=agent.id,
    name="生产环境密钥",
    api_key="mmc_demo_api_key_123456",
    permissions='["chat", "config_read"]'
)

# 4. 创建Agent人格配置
personality = PersonalityConfig.create(
    id="config_personality_001",
    agent_id=agent.id,
    personality="友好、专业的客服助手，具有耐心和细致的解答能力",
    reply_style="温和、专业、略带幽默",
    interest="客户服务、技术支持、产品咨询",
    states='[{"name": "正常", "keywords": ["你好", "帮助", "问题"]}]',
    state_probability=0.3
)

# 5. 创建聊天配置
chat_config = ChatConfigOverrides.create(
    id="config_chat_001",
    agent_id=agent.id,
    max_context_size=20,
    interest_rate_mode="medium",
    planner_size=2.0,
    talk_value=0.9
)

# 6. 创建插件配置
plugin_config = PluginConfigOverrides.create(
    id="config_plugin_001",
    agent_id=agent.id,
    enable_plugins=True,
    allowed_plugins='["knowledge_base", "order_query", "ticket_system"]',
    blocked_plugins='["admin_only"]'
)
```

### Agent配置管理示例
```python
from maim_db.src.core.agent_config_manager import AgentConfigManager

# 创建配置管理器
config_manager = AgentConfigManager("agent_demo_001")

# 获取所有配置
all_configs = config_manager.get_all_configs()
print(f"人格描述: {all_configs['persona']['personality']}")
print(f"聊天上下文: {all_configs['config_overrides']['chat']['max_context_size']}")

# 更新人格配置
persona_update = {
    "personality": "更新后：经验丰富的技术专家",
    "reply_style": "技术性、条理清晰、通俗易懂"
}
config_manager.update_config_from_json({"persona": persona_update})

# 获取单独配置
personality_config = config_manager.get_personality_config()
chat_config = config_manager.get_config_overrides("chat")

# 删除所有配置
config_manager.delete_all_configs()
```

### 查询数据
```python
# 查询租户下的所有Agent
agents = Agent.select().where(Agent.tenant_id == tenant.id)

# 查询活跃的API密钥
active_keys = ApiKey.select().where(
    (ApiKey.tenant_id == tenant.id) &
    (ApiKey.status == "active")
)

# 统计数据
agent_count = Agent.select().where(Agent.tenant_id == tenant.id).count()
```

---

## 🎯 特性总结

### 多租户支持
- 完整的租户隔离
- 灵活的权限管理
- 可配置的租户设置

### 结构化配置管理
- **12个专门配置表**：替代单一JSON字段
- **模块化管理**：人格、聊天、记忆、情绪等独立配置
- **类型安全**：强类型字段验证和约束
- **高效查询**：结构化字段支持索引和搜索
- **灵活更新**：支持部分配置更新和完整覆盖

### 配置覆盖系统
- **三层架构**：persona → bot_overrides → config_overrides
- **功能模块化**：每个功能模块独立配置表
- **向后兼容**：API响应仍保持JSON格式
- **配置管理器**：提供统一的配置操作接口

### JSON配置存储
- 租户配置：`tenant_config`
- Agent基础配置：`config`（保留兼容性）
- API权限：`permissions`
- 复杂数据：JSON字段支持复杂数据结构

### 状态管理
- 租户状态：活跃/非活跃/暂停
- Agent状态：活跃/非活跃/归档
- API密钥状态：活跃/禁用/过期

### 性能优化
- **索引优化**：agent_id字段建立索引
- **外键约束**：确保配置与Agent的关联
- **时间戳自动管理**：created_at/updated_at自动更新
- **连接池支持**：高效的数据库连接管理
- **查询优化**：结构化字段支持精确查询

### 数据完整性
- 外键级联删除
- 唯一性约束
- 非空约束
- 字符长度限制
- 配置ID唯一性

### 扩展性设计
- **模块化架构**：新配置类型可独立添加
- **配置管理器**：统一的配置操作抽象
- **异步支持**：AsyncAgent等异步模型
- **API兼容**：保持现有API接口不变

这个数据库模型设计为企业级多租户SaaS应用提供了完整的数据基础设施，特别是Agent配置系统的结构化设计，为复杂的AI助手配置管理提供了强大的支持！