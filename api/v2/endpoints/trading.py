"""
交易API端点 v2
"""

from fastapi import APIRouter
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/status")
async def trading_status():
    """交易状态检查"""
    return {"status": "v2_trading_ready"}
