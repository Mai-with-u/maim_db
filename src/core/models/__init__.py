"""
数据模型包初始化文件
导出所有数据模型供其他模块使用
版本2：基于MaiMConfig设计的多租户模型
"""

# 导入v2系统模型（基于MaiMConfig设计）
from .system_v2 import (
    # 枚举类
    TenantType,
    TenantStatus,
    AgentStatus,
    ApiKeyStatus,

    # 模型类
    BaseModel,
    Tenant,
    Agent,
    ApiKey,
)

# 导入Agent配置模型
from .agent_config import (
    PersonalityConfig,
    BotConfigOverrides,
    ChatConfigOverrides,
    ExpressionConfigOverrides,
    MemoryConfigOverrides,
    MoodConfigOverrides,
    EmojiConfigOverrides,
    ToolConfigOverrides,
    VoiceConfigOverrides,
    PluginConfigOverrides,
    KeywordReactionConfigOverrides,
    RelationshipConfigOverrides,

    # 工具函数和常量
    generate_config_id,
    parse_json_field,
    serialize_json_field,
    AGENT_CONFIG_MODELS,
    CONFIG_TYPE_MAPPING,
)

# 导入原有的业务模型（保持不变）
from .business import (
    BusinessBaseModel,
    ChatHistory,
    ChatLogs,
    FileUpload,
    SystemMetrics,
    UserSession,
)

# 保留原有的系统模型用于向后兼容（但标记为deprecated）
from .system import (
    BaseModel as OldBaseModel,
    Agent as OldAgent,
    ApiKey as OldApiKey,
    Tenant as OldTenant,
    User,
)

# v2模型列表（新设计，基于MaiMConfig）
V2_MODELS = [
    BaseModel,
    Tenant,
    Agent,
    ApiKey,
]

# Agent配置模型列表
AGENT_CONFIG_MODELS = [
    PersonalityConfig,
    BotConfigOverrides,
    ChatConfigOverrides,
    ExpressionConfigOverrides,
    MemoryConfigOverrides,
    MoodConfigOverrides,
    EmojiConfigOverrides,
    ToolConfigOverrides,
    VoiceConfigOverrides,
    PluginConfigOverrides,
    KeywordReactionConfigOverrides,
    RelationshipConfigOverrides,
]

# 业务模型列表（保持不变）
BUSINESS_MODELS = [
    BusinessBaseModel,
    ChatHistory,
    ChatLogs,
    FileUpload,
    UserSession,
    SystemMetrics,
]

# 所有模型的列表，用于数据库表创建
ALL_MODELS = V2_MODELS + BUSINESS_MODELS + AGENT_CONFIG_MODELS

# 向后兼容的旧模型（标记为deprecated）
DEPRECATED_MODELS = [
    OldBaseModel,
    OldTenant,
    User,
    OldAgent,
    OldApiKey,
]

__all__ = [
    # 枚举类
    'TenantType',
    'TenantStatus',
    'AgentStatus',
    'ApiKeyStatus',

    # v2系统模型
    'BaseModel',
    'Tenant',
    'Agent',
    'ApiKey',

    # Agent配置模型
    'PersonalityConfig',
    'BotConfigOverrides',
    'ChatConfigOverrides',
    'ExpressionConfigOverrides',
    'MemoryConfigOverrides',
    'MoodConfigOverrides',
    'EmojiConfigOverrides',
    'ToolConfigOverrides',
    'VoiceConfigOverrides',
    'PluginConfigOverrides',
    'KeywordReactionConfigOverrides',
    'RelationshipConfigOverrides',

    # 业务模型
    'BusinessBaseModel',
    'ChatHistory',
    'ChatLogs',
    'FileUpload',
    'UserSession',
    'SystemMetrics',

    # 旧模型（deprecated）
    'OldBaseModel',
    'OldTenant',
    'OldAgent',
    'OldApiKey',
    'User',

    # 模型集合
    'ALL_MODELS',
    'V2_MODELS',
    'BUSINESS_MODELS',
    'AGENT_CONFIG_MODELS',
    'DEPRECATED_MODELS',

    # 工具函数
    'generate_config_id',
    'parse_json_field',
    'serialize_json_field',
    'CONFIG_TYPE_MAPPING',
]