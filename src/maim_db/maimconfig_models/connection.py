"""
数据库连接管理
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from src.common.config import settings
from src.common.logger import get_logger

logger = get_logger(__name__)

# 创建异步引擎
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_size=20,
    max_overflow=0,
    pool_pre_ping=True,
    pool_recycle=3600,
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


async def init_database() -> None:
    """初始化数据库连接"""
    try:
        # 测试数据库连接
        async with engine.begin() as conn:
            await conn.execute("SELECT 1")
        logger.info("数据库连接测试成功")
    except Exception as e:
        logger.error(f"数据库连接失败: {e}")
        raise