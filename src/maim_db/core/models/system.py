"""
控制面模型定义
包含 User, Tenant, ApiKey, Agent 等系统级数据模型
"""
import uuid
from datetime import datetime

from peewee import (
    BooleanField,
    CharField,
    DateTimeField,
    ForeignKeyField,
    IntegerField,
    Model,
    TextField,
    UUIDField,
)

from ..database import get_database


class BaseModel(Model):
    """系统模型基类，不包含多租户字段"""

    class Meta:
        database = get_database()


class Tenant(BaseModel):
    """租户模型"""

    id = UUIDField(primary_key=True, default=uuid.uuid4)
    name = CharField(max_length=255, unique=True, index=True)
    description = TextField(null=True)
    is_active = BooleanField(default=True)
    max_users = IntegerField(default=10)
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)

    class Meta:
        table_name = 'tenants'
        database = get_database()

    def save(self, *args, **kwargs):
        """保存时更新时间戳"""
        if self.updated_at:
            self.updated_at = datetime.utcnow()
        return super().save(*args, **kwargs)


class User(BaseModel):
    """用户模型"""

    id = UUIDField(primary_key=True, default=uuid.uuid4)
    username = CharField(max_length=255, unique=True, index=True)
    email = CharField(max_length=255, unique=True, index=True)
    password_hash = CharField(max_length=255)
    full_name = CharField(max_length=255, null=True)
    is_active = BooleanField(default=True)
    is_superuser = BooleanField(default=False)
    last_login = DateTimeField(null=True)
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)

    # 租户关联
    tenant = ForeignKeyField(Tenant, backref='users', field='id')

    class Meta:
        table_name = 'users'
        database = get_database()

    def save(self, *args, **kwargs):
        """保存时更新时间戳"""
        if self.updated_at:
            self.updated_at = datetime.utcnow()
        return super().save(*args, **kwargs)


class Agent(BaseModel):
    """Agent 模型"""

    id = UUIDField(primary_key=True, default=uuid.uuid4)
    name = CharField(max_length=255, index=True)
    description = TextField(null=True)
    config = TextField(null=True)  # JSON 格式的配置信息
    model_type = CharField(max_length=100, default='gpt-3.5-turbo')
    is_active = BooleanField(default=True)
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)

    # 拥有者关联
    user = ForeignKeyField(User, backref='agents', field='id')
    tenant = ForeignKeyField(Tenant, backref='agents', field='id')

    class Meta:
        table_name = 'agents'
        database = get_database()
        indexes = (
            (('name', 'tenant'), True),  # 租户内名称唯一
        )

    def save(self, *args, **kwargs):
        """保存时更新时间戳"""
        if self.updated_at:
            self.updated_at = datetime.utcnow()
        return super().save(*args, **kwargs)


class ApiKey(BaseModel):
    """API密钥模型"""

    id = UUIDField(primary_key=True, default=uuid.uuid4)
    key_hash = CharField(max_length=255, unique=True, index=True)  # 存储哈希值
    name = CharField(max_length=255)
    description = TextField(null=True)
    is_active = BooleanField(default=True)
    expires_at = DateTimeField(null=True)
    last_used_at = DateTimeField(null=True)
    usage_count = IntegerField(default=0)
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)

    # 关联的 Agent
    agent = ForeignKeyField(Agent, backref='api_keys', field='id')

    class Meta:
        table_name = 'api_keys'
        database = get_database()

    def save(self, *args, **kwargs):
        """保存时更新时间戳"""
        if self.updated_at:
            self.updated_at = datetime.utcnow()
        return super().save(*args, **kwargs)
