"""
数据库连接管理
支持PostgreSQL和Redis
"""

import asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from redis import asyncio as aioredis
import logging

from core.config import settings

logger = logging.getLogger(__name__)

# 创建异步数据库引擎
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_recycle=300,
)

# 创建异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# 创建Redis连接池
redis_pool = None

async def init_db():
    """初始化数据库"""
    try:
        # 初始化Redis连接池
        global redis_pool
        redis_pool = aioredis.ConnectionPool.from_url(
            settings.REDIS_URL,
            max_connections=20,
            decode_responses=True
        )
        
        # 测试数据库连接
        async with engine.begin() as conn:
            await conn.run_sync(lambda sync_conn: None)
        
        logger.info("✅ 数据库连接初始化成功")
        
    except Exception as e:
        logger.error(f"❌ 数据库连接初始化失败: {e}")
        raise

async def get_db() -> AsyncGenerator[AsyncSession, None]:
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

async def get_redis():
    """获取Redis连接"""
    if redis_pool is None:
        raise RuntimeError("Redis连接池未初始化")
    
    redis = aioredis.Redis(connection_pool=redis_pool)
    try:
        yield redis
    finally:
        await redis.close()

async def close_db():
    """关闭数据库连接"""
    await engine.dispose()
    if redis_pool:
        await redis_pool.disconnect()
    logger.info("数据库连接已关闭")

# 导出
__all__ = ["init_db", "get_db", "get_redis", "close_db", "AsyncSessionLocal"]
