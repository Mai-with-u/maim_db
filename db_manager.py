#!/usr/bin/env python3
"""
MaiMBot 统一数据库管理器
支持PostgreSQL和SQLite数据库的统一管理、启动、迁移和维护
"""

import os
import sys
import argparse
import subprocess
import json
import time
import logging
from pathlib import Path
from typing import Optional, Dict, Any

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.core import ALL_MODELS, init_database, close_database
from src.core.config import DatabaseConfig

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DatabaseManager:
    """统一数据库管理器"""

    def __init__(self):
        self.config_dir = Path(__file__).parent / "config"
        self.data_dir = Path(__file__).parent / "data"
        self.scripts_dir = Path(__file__).parent / "scripts"

        # 确保目录存在
        self.config_dir.mkdir(exist_ok=True)
        self.data_dir.mkdir(exist_ok=True)
        self.scripts_dir.mkdir(exist_ok=True)

        # Docker配置
        self.docker_compose_file = self.config_dir / "docker-compose.yml"
        self.postgres_config_file = self.config_dir / "postgres.json"

    def get_database_mode(self) -> str:
        """获取当前数据库模式"""
        # 检查环境变量
        if os.getenv('DB_HOST'):
            return "postgres"

        # 检查PostgreSQL容器是否运行
        if self.is_postgres_running():
            return "postgres"

        return "sqlite"

    def is_postgres_running(self) -> bool:
        """检查PostgreSQL容器是否运行"""
        try:
            result = subprocess.run(
                ["docker", "ps", "--filter", "name=maimbot-postgres", "--format", "{{.Names}}"],
                capture_output=True, text=True, timeout=10
            )
            return "maimbot-postgres" in result.stdout.strip()
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def create_postgres_config(self, **kwargs) -> Dict[str, Any]:
        """创建PostgreSQL配置"""
        default_config = {
            "postgres_version": "15",
            "container_name": "maimbot-postgres",
            "port": "5432",
            "database": "ai_saas",
            "user": "postgres",
            "password": "maimbot_2024",
            "data_volume": "maimbot_postgres_data",
            "host": "localhost",
            "max_connections": "100",
            "shared_buffers": "256MB",
            "effective_cache_size": "1GB"
        }

        # 更新配置
        default_config.update(kwargs)

        # 保存配置文件
        with open(self.postgres_config_file, 'w') as f:
            json.dump(default_config, f, indent=2, ensure_ascii=False)

        return default_config

    def create_docker_compose(self, config: Dict[str, Any]):
        """创建Docker Compose配置"""
        compose_content = f"""version: '3.8'

services:
  postgres:
    image: postgres:{config['postgres_version']}
    container_name: {config['container_name']}
    restart: unless-stopped
    environment:
      POSTGRES_DB: {config['database']}
      POSTGRES_USER: {config['user']}
      POSTGRES_PASSWORD: {config['password']}
      POSTGRES_INITDB_ARGS: "--encoding=UTF-8 --lc-collate=C --lc-ctype=C"
    volumes:
      - {config['data_volume']}:/var/lib/postgresql/data
      - ./scripts/init-postgres.sql:/docker-entrypoint-initdb.d/init-postgres.sql
    ports:
      - "{config['port']}:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U {config['user']} -d {config['database']}"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
    command: >
      postgres
      -c max_connections={config['max_connections']}
      -c shared_buffers={config['shared_buffers']}
      -c effective_cache_size={config['effective_cache_size']}
      -c maintenance_work_mem=64MB
      -c checkpoint_completion_target=0.9
      -c wal_buffers=16MB
      -c default_statistics_target=100

volumes:
  {config['data_volume']}:
    driver: local
"""

        with open(self.docker_compose_file, 'w') as f:
            f.write(compose_content)

    def create_init_script(self, config: Dict[str, Any]):
        """创建PostgreSQL初始化脚本"""
        init_script = f"""-- PostgreSQL初始化脚本
-- 为MaiMBot创建数据库和配置

-- 创建扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- 设置时区
SET timezone = 'UTC';

-- 创建索引优化配置
-- 这些将在表创建后由应用程序处理

-- 输出初始化完成信息
DO $$
BEGIN
    RAISE NOTICE '数据库 % 初始化完成', '{config['database']}';
END $$;
"""

        init_script_file = self.scripts_dir / "init-postgres.sql"
        with open(init_script_file, 'w') as f:
            f.write(init_script)

    def start_postgres(self, force_recreate: bool = False, **config_overrides):
        """启动PostgreSQL数据库"""
        logger.info("启动PostgreSQL数据库...")

        # 创建配置
        config = self.create_postgres_config(**config_overrides)

        # 创建配置文件
        self.create_docker_compose(config)
        self.create_init_script(config)

        # 设置环境变量
        os.environ.update({
            'DB_HOST': config['host'],
            'DB_PORT': config['port'],
            'DB_NAME': config['database'],
            'DB_USER': config['user'],
            'DB_PASSWORD': config['password']
        })

        try:
            cmd = ["docker-compose", "-f", str(self.docker_compose_file), "up", "-d"]
            if force_recreate:
                cmd.append("--force-recreate")

            logger.info(f"执行命令: {' '.join(cmd)}")
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            logger.info("PostgreSQL容器启动中...")

            # 等待数据库就绪
            self.wait_for_postgres_ready(config)

            logger.info("✅ PostgreSQL数据库启动成功")
            logger.info(f"连接信息: {config['user']}@{config['host']}:{config['port']}/{config['database']}")

            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"❌ PostgreSQL启动失败: {e}")
            logger.error(f"错误输出: {e.stderr}")
            return False
        except FileNotFoundError:
            logger.error("❌ Docker或docker-compose未安装")
            return False

    def wait_for_postgres_ready(self, config: Dict[str, Any], timeout: int = 120):
        """等待PostgreSQL数据库就绪"""
        logger.info("等待数据库就绪...")
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                # 使用docker exec检查数据库状态
                cmd = [
                    "docker", "exec", config['container_name'],
                    "psql", "-U", config['user'], "-d", config['database'],
                    "-c", "SELECT 1"
                ]
                result = subprocess.run(cmd, capture_output=True, timeout=10)
                if result.returncode == 0:
                    logger.info("✅ 数据库已就绪")
                    return True

            except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
                pass

            time.sleep(2)

        raise TimeoutError("数据库启动超时")

    def stop_postgres(self):
        """停止PostgreSQL数据库"""
        logger.info("停止PostgreSQL数据库...")

        if not self.docker_compose_file.exists():
            logger.warning("Docker Compose配置文件不存在")
            return False

        try:
            subprocess.run(
                ["docker-compose", "-f", str(self.docker_compose_file), "down"],
                check=True, capture_output=True
            )
            logger.info("✅ PostgreSQL数据库已停止")

            # 清除环境变量
            for key in ['DB_HOST', 'DB_PORT', 'DB_NAME', 'DB_USER', 'DB_PASSWORD']:
                os.environ.pop(key, None)

            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"❌ PostgreSQL停止失败: {e}")
            return False
        except FileNotFoundError:
            logger.error("❌ Docker或docker-compose未安装")
            return False

    def reset_postgres(self, **config_overrides):
        """重置PostgreSQL数据库（删除所有数据）"""
        logger.warning("⚠️ 重置PostgreSQL数据库将删除所有数据！")

        # 停止现有容器
        if self.is_postgres_running():
            self.stop_postgres()

        # 删除数据卷
        try:
            config = self.create_postgres_config(**config_overrides)
            subprocess.run(
                ["docker", "volume", "rm", config['data_volume']],
                check=True, capture_output=True
            )
            logger.info("✅ 数据卷已删除")
        except subprocess.CalledProcessError as e:
            logger.warning(f"删除数据卷失败: {e}")

        # 重新启动
        return self.start_postgres(force_recreate=True, **config_overrides)

    def init_database_tables(self):
        """初始化数据库表结构"""
        logger.info("初始化数据库表结构...")

        try:
            # 初始化数据库连接
            init_database()

            # 创建所有表
            from src.core.database import db_manager
            db_manager.create_tables(ALL_MODELS)

            logger.info("✅ 数据库表结构初始化完成")
            return True

        except Exception as e:
            logger.error(f"❌ 数据库表初始化失败: {e}")
            return False

    def get_database_info(self):
        """获取数据库信息"""
        mode = self.get_database_mode()
        info = {
            "mode": mode,
            "status": "运行中" if self.is_database_running() else "未运行"
        }

        if mode == "postgres":
            config = self.create_postgres_config()
            info.update({
                "type": "PostgreSQL",
                "version": config.get("postgres_version"),
                "host": config.get("host"),
                "port": config.get("port"),
                "database": config.get("database"),
                "user": config.get("user"),
                "container_name": config.get("container_name"),
                "container_running": self.is_postgres_running()
            })
        else:
            sqlite_path = self.data_dir / "MaiBot.db"
            info.update({
                "type": "SQLite",
                "path": str(sqlite_path),
                "exists": sqlite_path.exists(),
                "size": f"{sqlite_path.stat().st_size / 1024:.1f} KB" if sqlite_path.exists() else "0 KB"
            })

        return info

    def is_database_running(self):
        """检查数据库是否运行"""
        mode = self.get_database_mode()
        if mode == "postgres":
            return self.is_postgres_running()
        else:
            # SQLite总是可用的
            return True

    def backup_database(self, backup_path: Optional[str] = None):
        """备份数据库"""
        if not backup_path:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            backup_path = self.data_dir / f"backup_{timestamp}"

        backup_path = Path(backup_path)
        backup_path.mkdir(parents=True, exist_ok=True)

        mode = self.get_database_mode()

        if mode == "postgres":
            return self._backup_postgres(backup_path)
        else:
            return self._backup_sqlite(backup_path)

    def _backup_postgres(self, backup_path: Path):
        """备份PostgreSQL数据库"""
        logger.info("备份PostgreSQL数据库...")

        try:
            config = self.create_postgres_config()
            backup_file = backup_path / f"{config['database']}_backup.sql"

            cmd = [
                "docker", "exec", config['container_name'],
                "pg_dump", "-U", config['user'], config['database']
            ]

            with open(backup_file, 'w') as f:
                subprocess.run(cmd, check=True, stdout=f)

            logger.info(f"✅ PostgreSQL备份完成: {backup_file}")
            return backup_file

        except Exception as e:
            logger.error(f"❌ PostgreSQL备份失败: {e}")
            return None

    def _backup_sqlite(self, backup_path: Path):
        """备份SQLite数据库"""
        logger.info("备份SQLite数据库...")

        try:
            sqlite_file = self.data_dir / "MaiBot.db"
            backup_file = backup_path / "MaiBot.db"

            if sqlite_file.exists():
                import shutil
                shutil.copy2(sqlite_file, backup_file)
                logger.info(f"✅ SQLite备份完成: {backup_file}")
                return backup_file
            else:
                logger.warning("SQLite数据库文件不存在")
                return None

        except Exception as e:
            logger.error(f"❌ SQLite备份失败: {e}")
            return None

    def restore_database(self, backup_file: str):
        """恢复数据库"""
        backup_file = Path(backup_file)
        if not backup_file.exists():
            logger.error(f"备份文件不存在: {backup_file}")
            return False

        mode = self.get_database_mode()

        if mode == "postgres" and backup_file.suffix == '.sql':
            return self._restore_postgres(backup_file)
        elif backup_file.name == "MaiBot.db":
            return self._restore_sqlite(backup_file)
        else:
            logger.error("备份文件类型不匹配当前数据库模式")
            return False

    def _restore_postgres(self, backup_file: Path):
        """恢复PostgreSQL数据库"""
        logger.info("恢复PostgreSQL数据库...")

        try:
            config = self.create_postgres_config()

            cmd = [
                "docker", "exec", "-i", config['container_name'],
                "psql", "-U", config['user'], config['database']
            ]

            with open(backup_file, 'r') as f:
                subprocess.run(cmd, check=True, stdin=f)

            logger.info("✅ PostgreSQL恢复完成")
            return True

        except Exception as e:
            logger.error(f"❌ PostgreSQL恢复失败: {e}")
            return False

    def _restore_sqlite(self, backup_file: Path):
        """恢复SQLite数据库"""
        logger.info("恢复SQLite数据库...")

        try:
            sqlite_file = self.data_dir / "MaiBot.db"
            import shutil
            shutil.copy2(backup_file, sqlite_file)

            logger.info("✅ SQLite恢复完成")
            return True

        except Exception as e:
            logger.error(f"❌ SQLite恢复失败: {e}")
            return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="MaiMBot统一数据库管理器")
    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    # 状态命令
    subparsers.add_parser('status', help='显示数据库状态')

    # 启动命令
    start_parser = subparsers.add_parser('start', help='启动数据库')
    start_parser.add_argument('--force', action='store_true', help='强制重新创建容器')
    start_parser.add_argument('--port', type=str, default='5432', help='PostgreSQL端口')
    start_parser.add_argument('--password', type=str, help='PostgreSQL密码')

    # 停止命令
    subparsers.add_parser('stop', help='停止数据库')

    # 重置命令
    reset_parser = subparsers.add_parser('reset', help='重置数据库')
    reset_parser.add_argument('--confirm', action='store_true', help='确认重置')

    # 初始化命令
    subparsers.add_parser('init', help='初始化数据库表')

    # 备份命令
    backup_parser = subparsers.add_parser('backup', help='备份数据库')
    backup_parser.add_argument('--path', type=str, help='备份路径')

    # 恢复命令
    restore_parser = subparsers.add_parser('restore', help='恢复数据库')
    restore_parser.add_argument('file', help='备份文件路径')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    db_manager = DatabaseManager()

    # 执行命令
    if args.command == 'status':
        info = db_manager.get_database_info()
        print(json.dumps(info, indent=2, ensure_ascii=False))

    elif args.command == 'start':
        kwargs = {}
        if args.port:
            kwargs['port'] = args.port
        if args.password:
            kwargs['password'] = args.password

        db_manager.start_postgres(force_recreate=args.force, **kwargs)

    elif args.command == 'stop':
        db_manager.stop_postgres()

    elif args.command == 'reset':
        if not args.confirm:
            print("请使用 --confirm 确认重置操作")
            return
        db_manager.reset_postgres()

    elif args.command == 'init':
        db_manager.init_database_tables()

    elif args.command == 'backup':
        backup_file = db_manager.backup_database(args.path)
        if backup_file:
            print(f"备份完成: {backup_file}")

    elif args.command == 'restore':
        success = db_manager.restore_database(args.file)
        if success:
            print("恢复完成")


if __name__ == "__main__":
    main()