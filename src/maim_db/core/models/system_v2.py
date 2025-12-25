"""
基于MaiMConfig的控制面模型定义 v2.0
使用Peewee ORM，包含 Tenant, Agent, ApiKey 等系统级数据模型
"""

import uuid
import json
from datetime import datetime, timedelta
from enum import Enum

from peewee import (
    BooleanField,
    CharField,
    DateTimeField,
    ForeignKeyField,
    IntegerField,
    Model,
    TextField,
    UUIDField,
    IntegerField,
    BigIntegerField,
    FloatField,
    Check,
    DatabaseProxy,
    CompositeKey,
)

from ..database import get_database


class TenantType(Enum):
    """租户类型"""

    PERSONAL = "personal"
    ENTERPRISE = "enterprise"


class TenantStatus(Enum):
    """租户状态"""

    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


class AgentStatus(Enum):
    """Agent状态"""

    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class ApiKeyStatus(Enum):
    """API密钥状态"""

    ACTIVE = "active"
    DISABLED = "disabled"
    EXPIRED = "expired"


class BaseModel(Model):
    """模型基类"""

    class Meta:
        database = get_database()


class User(BaseModel):
    """用户表 - 基于MaiMConfig设计"""

    id = CharField(primary_key=True, max_length=50, help_text="用户ID")
    username = CharField(max_length=100, unique=True, index=True, help_text="用户名")
    email = CharField(max_length=255, unique=True, index=True, null=True, help_text="邮箱")
    hashed_password = CharField(max_length=255, help_text="加密密码")
    is_active = BooleanField(default=True, help_text="是否活跃")
    
    created_at = DateTimeField(default=datetime.utcnow, help_text="创建时间")
    updated_at = DateTimeField(default=datetime.utcnow, help_text="更新时间")

    class Meta:
        table_name = "users"
        database = get_database()

    def save(self, *args, **kwargs):
        """保存时更新时间戳"""
        self.updated_at = datetime.utcnow()
        return super().save(*args, **kwargs)


class Tenant(BaseModel):
    """租户表 - 基于MaiMConfig设计"""

    id = CharField(
        primary_key=True, max_length=50, help_text="租户ID，格式：tenant_xxx"
    )
    tenant_name = CharField(
        max_length=100, unique=True, index=True, help_text="租户名称"
    )
    tenant_type = CharField(
        max_length=20,
        choices=[(e.value, e.value) for e in TenantType],
        default=TenantType.PERSONAL.value,
        help_text="租户类型：personal 或 enterprise",
    )
    description = TextField(null=True, help_text="租户描述")
    contact_email = CharField(max_length=255, null=True, help_text="联系邮箱")
    tenant_config = TextField(null=True, help_text="租户配置，JSON格式")
    status = CharField(
        max_length=20,
        choices=[(e.value, e.value) for e in TenantStatus],
        default=TenantStatus.ACTIVE.value,
        help_text="租户状态",
    )
    owner_id = CharField(max_length=50, null=True, help_text="所有者ID")
    created_at = DateTimeField(default=datetime.utcnow, help_text="创建时间")
    updated_at = DateTimeField(default=datetime.utcnow, help_text="更新时间")

    class Meta:
        table_name = "tenants"
        database = get_database()

    def save(self, *args, **kwargs):
        """保存时更新时间戳"""
        self.updated_at = datetime.utcnow()
        return super().save(*args, **kwargs)

    def get_config(self):
        """获取租户配置"""
        if self.tenant_config:
            try:
                return json.loads(self.tenant_config)
            except json.JSONDecodeError:
                return {}
        return {}

    def set_config(self, config_dict):
        """设置租户配置"""
        self.tenant_config = json.dumps(config_dict)
        self.save()

    @property
    def is_active(self):
        """检查租户是否活跃"""
        return self.status == TenantStatus.ACTIVE.value


class Agent(BaseModel):
    """Agent表 - 基于MaiMConfig设计"""

    id = CharField(
        primary_key=True, max_length=50, help_text="Agent ID，格式：agent_xxx"
    )
    tenant_id = CharField(max_length=50, index=True, help_text="所属租户ID")
    name = CharField(max_length=100, help_text="Agent名称")
    description = TextField(null=True, help_text="Agent描述")
    template_id = CharField(max_length=50, null=True, help_text="模板ID")
    config = TextField(null=True, help_text="Agent配置，JSON格式")
    status = CharField(
        max_length=20,
        choices=[(e.value, e.value) for e in AgentStatus],
        default=AgentStatus.ACTIVE.value,
        help_text="Agent状态",
    )
    created_at = DateTimeField(default=datetime.utcnow, help_text="创建时间")
    updated_at = DateTimeField(default=datetime.utcnow, help_text="更新时间")

    class Meta:
        table_name = "agents"
        database = get_database()

    def save(self, *args, **kwargs):
        """保存时更新时间戳"""
        self.updated_at = datetime.utcnow()
        return super().save(*args, **kwargs)

    def get_config(self):
        """获取Agent配置"""
        if self.config:
            try:
                return json.loads(self.config)
            except json.JSONDecodeError:
                return {}
        return {}

    def set_config(self, config_dict):
        """设置Agent配置"""
        self.config = json.dumps(config_dict)
        self.save()

    @property
    def is_active(self):
        """检查Agent是否活跃"""
        return self.status == AgentStatus.ACTIVE.value


