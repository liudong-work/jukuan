"""
API v1 模块
"""

from fastapi import APIRouter
from .endpoints import auth, trading, strategy, analysis, jq_data, ml_strategy, robo_advisor, strategy_executor, smart_assistant

# 创建v1 API路由器
api_router = APIRouter()

# 注册各个端点
api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(trading.router, prefix="/trading", tags=["交易"])
api_router.include_router(strategy.router, prefix="/strategy", tags=["策略"])
api_router.include_router(analysis.router, prefix="/analysis", tags=["分析"])
api_router.include_router(jq_data.router, prefix="/jq", tags=["聚宽数据"])
api_router.include_router(ml_strategy.router, prefix="/ml-strategy", tags=["机器学习策略"])
api_router.include_router(robo_advisor.router, prefix="/robo-advisor", tags=["智能投顾"])
api_router.include_router(strategy_executor.router, prefix="/strategy-executor", tags=["策略执行"])
api_router.include_router(smart_assistant.router, prefix="/smart-assistant", tags=["智能交易助手"])

__all__ = ["api_router"]
