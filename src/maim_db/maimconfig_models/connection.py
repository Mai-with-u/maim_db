"""
数据库连接管理
"""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from maim_db.core.settings import settings
import logging

logger = logging.getLogger(__name__)

# 创建异步引擎
# 创建异步引擎
# 创建异步引擎
engine_args = {
    "echo": settings.debug,
}

if "sqlite" not in settings.database_url:
    engine_args.update({
        "pool_size": 20,
        "max_overflow": 0,
        "pool_pre_ping": True,
        "pool_recycle": 3600,
    })

# SQLAlchemy 2.0+ / aiosqlite special handling: ensure no pool args for sqlite if implied NullPool
# logic above handles it by only adding them if NOT sqlite.
# effectively engine_args only has 'echo' for sqlite.

engine = create_async_engine(
    settings.database_url,
    **engine_args
)

# 创建异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """数据库模型基类"""
    pass


async def get_db() -> AsyncSession:
    """获取数据库会话"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            logger.error(f"数据库会话错误: {e}")
            raise
        finally:
            await session.close()



# 启用 WAL 模式 (对于 SQLite)
if "sqlite" in settings.database_url:
    from sqlalchemy import event
    
    @event.listens_for(engine.sync_engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=DELETE")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.close()


async def init_database() -> None:
    """初始化数据库连接"""
    try:
        # 测试数据库连接
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("数据库连接测试成功")
    except Exception as e:
        logger.error(f"数据库连接失败: {e}")
        raise