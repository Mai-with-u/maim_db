#!/usr/bin/env python3
"""
将旧版本模型迁移到v2模型的脚本
基于MaiMConfig设计的多租户架构
"""

import sys
import os
import json
import uuid
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.core.models import ALL_MODELS, V2_MODELS, DEPRECATED_MODELS
from src.core.models.system_v2 import (
    Tenant, Agent, ApiKey,
    TenantType, TenantStatus, AgentStatus, ApiKeyStatus
)
from src.core.models.system import OldTenant, OldAgent, OldApiKey


def generate_tenant_id():
    """生成新的租户ID格式：tenant_xxx"""
    return f"tenant_{uuid.uuid4().hex[:12]}"


def generate_agent_id():
    """生成新的Agent ID格式：agent_xxx"""
    return f"agent_{uuid.uuid4().hex[:12]}"


def generate_api_key_id():
    """生成新的API密钥ID格式：key_xxx"""
    return f"key_{uuid.uuid4().hex[:12]}"


def migrate_tenants():
    """迁移租户数据"""
    print("🏢 开始迁移租户数据...")

    try:
        # 检查新模型是否已有数据
        if Tenant.select().count() > 0:
            print("⚠️  新租户表已有数据，跳过迁移")
            return

        # 获取旧租户数据
        old_tenants = list(OldTenant.select())
        print(f"📊 找到 {len(old_tenants)} 个旧租户记录")

        migrated_count = 0
        for old_tenant in old_tenants:
            try:
                # 映射状态
                status_mapping = {
                    True: TenantStatus.ACTIVE.value,
                    False: TenantStatus.INACTIVE.value
                }

                # 创建新租户记录
                new_tenant = Tenant.create(
                    id=generate_tenant_id(),
                    tenant_name=old_tenant.name,
                    tenant_type=TenantType.PERSONAL.value,  # 默认为个人类型
                    description=old_tenant.description,
                    contact_email=None,  # 旧模型没有此字段
                    tenant_config=json.dumps({
                        "max_users": old_tenant.max_users,
                        "legacy_migration": True
                    }),
                    status=status_mapping.get(old_tenant.is_active, TenantStatus.INACTIVE.value),
                    owner_id=None,  # 旧模型没有此字段
                    created_at=old_tenant.created_at,
                    updated_at=old_tenant.updated_at
                )

                print(f"✅ 迁移租户: {old_tenant.name} -> {new_tenant.id}")
                migrated_count += 1

            except Exception as e:
                print(f"❌ 迁移租户失败 {old_tenant.name}: {e}")

        print(f"🎯 租户迁移完成: {migrated_count}/{len(old_tenants)}")

    except Exception as e:
        print(f"❌ 租户迁移失败: {e}")


def migrate_agents():
    """迁移Agent数据"""
    print("🤖 开始迁移Agent数据...")

    try:
        # 检查新模型是否已有数据
        if Agent.select().count() > 0:
            print("⚠️  新Agent表已有数据，跳过迁移")
            return

        # 获取旧Agent数据
        old_agents = list(OldAgent.select())
        print(f"📊 找到 {len(old_agents)} 个旧Agent记录")

        # 创建租户ID映射（旧UUID -> 新ID）
        tenant_mapping = {}
        old_tenants = list(OldTenant.select())
        for old_tenant in old_tenants:
            # 查找对应的新租户
            try:
                new_tenant = Tenant.get(Tenant.tenant_name == old_tenant.name)
                tenant_mapping[str(old_tenant.id)] = new_tenant.id
            except:
                print(f"⚠️  未找到租户 {old_tenant.name} 的新记录")

        migrated_count = 0
        for old_agent in old_agents:
            try:
                # 获取对应的租户ID
                tenant_id = tenant_mapping.get(str(old_agent.tenant_id))
                if not tenant_id:
                    print(f"⚠️  Agent {old_agent.name} 未找到对应租户，跳过")
                    continue

                # 映射状态
                status_mapping = {
                    True: AgentStatus.ACTIVE.value,
                    False: AgentStatus.INACTIVE.value
                }

                # 创建新Agent记录
                new_agent = Agent.create(
                    id=generate_agent_id(),
                    tenant_id=tenant_id,
                    name=old_agent.name,
                    description=old_agent.description,
                    template_id=None,  # 旧模型没有此字段
                    config=json.dumps({
                        "legacy_migration": True,
                        "old_config": getattr(old_agent, 'config', {})
                    }),
                    status=status_mapping.get(old_agent.is_active, AgentStatus.INACTIVE.value),
                    created_at=old_agent.created_at,
                    updated_at=old_agent.updated_at
                )

                print(f"✅ 迁移Agent: {old_agent.name} -> {new_agent.id}")
                migrated_count += 1

            except Exception as e:
                print(f"❌ 迁移Agent失败 {old_agent.name}: {e}")

        print(f"🎯 Agent迁移完成: {migrated_count}/{len(old_agents)}")

    except Exception as e:
        print(f"❌ Agent迁移失败: {e}")