class ApiKey(BaseModel):
    """API密钥表 - 基于MaiMConfig设计"""

    id = CharField(
        primary_key=True, max_length=50, help_text="API密钥ID，格式：key_xxx"
    )
    tenant_id = CharField(max_length=50, index=True, help_text="所属租户ID")
    agent_id = CharField(max_length=50, index=True, help_text="所属Agent ID")
    name = CharField(max_length=100, help_text="API密钥名称")
    description = TextField(null=True, help_text="API密钥描述")
    api_key = CharField(max_length=255, unique=True, index=True, help_text="API密钥值")
    permissions = TextField(default="[]", help_text="权限列表，JSON格式")
    status = CharField(
        max_length=20,
        choices=[(e.value, e.value) for e in ApiKeyStatus],
        default=ApiKeyStatus.ACTIVE.value,
        help_text="API密钥状态",
    )
    expires_at = DateTimeField(null=True, help_text="过期时间")
    last_used_at = DateTimeField(null=True, help_text="最后使用时间")
    usage_count = IntegerField(default=0, help_text="使用次数")
    created_at = DateTimeField(default=datetime.utcnow, help_text="创建时间")
    updated_at = DateTimeField(default=datetime.utcnow, help_text="更新时间")

    class Meta:
        table_name = "api_keys"
        database = get_database()
        # 创建复合索引
        indexes = ((("tenant_id", "agent_id"), False),)

    def save(self, *args, **kwargs):
        """保存时更新时间戳"""
        self.updated_at = datetime.utcnow()
        return super().save(*args, **kwargs)

    def get_permissions(self):
        """获取权限列表"""
        if self.permissions:
            try:
                return json.loads(self.permissions)
            except json.JSONDecodeError:
                return []
        return []

    def set_permissions(self, permissions_list):
        """设置权限列表"""
        self.permissions = json.dumps(permissions_list)
        self.save()

    def has_permission(self, permission):
        """检查是否有指定权限"""
        return permission in self.get_permissions()

    def is_expired(self):
        """检查是否已过期"""
        if self.expires_at:
            return datetime.utcnow() > self.expires_at
        return False

    @property
    def is_active(self):
        """检查API密钥是否活跃且未过期"""
        return self.status == ApiKeyStatus.ACTIVE.value and not self.is_expired()


class AgentActiveState(BaseModel):
    """Agent 活跃状态，供异步任务管理器按 TTL 判定是否需要持续运行"""

    tenant_id = CharField(max_length=50, index=True, help_text="租户ID")
    agent_id = CharField(max_length=50, index=True, help_text="Agent ID")
    last_seen_at = DateTimeField(default=datetime.utcnow, help_text="最近一次心跳时间")
    ttl_seconds = IntegerField(default=300, help_text="活跃 TTL，秒")
    expires_at = DateTimeField(index=True, help_text="到期时间，用于筛选仍然活跃的记录")

    class Meta:
        table_name = "agent_active_states"
        database = get_database()
        indexes = (
            (("tenant_id", "agent_id"), True),
            (("expires_at",), False),
        )

    def save(self, *args, **kwargs):
        """保存时同步计算过期时间"""
        now = datetime.utcnow() if not self.last_seen_at else self.last_seen_at
        if not self.ttl_seconds or self.ttl_seconds <= 0:
            raise ValueError("ttl_seconds 必须为正数")
        self.expires_at = now + timedelta(seconds=self.ttl_seconds)
        self.last_seen_at = now
        return super().save(*args, **kwargs)

    @classmethod
    def touch(
        cls,
        tenant_id: str,
        agent_id: str,
        ttl_seconds: int,
        *,
        current_time: datetime = None,
    ):
        """更新或创建活跃状态，并重置 TTL"""
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds 必须为正数")

        now = current_time or datetime.utcnow()
        expires_at = now + timedelta(seconds=ttl_seconds)

        record, created = cls.get_or_create(
            tenant_id=tenant_id,
            agent_id=agent_id,
            defaults={
                "last_seen_at": now,
                "ttl_seconds": ttl_seconds,
                "expires_at": expires_at,
            },
        )

        if not created:
            record.last_seen_at = now
            record.ttl_seconds = ttl_seconds
            record.expires_at = expires_at
            record.save()

        return record

    @classmethod
    def list_active(cls, *, current_time: datetime = None):
        """列出仍未过期的活跃记录"""
        now = current_time or datetime.utcnow()
        return cls.select().where(cls.expires_at > now)


# 导出所有模型
__all__ = [
    # 枚举类
    "TenantType",
    "TenantStatus",
    "AgentStatus",
    "ApiKeyStatus",
    # 模型类
    "BaseModel",
    "Tenant",
    "Agent",
    "ApiKey",
]
