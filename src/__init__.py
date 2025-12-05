"""
AI Project Core 源码包初始化文件
统一数据库核心库的主要入口
"""

# 导入异步模型
try:
    from .core.async_models import (
        AsyncTenant,
        AsyncAgent,
        AsyncApiKey,
    )
except ImportError:
    AsyncTenant = None
    AsyncAgent = None
    AsyncApiKey = None

from .core import (
    # 模型集合
    ALL_MODELS,
    V2_MODELS,
    BUSINESS_MODELS,
    DEPRECATED_MODELS,
    # 枚举类
    TenantType,
    TenantStatus,
    AgentStatus,
    ApiKeyStatus,
    # v2系统模型
    BaseModel,
    Tenant,
    Agent,
    ApiKey,
    # 基础模型
    BusinessBaseModel,
    # 业务模型
    ChatHistory,
    ChatLogs,
    FileUpload,
    SystemMetrics,
    UserSession,
    # 旧系统模型（deprecated）
    OldBaseModel,
    OldTenant,
    OldAgent,
    OldApiKey,
    User,
    # 配置
    DatabaseConfig,
    settings,
    # 上下文管理
    agent_context,
    agent_context_manager,
    clear_current_agent_id,
    # 数据库相关
    close_database,
    database,
    db_manager,
    get_current_agent_id,
    get_database,
    init_database,
    set_current_agent_id,
)

__all__ = [
    # 数据库相关
    'close_database',
    'database',
    'db_manager',
    'get_database',
    'init_database',

    # 配置
    'DatabaseConfig',

    # 上下文管理
    'agent_context',
    'agent_context_manager',
    'clear_current_agent_id',
    'get_current_agent_id',
    'set_current_agent_id',

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

    # 基础模型
    'BusinessBaseModel',

    # 业务模型
    'ChatHistory',
    'ChatLogs',
    'FileUpload',
    'SystemMetrics',
    'UserSession',

    # 旧系统模型（deprecated）
    'OldBaseModel',
    'OldTenant',
    'OldAgent',
    'OldApiKey',
    'User',

    # 模型集合
    'ALL_MODELS',
    'V2_MODELS',
    'BUSINESS_MODELS',
    'DEPRECATED_MODELS',

    # 异步模型
    'AsyncTenant',
    'AsyncAgent',
    'AsyncApiKey',
]

__version__ = "1.0.0"
__author__ = "AI Project Team"
__description__ = "统一数据库核心库 - 支持多租户SaaS架构的数据模型和数据库管理"