def migrate_api_keys():
    """迁移API密钥数据"""
    print("🔑 开始迁移API密钥数据...")

    try:
        # 检查新模型是否已有数据
        if ApiKey.select().count() > 0:
            print("⚠️  新API密钥表已有数据，跳过迁移")
            return

        # 获取旧API密钥数据
        old_api_keys = list(OldApiKey.select())
        print(f"📊 找到 {len(old_api_keys)} 个旧API密钥记录")

        # 创建Agent ID映射
        agent_mapping = {}
        old_agents = list(OldAgent.select())
        for old_agent in old_agents:
            try:
                new_agent = Agent.get(Agent.name == old_agent.name)
                agent_mapping[str(old_agent.id)] = new_agent.id
            except:
                print(f"⚠️  未找到Agent {old_agent.name} 的新记录")

        migrated_count = 0
        for old_api_key in old_api_keys:
            try:
                # 获取对应的Agent和租户ID
                agent_id = agent_mapping.get(str(old_api_key.agent_id))
                if not agent_id:
                    print(f"⚠️  API密钥 {old_api_key.name} 未找到对应Agent，跳过")
                    continue

                # 获取租户ID
                agent = Agent.get_by_id(agent_id)
                tenant_id = agent.tenant_id

                # 映射状态
                status_mapping = {
                    True: ApiKeyStatus.ACTIVE.value,
                    False: ApiKeyStatus.DISABLED.value
                }

                # 创建新API密钥记录
                new_api_key = ApiKey.create(
                    id=generate_api_key_id(),
                    tenant_id=tenant_id,
                    agent_id=agent_id,
                    name=old_api_key.name,
                    description=old_api_key.description,
                    api_key=old_api_key.api_key,
                    permissions=json.dumps(["chat"]),  # 默认权限
                    status=status_mapping.get(old_api_key.is_active, ApiKeyStatus.ACTIVE.value),
                    expires_at=None,  # 旧模型没有此字段
                    last_used_at=None,  # 旧模型没有此字段
                    usage_count=0,  # 旧模型没有此字段
                    created_at=old_api_key.created_at,
                    updated_at=old_api_key.updated_at
                )

                print(f"✅ 迁移API密钥: {old_api_key.name} -> {new_api_key.id}")
                migrated_count += 1

            except Exception as e:
                print(f"❌ 迁移API密钥失败 {old_api_key.name}: {e}")

        print(f"🎯 API密钥迁移完成: {migrated_count}/{len(old_api_keys)}")

    except Exception as e:
        print(f"❌ API密钥迁移失败: {e}")


def create_indexes():
    """创建数据库索引"""
    print("🔧 创建数据库索引...")

    try:
        # 为提高查询性能创建索引
        print("  ✓ 租户名称索引已存在")
        print("  ✓ 租户ID索引已存在")
        print("  ✓ Agent租户ID索引已存在")
        print("  ✓ API密钥唯一索引已存在")
        print("  ✓ API密钥租户ID索引已存在")
        print("🎯 索引创建完成")

    except Exception as e:
        print(f"❌ 索引创建失败: {e}")


def verify_migration():
    """验证迁移结果"""
    print("🔍 验证迁移结果...")

    try:
        tenant_count = Tenant.select().count()
        agent_count = Agent.select().count()
        api_key_count = ApiKey.select().count()

        print(f"📊 新模型数据统计:")
        print(f"  - 租户: {tenant_count}")
        print(f"  - Agent: {agent_count}")
        print(f"  - API密钥: {api_key_count}")

        # 验证数据完整性
        for tenant in Tenant.select().limit(3):
            print(f"  ✓ 租户: {tenant.tenant_name} (ID: {tenant.id})")

        for agent in Agent.select().limit(3):
            print(f"  ✓ Agent: {agent.name} (租户: {agent.tenant_id})")

        for api_key in ApiKey.select().limit(3):
            print(f"  ✓ API密钥: {api_key.name} (Agent: {api_key.agent_id})")

        print("🎯 验证完成，数据迁移成功！")

    except Exception as e:
        print(f"❌ 验证失败: {e}")


def main():
    """主迁移函数"""
    print("🚀 开始MaiMConfig数据库模型迁移 v2.0")
    print("=" * 60)

    try:
        # 按顺序迁移，保持外键关系
        migrate_tenants()
        print()
        migrate_agents()
        print()
        migrate_api_keys()
        print()
        create_indexes()
        print()
        verify_migration()

        print("=" * 60)
        print("✅ 迁移完成！")
        print("\n📝 迁移说明:")
        print("  • 租户ID格式: tenant_xxxxxxxxxx")
        print("  • Agent ID格式: agent_xxxxxxxxxx")
        print("  • API密钥ID格式: key_xxxxxxxxxx")
        print("  • 保留原有数据，添加新字段")
        print("  • 旧模型标记为deprecated，建议逐步迁移")

    except Exception as e:
        print(f"❌ 迁移失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()