"""
异步版本的maim_db模型
为maimconfig提供异步接口
"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional

from .models.system_v2 import Agent as MaimDbAgent
from .models.system_v2 import AgentStatus, ApiKeyStatus, TenantStatus, TenantType
from .models.system_v2 import ApiKey as MaimDbApiKey
from .models.system_v2 import Tenant as MaimDbTenant


class AsyncTenant:
    """异步租户模型"""

    def __init__(self, tenant: MaimDbTenant = None):
        if tenant:
            self.id = tenant.id
            self.tenant_name = tenant.tenant_name
            self.tenant_type = TenantType(tenant.tenant_type)
            self.description = tenant.description
            self.contact_email = tenant.contact_email
            self.tenant_config = self._parse_json(tenant.tenant_config)
            self.status = TenantStatus(tenant.status)
            self.owner_id = tenant.owner_id
            self.created_at = tenant.created_at
            self.updated_at = tenant.updated_at
            self._tenant = tenant
        else:
            self.id = None
            self.tenant_name = None
            self.tenant_type = TenantType.PERSONAL
            self.description = None
            self.contact_email = None
            self.tenant_config = None
            self.status = TenantStatus.ACTIVE
            self.owner_id = None
            self.created_at = datetime.utcnow()
            self.updated_at = datetime.utcnow()
            self._tenant = None

    def _parse_json(self, json_str: str) -> Optional[Dict]:
        if not json_str:
            return None
        try:
            return json.loads(json_str)
        except (json.JSONDecodeError, TypeError):
            return None

    @classmethod
    async def create(cls, **kwargs) -> 'AsyncTenant':
        """创建租户"""
        def _create():
            data = {
                'tenant_name': kwargs.get('tenant_name'),
                'tenant_type': kwargs.get('tenant_type', TenantType.PERSONAL.value),
                'description': kwargs.get('description'),
                'contact_email': kwargs.get('contact_email'),
                'tenant_config': json.dumps(kwargs.get('tenant_config', {})),
                'status': kwargs.get('status', TenantStatus.ACTIVE.value),
                'owner_id': kwargs.get('owner_id'),
            }

            if 'id' not in kwargs:
                data['id'] = f"tenant_{uuid.uuid4().hex[:12]}"
            else:
                data['id'] = kwargs['id']

            return MaimDbTenant.create(**data)

        tenant = await asyncio.get_event_loop().run_in_executor(None, _create)
        return cls(tenant)

    @classmethod
    async def get(cls, tenant_id: str) -> Optional['AsyncTenant']:
        """获取租户"""
        def _get():
            try:
                return MaimDbTenant.get_by_id(tenant_id)
            except MaimDbTenant.DoesNotExist:
                return None

        tenant = await asyncio.get_event_loop().run_in_executor(None, _get)
        return cls(tenant) if tenant else None

    @classmethod
    async def get_by_name(cls, tenant_name: str) -> Optional['AsyncTenant']:
        """根据名称获取租户"""
        def _get():
            try:
                return MaimDbTenant.get(MaimDbTenant.tenant_name == tenant_name)
            except MaimDbTenant.DoesNotExist:
                return None

        tenant = await asyncio.get_event_loop().run_in_executor(None, _get)
        return cls(tenant) if tenant else None

    @classmethod
    async def get_all(cls, limit: int = None, offset: int = 0) -> List['AsyncTenant']:
        """获取所有租户"""
        def _get_all():
            query = MaimDbTenant.select()
            if limit:
                query = query.limit(limit).offset(offset)
            return list(query)

        tenants = await asyncio.get_event_loop().run_in_executor(None, _get_all)
        return [cls(tenant) for tenant in tenants]

    @classmethod
    async def count(cls) -> int:
        """获取租户总数"""
        def _count():
            return MaimDbTenant.select().count()

        return await asyncio.get_event_loop().run_in_executor(None, _count)

    async def update(self, **kwargs) -> 'AsyncTenant':
        """更新租户"""
        if not self._tenant:
            raise RuntimeError("租户实例未关联到数据库记录")

        def _update():
            for field, value in kwargs.items():
                if hasattr(self._tenant, field):
                    if field == 'tenant_config' and value is not None:
                        value = json.dumps(value)
                    setattr(self._tenant, field, value)
            self._tenant.save()
            return self._tenant

        await asyncio.get_event_loop().run_in_executor(None, _update)

        # 更新本地属性
        for field, value in kwargs.items():
            if hasattr(self, field):
                if field == 'tenant_config':
                    value = self._parse_json(json.dumps(value)) if value else None
                setattr(self, field, value)

        return self

    async def delete(self):
        """删除租户"""
        if not self._tenant:
            raise RuntimeError("租户实例未关联到数据库记录")

        def _delete():
            self._tenant.delete_instance()

        await asyncio.get_event_loop().run_in_executor(None, _delete)

    def __repr__(self):
        return f"<AsyncTenant(id='{self.id}', name='{self.tenant_name}')>"


class AsyncAgent:
    """异步Agent模型"""

    def __init__(self, agent: MaimDbAgent = None):
        if agent:
            self.id = agent.id
            self.tenant_id = agent.tenant_id
            self.name = agent.name
            self.description = agent.description
            self.template_id = agent.template_id
            self.config = self._parse_json(agent.config)
            self.status = AgentStatus(agent.status)
            self.created_at = agent.created_at
            self.updated_at = agent.updated_at
            self._agent = agent
        else:
            self.id = None
            self.tenant_id = None
            self.name = None
            self.description = None
            self.template_id = None
            self.config = None
            self.status = AgentStatus.ACTIVE
            self.created_at = datetime.utcnow()
            self.updated_at = datetime.utcnow()
            self._agent = None

    def _parse_json(self, json_str: str) -> Optional[Dict]:
        if not json_str:
            return None
        try:
            return json.loads(json_str)
        except (json.JSONDecodeError, TypeError):
            return None

    @classmethod
    async def create(cls, **kwargs) -> 'AsyncAgent':
        """创建Agent"""
        def _create():
            data = {
                'tenant_id': kwargs.get('tenant_id'),
                'name': kwargs.get('name'),
                'description': kwargs.get('description'),
                'template_id': kwargs.get('template_id'),
                'config': json.dumps(kwargs.get('config', {})),
                'status': kwargs.get('status', AgentStatus.ACTIVE.value),
            }

            if 'id' not in kwargs:
                data['id'] = f"agent_{uuid.uuid4().hex[:12]}"
            else:
                data['id'] = kwargs['id']

            return MaimDbAgent.create(**data)

        agent = await asyncio.get_event_loop().run_in_executor(None, _create)
        return cls(agent)

    @classmethod
    async def get(cls, agent_id: str) -> Optional['AsyncAgent']:
        """获取Agent"""
        def _get():
            try:
                return MaimDbAgent.get_by_id(agent_id)
            except MaimDbAgent.DoesNotExist:
                return None

        agent = await asyncio.get_event_loop().run_in_executor(None, _get)
        return cls(agent) if agent else None

    @classmethod
    async def get_by_tenant(cls, tenant_id: str) -> List['AsyncAgent']:
        """获取租户下的所有Agent"""
        def _get_by_tenant():
            return list(MaimDbAgent.select().where(MaimDbAgent.tenant_id == tenant_id))

        agents = await asyncio.get_event_loop().run_in_executor(None, _get_by_tenant)
        return [cls(agent) for agent in agents]

    async def update(self, **kwargs) -> 'AsyncAgent':
        """更新Agent"""
        if not self._agent:
            raise RuntimeError("Agent实例未关联到数据库记录")

        def _update():
            for field, value in kwargs.items():
                if hasattr(self._agent, field):
                    if field == 'config' and value is not None:
                        value = json.dumps(value)
                    setattr(self._agent, field, value)
            self._agent.save()
            return self._agent

        await asyncio.get_event_loop().run_in_executor(None, _update)

        # 更新本地属性
        for field, value in kwargs.items():
            if hasattr(self, field):
                if field == 'config':
                    value = self._parse_json(json.dumps(value)) if value else None
                setattr(self, field, value)

        return self

    async def delete(self):
        """删除Agent"""
        if not self._agent:
            raise RuntimeError("Agent实例未关联到数据库记录")

        def _delete():
            self._agent.delete_instance()

        await asyncio.get_event_loop().run_in_executor(None, _delete)

    def __repr__(self):
        return f"<AsyncAgent(id='{self.id}', name='{self.name}', tenant_id='{self.tenant_id}')>"


class AsyncApiKey:
    """异步API密钥模型"""

    def __init__(self, api_key: MaimDbApiKey = None):
        if api_key:
            self.id = api_key.id
            self.tenant_id = api_key.tenant_id
            self.agent_id = api_key.agent_id
            self.name = api_key.name
            self.description = api_key.description
            self.api_key = api_key.api_key
            self.permissions = self._parse_json(api_key.permissions)
            self.status = ApiKeyStatus(api_key.status)
            self.expires_at = api_key.expires_at
            self.last_used_at = api_key.last_used_at
            self.usage_count = api_key.usage_count
            self.created_at = api_key.created_at
            self.updated_at = api_key.updated_at
            self._api_key = api_key
        else:
            self.id = None
            self.tenant_id = None
            self.agent_id = None
            self.name = None
            self.description = None
            self.api_key = None
            self.permissions = []
            self.status = ApiKeyStatus.ACTIVE
            self.expires_at = None
            self.last_used_at = None
            self.usage_count = 0
            self.created_at = datetime.utcnow()
            self.updated_at = datetime.utcnow()
            self._api_key = None

    def _parse_json(self, json_str: str) -> List[str]:
        if not json_str:
            return []
        try:
            result = json.loads(json_str)
            return result if isinstance(result, list) else [str(result)]
        except (json.JSONDecodeError, TypeError):
            return []

    @classmethod
    async def create(cls, **kwargs) -> 'AsyncApiKey':
        """创建API密钥"""
        def _create():
            data = {
                'tenant_id': kwargs.get('tenant_id'),
                'agent_id': kwargs.get('agent_id'),
                'name': kwargs.get('name'),
                'description': kwargs.get('description'),
                'api_key': kwargs.get('api_key'),
                'permissions': json.dumps(kwargs.get('permissions', [])),
                'status': kwargs.get('status', ApiKeyStatus.ACTIVE.value),
                'expires_at': kwargs.get('expires_at'),
            }

            if 'id' not in kwargs:
                data['id'] = f"key_{uuid.uuid4().hex[:12]}"
            else:
                data['id'] = kwargs['id']

            return MaimDbApiKey.create(**data)

        api_key = await asyncio.get_event_loop().run_in_executor(None, _create)
        return cls(api_key)

    @classmethod
    async def get(cls, api_key_id: str) -> Optional['AsyncApiKey']:
        """获取API密钥"""
        def _get():
            try:
                return MaimDbApiKey.get_by_id(api_key_id)
            except MaimDbApiKey.DoesNotExist:
                return None

        api_key = await asyncio.get_event_loop().run_in_executor(None, _get)
        return cls(api_key) if api_key else None

    @classmethod
    async def get_by_key(cls, api_key_value: str) -> Optional['AsyncApiKey']:
        """根据API密钥值获取"""
        def _get():
            try:
                return MaimDbApiKey.get(MaimDbApiKey.api_key == api_key_value)
            except MaimDbApiKey.DoesNotExist:
                return None

        api_key = await asyncio.get_event_loop().run_in_executor(None, _get)
        return cls(api_key) if api_key else None

    @classmethod
    async def get_by_tenant(cls, tenant_id: str) -> List['AsyncApiKey']:
        """获取租户下的所有API密钥"""
        def _get_by_tenant():
            return list(MaimDbApiKey.select().where(MaimDbApiKey.tenant_id == tenant_id))

        api_keys = await asyncio.get_event_loop().run_in_executor(None, _get_by_tenant)
        return [cls(api_key) for api_key in api_keys]

    def __repr__(self):
        return f"<AsyncApiKey(id='{self.id}', name='{self.name}', tenant_id='{self.tenant_id}')>"


# 导出异步模型
__all__ = [
    'AsyncTenant', 'AsyncAgent', 'AsyncApiKey',
    'TenantType', 'TenantStatus', 'AgentStatus', 'ApiKeyStatus'
]
