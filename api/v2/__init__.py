"""
API v2 模块
"""

from fastapi import APIRouter
from .endpoints import auth, trading, strategy, analysis, realtime

# 创建v2 API路由器
api_router = APIRouter()

# 注册各个端点
api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(trading.router, prefix="/trading", tags=["交易"])
api_router.include_router(strategy.router, prefix="/strategy", tags=["策略"])
api_router.include_router(analysis.router, prefix="/analysis", tags=["分析"])
api_router.include_router(realtime.router, prefix="/realtime", tags=["实时数据"])

__all__ = ["api_router"]
