"""
环境变量读取配置模块
用于读取数据库连接相关配置
集成maimconfig的配置管理方式
"""
import os
from typing import Optional

try:
    from .settings import settings
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False
    settings = None


class DatabaseConfig:
    """数据库配置类 - 支持maimconfig的配置方式"""

    def __init__(self):
        if PYDANTIC_AVAILABLE and settings:
            # 优先使用Pydantic设置（maimconfig方式）
            self.database_url = settings.database_url
            self.database_host = settings.database_host
            self.database_port = settings.database_port
            self.database_name = settings.database_name
            self.database_user = settings.database_user
            self.database_password = settings.database_password
        else:
            # 回退到环境变量（maim_db原有方式）
            self.database_url = os.getenv('DATABASE_URL') or os.getenv('DB_URL')
            self.database_host = os.getenv('DATABASE_HOST') or os.getenv('DB_HOST', 'localhost')
            self.database_port = int(os.getenv('DATABASE_PORT') or os.getenv('DB_PORT', '5432'))
            self.database_name = os.getenv('DATABASE_NAME') or os.getenv('DB_NAME', 'ai_saas')
            self.database_user = os.getenv('DATABASE_USER') or os.getenv('DB_USER', 'postgres')
            self.database_password = os.getenv('DATABASE_PASSWORD') or os.getenv('DB_PASSWORD', '')

    def get_host(self) -> str:
        """获取数据库主机地址"""
        return self.database_host

    def get_port(self) -> int:
        """获取数据库端口"""
        return self.database_port

    def get_name(self) -> str:
        """获取数据库名称"""
        return self.database_name

    def get_user(self) -> str:
        """获取数据库用户名"""
        return self.database_user

    def get_password(self) -> str:
        """获取数据库密码"""
        return self.database_password

    def get_database_url(self) -> str:
        """获取完整的数据库连接URL"""
        # 优先使用完整的DATABASE_URL
        if self.database_url:
            return self.database_url

        # 构建PostgreSQL连接URL
        if self._is_postgres_config():
            host = self.get_host()
            port = self.get_port()
            name = self.get_name()
            user = self.get_user()
            password = self.get_password()

            if password:
                return f"postgresql://{user}:{password}@{host}:{port}/{name}"
            else:
                return f"postgresql://{user}@{host}:{port}/{name}"

        # 如果是MySQL配置，返回MySQL URL
        elif self._is_mysql_config():
            host = self.get_host()
            port = self.get_port()
            name = self.get_name()
            user = self.get_user()
            password = self.get_password()

            if password:
                return f"mysql+pymysql://{user}:{password}@{host}:{port}/{name}"
            else:
                return f"mysql+pymysql://{user}@{host}:{port}/{name}"

        else:
            # 默认SQLite - 无需任何配置即可使用
            return "sqlite:///data/MaiBot.db"

    def get_max_connections(self) -> int:
        """获取最大连接数"""
        if PYDANTIC_AVAILABLE and settings:
            return settings.db_max_connections
        return int(os.getenv('DB_MAX_CONNECTIONS', '20'))

    def get_connection_timeout(self) -> int:
        """获取连接超时时间（秒）"""
        if PYDANTIC_AVAILABLE and settings:
            return settings.db_connection_timeout
        return int(os.getenv('DB_CONNECTION_TIMEOUT', '30'))

    def get_timezone(self) -> str:
        """获取数据库时区设置"""
        if PYDANTIC_AVAILABLE and settings:
            return settings.db_timezone
        return os.getenv('DB_TIMEZONE', 'UTC')

    def get_database_type(self) -> str:
        """获取数据库类型"""
        database_url_str = str(self.database_url) if self.database_url else ""

        if database_url_str:
            if 'mysql' in database_url_str:
                return 'mysql'
            elif 'postgresql' in database_url_str:
                return 'postgresql'
            elif 'sqlite' in database_url_str:
                return 'sqlite'

        # 根据端口判断
        if self.database_port == 3306:
            return 'mysql'
        elif self.database_port == 5432:
            return 'postgresql'
        else:
            return 'postgresql'  # 默认

    def _is_postgres_config(self) -> bool:
        """检查是否为PostgreSQL配置"""
        database_url_str = str(self.database_url) if self.database_url else ""
        return (self.database_port == 5432 or
                'postgres' in database_url_str.lower())

    def _is_mysql_config(self) -> bool:
        """检查是否为MySQL配置"""
        database_url_str = str(self.database_url) if self.database_url else ""
        return (self.database_port == 3306 or
                'mysql' in database_url_str.lower())
