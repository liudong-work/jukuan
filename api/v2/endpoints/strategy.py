"""
策略API端点 v2
"""

from fastapi import APIRouter
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/status")
async def strategy_status():
    """策略状态检查"""
    return {"status": "v2_strategy_ready"}
