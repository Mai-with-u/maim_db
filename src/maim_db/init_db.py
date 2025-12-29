"""
统一数据库初始化脚本
用于在容器启动时创建所有必要的数据库表
"""
import sys
import os

# Ensure we can import from current package structure if run directly
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from maim_db.core.database import db_manager
from maim_db.core.models import ALL_MODELS

def init_db():
    print("🚀 开始统一数据库初始化...")
    
    # 1. 连接数据库
    try:
        db_manager.connect()
        print("✅ 数据库连接成功")
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        sys.exit(1)

    # 2. 创建所有表
    try:
        print(f"📦 准备创建 {len(ALL_MODELS)} 个模型对应的表...")
        db_manager.create_tables(ALL_MODELS)
        print("✅ 所有表创建成功")
    except Exception as e:
        print(f"❌ 创建表失败: {e}")
        # Print more detail if available
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db_manager.close()
        print("db connection closed.")

if __name__ == "__main__":
    init_db()
