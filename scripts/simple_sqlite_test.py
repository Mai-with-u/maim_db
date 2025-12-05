#!/usr/bin/env python3
"""
简单SQLite启动测试
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

def test_sqlite_only():
    """只测试SQLite启动，不做复杂操作"""
    print("🚀 测试maim_db SQLite默认启动...")

    try:
        # 测试导入
        from src.core import get_database, init_database, close_database
        from src.core.config import DatabaseConfig
        print("✅ 导入成功")

        # 测试配置
        config = DatabaseConfig()
        print(f"📋 数据库类型: {config.get_database_type()}")
        print(f"📋 连接URL: {config.get_database_url()}")

        # 测试数据库连接
        database = get_database()
        print(f"🔗 数据库实例: {type(database).__name__}")

        # 测试初始化
        init_database()
        print("✅ 数据库初始化成功")

        # 关闭连接
        close_database()
        print("✅ 数据库关闭成功")

        print("\n🎉 SQLite默认启动测试成功！")
        return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_sqlite_only()