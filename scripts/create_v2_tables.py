#!/usr/bin/env python3
"""
创建v2版本数据库表
基于MaiMConfig设计的多租户架构
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.core.models import V2_MODELS
from src.database import get_database


def create_tables():
    """创建所有v2模型对应的数据库表"""
    print("🗄️ 创建v2版本数据库表...")

    try:
        database = get_database()

        print(f"📊 将创建 {len(V2_MODELS)} 个表的数据库:")
        for model in V2_MODELS:
            table_name = model._meta.table_name
            print(f"  • {table_name}")

        # 确保数据库连接正常
        database.connect()

        # 批量创建表
        database.create_tables(V2_MODELS, safe=True)

        print("✅ 数据库表创建完成")

        # 验证表是否创建成功
        tables = database.get_tables()
        print(f"\n📋 当前数据库中的表: {len(tables)}")
        for table in sorted(tables):
            print(f"  • {table}")

        # 关闭连接
        database.close()

        return True

    except Exception as e:
        print(f"❌ 创建数据库表失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def drop_tables():
    """删除v2版本的表（危险操作）"""
    print("⚠️  删除v2版本数据库表...")

    confirm = input("⚠️  这将删除所有v2版本的数据表，确定要继续吗？(yes/no): ")
    if confirm.lower() != 'yes':
        print("❌ 操作已取消")
        return False

    try:
        database = get_database()
        database.connect()

        print("🗑️  删除以下表:")
        for model in V2_MODELS:
            table_name = model._meta.table_name
            print(f"  • {table_name}")
            database.drop_table(table_name)

        print("✅ 数据库表删除完成")
        database.close()
        return True

    except Exception as e:
        print(f"❌ 删除数据库表失败: {e}")
        return False


def main():
    """主函数"""
    print("🚀 MaiMConfig v2数据库表管理")
    print("=" * 50)

    try:
        # 选择操作
        print("请选择操作:")
        print("1. 创建v2版本数据库表")
        print("2. 删除v2版本数据库表（危险）")
        print("3. 仅验证模型")

        choice = input("\n请输入选择 (1/2/3): ").strip()

        if choice == '1':
            success = create_tables()
            if success:
                print("\n✅ v2数据库表创建完成！")
                print("\n📝 数据库结构说明:")
                print("  • tenants: 租户表，支持多租户隔离")
                print("  • agents: Agent配置表，存储AI助手配置")
                print("  • api_keys: API密钥表，管理访问权限")
                print("\n🔧 ID格式:")
                print("  • 租户ID: tenant_xxxxxxxxxx")
                print("  • Agent ID: agent_xxxxxxxxxx")
                print("  • API密钥ID: key_xxxxxxxxxx")
                print("\n⚡️ 支持的功能:")
                print("  • JSON配置存储")
                print("  • 状态管理")
                print("  • 权限控制")
                print("  • 使用统计")

        elif choice == '2':
            drop_tables()

        elif choice == '3':
            from src.core.models import V2_MODELS, Tenant, Agent, ApiKey
            print("📊 模型验证:")
            print(f"  • V2模型数量: {len(V2_MODELS)}")
            print(f"  • Tenant: {Tenant.__name__}")
            print(f"  • Agent: {Agent.__name__}")
            print(f"  • ApiKey: {ApiKey.__name__}")
            print("✅ 模型定义正常")

        else:
            print("❌ 无效选择")

    except Exception as e:
        print(f"❌ 操作失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()