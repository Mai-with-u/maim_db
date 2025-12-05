#!/usr/bin/env python3
"""
MaiMBot数据库一键启动脚本
自动检测环境并启动最适合的数据库
"""

import os
import sys
import time
import json
from pathlib import Path

# 添加当前目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from db_manager import DatabaseManager
from src.core import init_database, ALL_MODELS
from src.core.database import db_manager as core_db_manager


def check_docker_available():
    """检查Docker是否可用"""
    try:
        import subprocess
        subprocess.run(["docker", "--version"], check=True, capture_output=True, timeout=10)
        subprocess.run(["docker-compose", "--version"], check=True, capture_output=True, timeout=10)
        return True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        return False


def auto_start_database():
    """自动启动数据库"""
    print("🚀 MaiMBot数据库自动启动中...")
    print("=" * 50)

    db_manager = DatabaseManager()

    # 检查当前状态
    current_mode = db_manager.get_database_mode()
    print(f"当前数据库模式: {current_mode}")

    # 尝试启动PostgreSQL
    if check_docker_available():
        print("\n📦 Docker可用，尝试启动PostgreSQL...")

        try:
            success = db_manager.start_postgres()
            if success:
                print("✅ PostgreSQL启动成功")

                # 初始化表结构
                print("\n🔧 初始化数据库表结构...")
                if db_manager.init_database_tables():
                    print("✅ 数据库表结构初始化完成")
                else:
                    print("❌ 数据库表结构初始化失败")
                    return False

                # 显示连接信息
                config = db_manager.create_postgres_config()
                print(f"\n📊 PostgreSQL连接信息:")
                print(f"   主机: {config['host']}")
                print(f"   端口: {config['port']}")
                print(f"   数据库: {config['database']}")
                print(f"   用户: {config['user']}")
                print(f"   密码: {config['password']}")

                return True
            else:
                print("❌ PostgreSQL启动失败，回退到SQLite")
        except Exception as e:
            print(f"❌ PostgreSQL启动异常: {e}")
            print("回退到SQLite模式")

    else:
        print("\n⚠️ Docker不可用，使用SQLite模式")

    # 使用SQLite作为备选方案
    print("\n📁 使用SQLite数据库...")

    try:
        # 初始化SQLite数据库
        init_database()

        # 创建表结构
        core_db_manager.create_tables(ALL_MODELS)

        print("✅ SQLite数据库初始化完成")

        # 显示SQLite信息
        sqlite_path = Path(__file__).parent / "data" / "MaiBot.db"
        if sqlite_path.exists():
            size = sqlite_path.stat().st_size / 1024
            print(f"\n📊 SQLite信息:")
            print(f"   文件路径: {sqlite_path}")
            print(f"   文件大小: {size:.1f} KB")

        return True

    except Exception as e:
        print(f"❌ SQLite初始化失败: {e}")
        return False


def show_database_info():
    """显示数据库信息"""
    print("\n📊 数据库状态信息:")
    print("=" * 50)

    db_manager = DatabaseManager()
    info = db_manager.get_database_info()

    print(f"数据库模式: {info['mode']}")
    print(f"运行状态: {info['status']}")
    print(f"数据库类型: {info['type']}")

    if info['mode'] == 'postgres':
        print(f"连接地址: {info['user']}@{info['host']}:{info['port']}/{info['database']}")
        print(f"容器状态: {'运行中' if info['container_running'] else '未运行'}")
    else:
        print(f"文件路径: {info['path']}")
        print(f"文件大小: {info['size']}")


def create_env_file():
    """创建环境变量文件"""
    env_file = Path(__file__).parent / ".env"

    if not env_file.exists():
        db_manager = DatabaseManager()
        config = db_manager.create_postgres_config()

        env_content = f"""# MaiMBot数据库配置
# PostgreSQL配置（优先使用）
DB_HOST={config['host']}
DB_PORT={config['port']}
DB_NAME={config['database']}
DB_USER={config['user']}
DB_PASSWORD={config['password']}

# 可选配置
DB_MAX_CONNECTIONS=20
DB_CONNECTION_TIMEOUT=30
DB_TIMEZONE=UTC
"""

        with open(env_file, 'w') as f:
            f.write(env_content)

        print(f"✅ 环境变量文件已创建: {env_file}")
        print("   您可以修改其中的配置参数")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="MaiMBot数据库一键启动")
    parser.add_argument('--info-only', action='store_true', help='仅显示数据库信息')
    parser.add_argument('--create-env', action='store_true', help='创建环境变量文件')
    parser.add_argument('--sqlite-only', action='store_true', help='强制使用SQLite')

    args = parser.parse_args()

    if args.create_env:
        create_env_file()
        return

    if args.info_only:
        show_database_info()
        return

    if args.sqlite_only:
        print("📁 强制使用SQLite模式...")
        # 清除PostgreSQL环境变量
        for key in ['DB_HOST', 'DB_PORT', 'DB_NAME', 'DB_USER', 'DB_PASSWORD']:
            os.environ.pop(key, None)

    # 自动启动数据库
    success = auto_start_database()

    if success:
        print("\n🎉 数据库启动成功！")
        show_database_info()

        print(f"\n💡 使用说明:")
        print(f"   1. MaiMBot现在可以正常使用多租户功能")
        print(f"   2. 数据库自动配置完成，无需额外设置")
        print(f"   3. 使用 'python db_manager.py status' 查看状态")

        # 提示创建环境变量文件
        env_file = Path(__file__).parent / ".env"
        if not env_file.exists():
            print(f"   4. 使用 'python {__file__} --create-env' 创建配置文件")
    else:
        print("\n❌ 数据库启动失败！")
        print("请检查Docker安装或权限设置")


if __name__ == "__main__":
    main()