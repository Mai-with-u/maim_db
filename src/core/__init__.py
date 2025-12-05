"""
核心库模块初始化文件
导出数据库配置、模型和上下文管理
"""

# 导入数据库相关
# 导入配置
from .config import DatabaseConfig
from .settings import settings

# 导入上下文管理
from .context_manager import (
    agent_context,
    agent_context_manager,
    clear_current_agent_id,
    get_current_agent_id,
    set_current_agent_id,
)

# 导入Agent配置管理
from .agent_config_manager import AgentConfigManager
from .database import (
    close_database,
    database,
    db_manager,
    get_database,
    init_database,
)

# 导入异步模型
from .async_models import (
    AsyncTenant,
    AsyncAgent,
    AsyncApiKey,
)

# 导入所有模型
from .models import (
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
)

# 导入Agent配置工具函数
from .models import (
    generate_config_id,
    parse_json_field,
    serialize_json_field,
    AGENT_CONFIG_MODELS,
    CONFIG_TYPE_MAPPING,
)

__all__ = [
    # 数据库相关
    'database',
    'get_database',
    'init_database',
    'close_database',
    'db_manager',

    # 配置
    'DatabaseConfig',
    'settings',

    # 上下文管理
    'get_current_agent_id',
    'set_current_agent_id',
    'clear_current_agent_id',
    'agent_context_manager',
    'agent_context',

    # 配置管理
    'AgentConfigManager',

    # 异步模型
    'AsyncTenant',
    'AsyncAgent',
    'AsyncApiKey',

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
    'UserSession',
    'SystemMetrics',

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

    # Agent配置工具函数
    'generate_config_id',
    'parse_json_field',
    'serialize_json_field',
    'AGENT_CONFIG_MODELS',
    'CONFIG_TYPE_MAPPING',
]
