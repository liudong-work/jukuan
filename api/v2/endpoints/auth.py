"""
认证API端点 v2
"""

from fastapi import APIRouter
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/status")
async def auth_status():
    """认证状态检查"""
    return {"status": "v2_auth_ready"}
