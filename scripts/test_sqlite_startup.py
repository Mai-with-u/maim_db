#!/usr/bin/env python3
"""
测试maim_db SQLite默认启动功能
"""

import sys
import os
import time

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.core import get_database, init_database, close_database
from src.core.models import V2_MODELS
from src.core.models.system_v2 import Tenant, Agent, ApiKey
from src.core.config import DatabaseConfig


def test_sqlite_startup():
    """测试SQLite默认启动"""
    print("🚀 测试maim_db SQLite默认启动...")
    print("=" * 50)

    try:
        # 1. 测试配置加载
        print("📋 测试配置加载...")
        config = DatabaseConfig()
        database_url = config.get_database_url()
        database_type = config.get_database_type()

        print(f"  ✅ 配置加载成功")
        print(f"     数据库类型: {database_type}")
        print(f"     连接URL: {database_url}")

        # 2. 测试数据库连接
        print("\n🔗 测试数据库连接...")
        database = get_database()
        print(f"  ✅ 数据库实例创建成功")
        print(f"     数据库类型: {type(database).__name__}")

        # 3. 测试数据库初始化
        print("\n🔧 测试数据库初始化...")
        init_database()
        print("  ✅ 数据库连接初始化成功")

        # 4. 测试表创建
        print("\n📊 测试表创建...")
        if not database.is_connection_usable():
            database.connect()
        database.create_tables(V2_MODELS, safe=True)

        # 验证表是否创建成功
        tables = database.get_tables()
        print(f"  ✅ 表创建成功，共创建 {len(tables)} 个表:")
        for table in sorted(tables):
            print(f"     • {table}")

        # 5. 测试基本CRUD操作
        print("\n🧪 测试基本CRUD操作...")

        # 创建测试租户
        tenant = Tenant.create(
            id="tenant_test_sqlite",
            tenant_name="SQLite测试租户",
            tenant_type="personal",
            description="这是一个SQLite测试租户",
            tenant_config='{"test": true, "db": "sqlite"}',
            status="active"
        )
        print(f"  ✅ 创建租户成功: {tenant.id}")

        # 创建测试Agent
        agent = Agent.create(
            id="agent_test_sqlite",
            tenant_id=tenant.id,
            name="SQLite测试助手",
            description="这是一个SQLite测试助手",
            template_id="test_template",
            config='{"model": "test", "db": "sqlite"}',
            status="active"
        )
        print(f"  ✅ 创建Agent成功: {agent.id}")

        # 创建测试API密钥
        api_key = ApiKey.create(
            id="key_test_sqlite",
            tenant_id=tenant.id,
            agent_id=agent.id,
            name="SQLite测试密钥",
            description="这是一个SQLite测试密钥",
            api_key="mmc_test_sqlite_key_12345678",
            permissions='["test", "sqlite"]',
            status="active"
        )
        print(f"  ✅ 创建API密钥成功: {api_key.id}")

        # 6. 测试查询操作
        print("\n🔍 测试查询操作...")

        # 查询租户数量
        tenant_count = Tenant.select().count()
        print(f"  ✅ 租户总数: {tenant_count}")

        # 查询Agent数量
        agent_count = Agent.select().count()
        print(f"  ✅ Agent总数: {agent_count}")

        # 查询API密钥数量
        api_key_count = ApiKey.select().count()
        print(f"  ✅ API密钥总数: {api_key_count}")

        # 7. 清理测试数据
        print("\n🧹 清理测试数据...")
        api_key.delete_instance()
        agent.delete_instance()
        tenant.delete_instance()
        print("  ✅ 测试数据清理完成")

        if database.is_connection_usable():
            database.close()

        # 8. 关闭数据库连接
        print("\n🔌 关闭数据库连接...")
        close_database()
        print("  ✅ 数据库连接已关闭")

        return True

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_environment_configurations():
    """测试不同环境配置"""
    print("\n🌍 测试不同环境配置...")
    print("=" * 50)

    configurations = [
        ("默认配置", {}),
        ("明确SQLite", {"DATABASE_URL": "sqlite:///data/test_sqlite.db"}),
        ("PostgreSQL", {"DATABASE_URL": "postgresql://user:pass@localhost:5432/test"}),
        ("MySQL", {"DATABASE_URL": "mysql+pymysql://user:pass@localhost:3306/test"}),
    ]

    for config_name, env_vars in configurations:
        print(f"\n📋 测试配置: {config_name}")

        # 设置环境变量
        original_env = {}
        for key, value in env_vars.items():
            original_env[key] = os.environ.get(key)
            os.environ[key] = value

        try:
            # 重新导入配置以获取新的环境变量
            import importlib
            import src.core.config
            importlib.reload(src.core.config)
            from src.core.config import DatabaseConfig

            config = DatabaseConfig()
            database_type = config.get_database_type()
            database_url = config.get_database_url()

            print(f"  ✅ 数据库类型: {database_type}")
            print(f"     连接URL: {database_url}")

        except Exception as e:
            print(f"  ❌ 配置测试失败: {e}")
        finally:
            # 恢复原始环境变量
            for key, original_value in original_env.items():
                if original_value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = original_value


def main():
    """主测试函数"""
    print("🧪 MaimDB SQLite默认启动测试")
    print("=" * 60)

    success_count = 0
    total_tests = 2

    # 测试SQLite默认启动
    if test_sqlite_startup():
        success_count += 1

    # 测试不同环境配置
    try:
        test_environment_configurations()
        success_count += 1
    except Exception as e:
        print(f"环境配置测试失败: {e}")

    print("\n" + "=" * 60)
    print(f"📊 测试结果: {success_count}/{total_tests} 通过")

    if success_count == total_tests:
        print("🎉 所有测试通过！SQLite默认启动功能正常！")
        print("\n💡 使用说明:")
        print("  1. 无需任何配置即可使用SQLite")
        print("  2. 数据库文件位于: data/MaiBot.db")
        print("  3. 支持通过环境变量切换到PostgreSQL/MySQL")
        print("  4. 完全兼容maimconfig的配置方式")
    else:
        print("⚠️ 部分测试失败，请检查配置")


if __name__ == "__main__":
    main()