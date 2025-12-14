"""
统一的 Peewee Database 实例配置
负责数据库连接管理和连接池配置
集成maimconfig的数据库连接方式
"""
import os
from playhouse.pool import PooledPostgresqlDatabase
from playhouse.pool import PooledMySQLDatabase
from peewee import SqliteDatabase

from .config import DatabaseConfig


class DatabaseManager:
    """数据库管理器 - 支持maimconfig的多种数据库"""

    def __init__(self):
        self._database = None
        self._database_config = DatabaseConfig()

    def get_database(self):
        """获取数据库实例（单例模式）"""
        if self._database is None:
            self._database = self._create_database()
        return self._database

    def _create_database(self):
        """创建数据库连接实例 - 默认SQLite，支持PostgreSQL、MySQL"""
        database_type = self._database_config.get_database_type()
        database_url = self._database_config.get_database_url()

        print(f"🔗 数据库类型: {database_type}")
        database_url_str = str(database_url) if database_url else ""

        # 安全显示连接信息
        if 'sqlite' in database_url_str:
            url_display = database_url_str
        else:
            url_display = database_url_str.split('@')[0] if '@' in database_url_str else database_url_str
            url_display += "@***"
        print(f"🔗 连接URL: {url_display}")

        try:
            if database_type == 'postgresql':
                print("🚀 尝试连接PostgreSQL数据库...")
                return self._create_postgresql_database()
            elif database_type == 'mysql':
                print("🚀 尝试连接MySQL数据库...")
                return self._create_mysql_database()
            elif database_type == 'sqlite':
                print("🚀 启动SQLite数据库...")
                return self._create_sqlite_database()
            else:
                # 默认直接使用SQLite
                print("🚀 默认启动SQLite数据库...")
                return self._create_sqlite_database()
        except Exception as e:
            print(f"❌ {database_type} 连接失败，回退到SQLite: {e}")
            print("🚀 回退启动SQLite数据库...")
            return self._create_sqlite_database()

    def _create_postgresql_database(self):
        """创建PostgreSQL数据库连接"""
        try:
            database_url = str(self._database_config.get_database_url())

            # 解析数据库URL以获取连接参数
            import urllib.parse
            parsed = urllib.parse.urlparse(database_url)

            return PooledPostgresqlDatabase(
                database=parsed.path[1:],  # 去掉开头的 '/'
                user=parsed.username,
                password=parsed.password,
                host=parsed.hostname,
                port=parsed.port,
                max_connections=self._database_config.get_max_connections(),
                stale_timeout=self._database_config.get_connection_timeout(),
                timezone=self._database_config.get_timezone()
            )
        except Exception as e:
            raise Exception(f"PostgreSQL连接创建失败: {e}")

    def _create_mysql_database(self):
        """创建MySQL数据库连接（maimconfig兼容）"""
        try:
            database_url = str(self._database_config.get_database_url())

            # 解析数据库URL以获取连接参数
            import urllib.parse
            parsed = urllib.parse.urlparse(database_url)

            return PooledMySQLDatabase(
                database=parsed.path[1:],  # 去掉开头的 '/'
                user=parsed.username,
                password=parsed.password,
                host=parsed.hostname,
                port=parsed.port,
                max_connections=self._database_config.get_max_connections(),
                stale_timeout=self._database_config.get_connection_timeout(),
                charset='utf8mb4'
            )
        except Exception as e:
            raise Exception(f"MySQL连接创建失败: {e}")

    def _create_sqlite_database(self):
        """创建SQLite数据库连接"""
        from pathlib import Path

        # 确保数据目录存在
        
        database_url = self._database_config.get_database_url()
        if database_url and 'sqlite' in str(database_url):
            # 尝试提取路径
            try:
                # remove scheme
                path_str = str(database_url).split('://')[-1]
                # If absolute path with extra slash (sqlite:////path), remove one slash if needed?
                # Usually sqlite:////absolute/path -> /absolute/path
                # But here we just get the part after ://
                # For sqlite:////home/..., it becomes //home/...
                # But Peewee SqliteDatabase takes a filename string. 
                # //home/... works as absolute path in some contexts, but let's be safe.
                if path_str.startswith('/'):
                     # Check if it was /// (relative) or //// (absolute)
                     # Standard: sqlite:///relative.db -> /relative.db? No.
                     # sqlite:///foo.db -> foo.db
                     # sqlite:////abs/path/foo.db -> /abs/path/foo.db
                     pass
                
                # Simplified parsing:
                # Allow the user to specify full path. 
                # If we use SQLAlchemy format: sqlite+aiosqlite:////path/to/db
                if ':///' in str(database_url):
                     db_path = str(database_url).split(':///')[-1]
                elif '://' in str(database_url):
                     db_path = str(database_url).split('://')[-1]
                else:
                     db_path = str(database_url)

                # Fix for 'sqlite+aiosqlite:////home' -> '/home'
                # If split result starts with /, keep it.
            except:
                db_path = "MainBot.db" # Fallback
        else:
            data_dir = Path(__file__).parent.parent.parent / "data"
            data_dir.mkdir(exist_ok=True)
            db_path = data_dir / "MaiBot.db"
            
        print(f"🚀 SQLite DB Path: {db_path}")

        return SqliteDatabase(
            db_path,
            pragmas={
                "journal_mode": "wal",        # WAL模式提高并发性能
                "cache_size": -64 * 1000,    # 64MB缓存
                "foreign_keys": 1,           # 启用外键约束
                "ignore_check_constraints": 0,
                "synchronous": 0,            # 异步写入提高性能
                "busy_timeout": 1000,        # 1秒超时
            },
        )

    def connect(self):
        """连接数据库"""
        db = self.get_database()
        if not db.is_connection_usable():
            db.connect()

    def close(self):
        """关闭数据库连接"""
        db = self.get_database()
        if db.is_connection_usable():
            db.close()

    def create_tables(self, models):
        """创建表"""
        db = self.get_database()
        db.create_tables(models, safe=True)

    def drop_tables(self, models):
        """删除表"""
        db = self.get_database()
        db.drop_tables(models, safe=True, cascade=True)


# 全局数据库管理器实例
db_manager = DatabaseManager()

# 导出数据库实例供模型使用
database = db_manager.get_database()


def get_database():
    """获取数据库实例的便捷函数"""
    return database


def init_database():
    """初始化数据库连接"""
    db_manager.connect()


def close_database():
    """关闭数据库连接"""
    db_manager.close()
