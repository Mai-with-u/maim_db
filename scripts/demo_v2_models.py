#!/usr/bin/env python3
"""
演示新版本v2模型的使用
基于MaiMConfig设计的多租户架构
"""

import sys
import os
import json
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.core.models.system_v2 import (
    Tenant, Agent, ApiKey,
    TenantType, TenantStatus, AgentStatus, ApiKeyStatus
)


def create_sample_tenant():
    """创建示例租户"""
    print("🏢 创建示例租户...")

    try:
        # 检查是否已存在
        if Tenant.select().where(Tenant.tenant_name == "示例企业").exists():
            print("⚠️  示例租户已存在")
            return

        tenant = Tenant.create(
            id="tenant_demo_001",
            tenant_name="示例企业",
            tenant_type=TenantType.ENTERPRISE.value,
            description="这是一个用于演示的示例企业租户",
            contact_email="demo@example.com",
            tenant_config=json.dumps({
                "timezone": "Asia/Shanghai",
                "language": "zh-CN",
                "max_agents": 10,
                "max_api_keys": 50
            }),
            status=TenantStatus.ACTIVE.value
        )

        print(f"✅ 创建租户成功: {tenant.tenant_name}")
        print(f"   ID: {tenant.id}")
        print(f"   类型: {tenant.tenant_type}")
        print(f"   配置: {tenant.get_config()}")
        return tenant

    except Exception as e:
        print(f"❌ 创建租户失败: {e}")
        return None


def create_sample_agent(tenant):
    """创建示例Agent"""
    print("🤖 创建示例Agent...")

    try:
        # 检查是否已存在
        if Agent.select().where(Agent.name == "智能客服助手").exists():
            print("⚠️  示例Agent已存在")
            return

        agent = Agent.create(
            id="agent_demo_001",
            tenant_id=tenant.id,
            name="智能客服助手",
            description="专业的客户服务AI助手，支持多语言对话",
            template_id="customer_service_template",
            config=json.dumps({
                "persona": "友好、专业的客服助手，具有耐心和细致的解答能力",
                "bot_overrides": {
                    "nickname": "小助手",
                    "platform": "web",
                    "qq_account": "123456789"
                },
                "config_overrides": {
                    "personality": {
                        "reply_style": "专业、礼貌",
                        "interest": "客户服务、技术支持"
                    },
                    "chat": {
                        "max_context_size": 20,
                        "response_timeout": 30,
                        "temperature": 0.7
                    }
                },
                "tags": ["客服", "技术支持", "AI助手"]
            }),
            status=AgentStatus.ACTIVE.value
        )

        print(f"✅ 创建Agent成功: {agent.name}")
        print(f"   ID: {agent.id}")
        print(f"   租户ID: {agent.tenant_id}")
        print(f"   状态: {agent.status}")
        print(f"   配置: {agent.get_config()}")
        return agent

    except Exception as e:
        print(f"❌ 创建Agent失败: {e}")
        return None


def create_sample_api_key(tenant, agent):
    """创建示例API密钥"""
    print("🔑 创建示例API密钥...")

    try:
        # 检查是否已存在
        if ApiKey.select().where(ApiKey.name == "生产环境密钥").exists():
            print("⚠️  示例API密钥已存在")
            return

        # 生成API密钥（模拟MaiMConfig的格式）
        import base64
        import uuid

        key_data = f"{tenant.id}_{agent.id}_{uuid.uuid4().hex[:16]}_v1"
        encoded_key = base64.b64encode(key_data.encode()).decode()
        api_key_value = f"mmc_{encoded_key}"

        api_key = ApiKey.create(
            id="key_demo_001",
            tenant_id=tenant.id,
            agent_id=agent.id,
            name="生产环境密钥",
            description="用于生产环境的API调用",
            api_key=api_key_value,
            permissions=json.dumps(["chat", "config_read", "config_write"]),
            status=ApiKeyStatus.ACTIVE.value,
            expires_at=datetime.utcnow() + timedelta(days=365),  # 1年后过期
        )

        print(f"✅ 创建API密钥成功: {api_key.name}")
        print(f"   ID: {api_key.id}")
        print(f"   租户ID: {api_key.tenant_id}")
        print(f"   Agent ID: {api_key.agent_id}")
        print(f"   API密钥: {api_key.api_key[:20]}...")
        print(f"   权限: {api_key.get_permissions()}")
        print(f"   状态: {api_key.status}")
        print(f"   过期时间: {api_key.expires_at}")
        return api_key

    except Exception as e:
        print(f"❌ 创建API密钥失败: {e}")
        return None


