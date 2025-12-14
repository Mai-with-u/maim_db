"""
数据库模型定义
"""

from sqlalchemy import String, Text, DateTime, JSON, Integer, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional, List, Dict, Any



import logging

from .connection import Base

logger = logging.getLogger(__name__)


class TenantType(str, PyEnum):
    """租户类型"""
    PERSONAL = "personal"
    ENTERPRISE = "enterprise"


class TenantStatus(str, PyEnum):
    """租户状态"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


class AgentStatus(str, PyEnum):
    """Agent状态"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class ApiKeyStatus(str, PyEnum):
    """API密钥状态"""
    ACTIVE = "active"
    DISABLED = "disabled"
    EXPIRED = "expired"





class User(Base):
    """用户表"""
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # 关系
    tenants: Mapped[List["Tenant"]] = relationship(
        "Tenant",
        back_populates="owner",
        cascade="all, delete-orphan",
        foreign_keys="Tenant.owner_id"
    )

    def __repr__(self):
        return f"<User(id='{self.id}', username='{self.username}')>"


class Tenant(Base):
    """租户表"""
    __tablename__ = "tenants"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    tenant_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    tenant_type: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    contact_email: Mapped[Optional[str]] = mapped_column(String(255))
    tenant_config: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(
        String(50),
        default=TenantStatus.ACTIVE.value,
        nullable=False
    )
    owner_id: Mapped[Optional[str]] = mapped_column(
        String(50),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # 关系
    owner: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="tenants",
        foreign_keys=[owner_id]
    )
    agents: Mapped[List["Agent"]] = relationship(
        "Agent",
        back_populates="tenant",
        cascade="all, delete-orphan"
    )
    api_keys: Mapped[List["ApiKey"]] = relationship(
        "ApiKey",
        back_populates="tenant",
        cascade="all, delete-orphan"
    )
    plugin_settings: Mapped[List["PluginSettings"]] = relationship(
        "PluginSettings",
        back_populates="tenant",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Tenant(id='{self.id}', name='{self.tenant_name}')>"


class Agent(Base):
    """Agent表"""
    __tablename__ = "agents"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    template_id: Mapped[Optional[str]] = mapped_column(String(50))
    config: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(
        String(50),
        default=AgentStatus.ACTIVE.value,
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # 关系
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="agents")
    api_keys: Mapped[List["ApiKey"]] = relationship(
        "ApiKey",
        back_populates="agent",
        cascade="all, delete-orphan"
    )
    plugin_settings: Mapped[List["PluginSettings"]] = relationship(
        "PluginSettings",
        back_populates="agent",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Agent(id='{self.id}', name='{self.name}', tenant_id='{self.tenant_id}')>"


class ApiKey(Base):
    """API密钥表"""
    __tablename__ = "api_keys"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    agent_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    api_key: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    permissions: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list)
    status: Mapped[str] = mapped_column(
        String(50),
        default=ApiKeyStatus.ACTIVE.value,
        nullable=False
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    usage_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # 关系
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="api_keys")
    agent: Mapped["Agent"] = relationship("Agent", back_populates="api_keys")

    def __repr__(self):
        return f"<ApiKey(id='{self.id}', name='{self.name}', tenant_id='{self.tenant_id}')>"


class PluginSettings(Base):
    """插件配置表"""
    __tablename__ = "plugin_settings"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    agent_id: Mapped[Optional[str]] = mapped_column(
        String(50),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    plugin_name: Mapped[str] = mapped_column(String(100), nullable=False)
    enabled: Mapped[bool] = mapped_column(default=False, nullable=False)
    config: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default={})
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # 关系
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="plugin_settings")
    agent: Mapped[Optional["Agent"]] = relationship("Agent", back_populates="plugin_settings")

    def __repr__(self):
        return f"<PluginSettings(id='{self.id}', plugin='{self.plugin_name}', tenant='{self.tenant_id}')>"



async def create_tables() -> None:
    """创建所有数据库表"""
    try:
        from .connection import engine
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("数据库表创建成功")
    except Exception as e:
        logger.error(f"数据库表创建失败: {e}")
        raise


