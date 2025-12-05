"""
应用配置管理 - 集成maimconfig的配置方式
支持配置和环境变量
"""

import os


class Settings:
    """应用配置 - 兼容maimconfig的配置格式"""

    def __init__(self):
        # 数据库配置 - 默认SQLite，兼容maimconfig
        self.database_url = os.getenv(
            'DATABASE_URL',
            "sqlite:///data/MaiBot.db"
        )
        self.database_host = os.getenv('DATABASE_HOST', "localhost")
        self.database_port = int(os.getenv('DATABASE_PORT', "3306"))
        self.database_name = os.getenv('DATABASE_NAME', "maimbot_api")
        self.database_user = os.getenv('DATABASE_USER', "username")
        self.database_password = os.getenv('DATABASE_PASSWORD', "password")

        # 服务器配置
        self.host = os.getenv('HOST', "0.0.0.0")
        self.port = int(os.getenv('PORT', "8000"))
        self.debug = os.getenv('DEBUG', "False").lower() == "true"

        # 日志配置
        self.log_level = os.getenv('LOG_LEVEL', "INFO")

        # API配置
        self.api_v1_prefix = os.getenv('API_V1_PREFIX', "/api/v1")
        self.api_v2_prefix = os.getenv('API_V2_PREFIX', "/api/v2")

        # 安全配置
        self.secret_key = os.getenv('SECRET_KEY', "your-secret-key-here")
        self.algorithm = os.getenv('ALGORITHM', "HS256")
        self.access_token_expire_minutes = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', "30"))

        # 应用配置
        self.app_name = os.getenv('APP_NAME', "MaiMBot API")
        self.app_version = os.getenv('APP_VERSION', "1.0.0")

        # 数据库连接配置
        self.db_max_connections = int(os.getenv('DB_MAX_CONNECTIONS', "20"))
        self.db_connection_timeout = int(os.getenv('DB_CONNECTION_TIMEOUT', "30"))
        self.db_timezone = os.getenv('DB_TIMEZONE', "UTC")


# 创建全局配置实例
settings = Settings()