def query_demo_data():
    """查询演示数据"""
    print("📊 查询演示数据...")

    try:
        # 查询所有租户
        tenants = list(Tenant.select())
        print(f"\n🏢 租户列表 ({len(tenants)} 个):")
        for tenant in tenants:
            print(f"  • {tenant.tenant_name} ({tenant.id}) - {tenant.status}")

        # 查询所有Agent
        agents = list(Agent.select())
        print(f"\n🤖 Agent列表 ({len(agents)} 个):")
        for agent in agents:
            print(f"  • {agent.name} ({agent.id}) - {agent.status}")

        # 查询所有API密钥
        api_keys = list(ApiKey.select())
        print(f"\n🔑 API密钥列表 ({len(api_keys)} 个):")
        for api_key in api_keys:
            print(f"  • {api_key.name} ({api_key.id}) - {api_key.status}")

        # 查询租户相关的完整信息
        print(f"\n🔗 租户关联信息:")
        for tenant in tenants:
            agents_count = Agent.select().where(Agent.tenant_id == tenant.id).count()
            api_keys_count = ApiKey.select().where(ApiKey.tenant_id == tenant.id).count()
            print(f"  • {tenant.tenant_name}: {agents_count} 个Agent, {api_keys_count} 个API密钥")

    except Exception as e:
        print(f"❌ 查询失败: {e}")


def test_api_key_functionality(api_key):
    """测试API密钥功能"""
    print("🔧 测试API密钥功能...")

    if not api_key:
        print("⚠️  没有API密钥可测试")
        return

    try:
        # 测试权限检查
        has_chat = api_key.has_permission("chat")
        has_config = api_key.has_permission("config_read")
        print(f"  权限 chat: {has_chat}")
        print(f"  权限 config_read: {has_config}")

        # 测试过期检查
        is_expired = api_key.is_expired()
        print(f"  是否过期: {is_expired}")

        # 测试活跃状态
        is_active = api_key.is_active()
        print(f"  是否活跃: {is_active}")

        # 使用计数增加
        api_key.usage_count += 1
        api_key.save()
        print(f"  使用次数: {api_key.usage_count}")

        print("✅ API密钥功能测试完成")

    except Exception as e:
        print(f"❌ API密钥功能测试失败: {e}")


def cleanup_demo_data():
    """清理演示数据"""
    print("🧹 清理演示数据...")

    try:
        # 删除API密钥
        api_keys = list(ApiKey.select().where(ApiKey.name.startswith("示例")))
        for api_key in api_keys:
            api_key.delete_instance()
        print(f"  删除 {len(api_keys)} 个API密钥")

        # 删除Agent
        agents = list(Agent.select().where(Agent.name.startswith("示例")))
        for agent in agents:
            agent.delete_instance()
        print(f"  删除 {len(agents)} 个Agent")

        # 删除租户
        tenants = list(Tenant.select().where(Tenant.tenant_name.startswith("示例")))
        for tenant in tenants:
            tenant.delete_instance()
        print(f"  删除 {len(tenants)} 个租户")

        print("✅ 清理完成")

    except Exception as e:
        print(f"❌ 清理失败: {e}")


def main():
    """主演示函数"""
    print("🚀 MaiMConfig v2模型演示")
    print("=" * 50)

    try:
        # 创建演示数据
        tenant = create_sample_tenant()
        if tenant:
            agent = create_sample_agent(tenant)
            if agent:
                api_key = create_sample_api_key(tenant, agent)
                if api_key:
                    # 测试功能
                    test_api_key_functionality(api_key)

        # 查询数据
        query_demo_data()

        print("\n" + "=" * 50)
        print("✅ 演示完成！")
        print("\n💡 提示:")
        print("  • 租户ID格式: tenant_xxxxxxxxxx")
        print("  • Agent ID格式: agent_xxxxxxxxxx")
        print("  • API密钥ID格式: key_xxxxxxxxxx")
        print("  • 支持JSON配置存储")
        print("  • 完整的多租户隔离")
        print("  • API密钥权限管理")

        # 询问是否清理
        # cleanup_demo_data()

    except Exception as e:
        print(f"❌ 演示失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()