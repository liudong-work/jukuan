"""
策略执行状态API端点 v1
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Form
from typing import List, Optional, Dict, Any
import logging
import sys
import os

# Add project root to Python path for module discovery
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

try:
    from services.strategy_executor import strategy_executor
except ImportError:
    logging.warning("无法导入策略执行引擎，使用模拟服务")
    strategy_executor = None

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/execution-status")
async def get_execution_status():
    """获取策略执行状态"""
    try:
        if strategy_executor is None:
            # 返回模拟数据
            return {
                "queue_size": 0,
                "active_strategies": 0,
                "execution_history_count": 0,
                "last_execution": None,
                "status": "service_unavailable"
            }
        
        status = await strategy_executor.get_execution_status()
        return status
        
    except Exception as e:
        logger.error(f"获取执行状态失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取执行状态失败"
        )

@router.post("/add-signal")
async def add_signal(
    stock_code: str = Form(..., description="股票代码"),
    action: str = Form(..., description="交易动作"),
    quantity: int = Form(..., description="数量"),
    price: Optional[float] = Form(None, description="价格"),
    confidence: float = Form(..., description="置信度")
):
    """添加策略信号"""
    try:
        if strategy_executor is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="策略执行引擎不可用"
            )
        
        signal = {
            "stock_code": stock_code,
            "action": action,
            "quantity": quantity,
            "price": price,
            "confidence": confidence
        }
        
        result = await strategy_executor.add_signal(signal)
        return {"message": "信号添加成功", "signal": signal}
        
    except Exception as e:
        logger.error(f"添加信号失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="添加信号失败"
        )

@router.post("/start-strategy/{strategy_id}")
async def start_strategy(strategy_id: str):
    """启动策略"""
    try:
        if strategy_executor is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="策略执行引擎不可用"
            )
        
        result = await strategy_executor.start_strategy(strategy_id)
        return {"message": "策略启动成功", "strategy_id": strategy_id}
        
    except Exception as e:
        logger.error(f"启动策略失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="启动策略失败"
        )

@router.post("/stop-strategy/{strategy_id}")
async def stop_strategy(strategy_id: str):
    """停止策略"""
    try:
        if strategy_executor is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="策略执行引擎不可用"
            )
        
        result = await strategy_executor.stop_strategy(strategy_id)
        return {"message": "策略停止成功", "strategy_id": strategy_id}
        
    except Exception as e:
        logger.error(f"停止策略失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="停止策略失败"
        )

@router.get("/execution-history")
async def get_execution_history():
    """获取执行历史"""
    try:
        if strategy_executor is None:
            # 返回模拟数据
            return {
                "executions": [],
                "total_count": 0,
                "status": "service_unavailable"
            }
        
        # 这里应该调用策略执行引擎的方法获取执行历史
        # 暂时返回模拟数据
        return {
            "executions": [],
            "total_count": 0,
            "status": "available"
        }
        
    except Exception as e:
        logger.error(f"获取执行历史失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取执行历史失败"
        )
