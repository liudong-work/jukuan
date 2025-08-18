"""
交易API端点 v1
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
import logging
import sys
import os

# Add project root to Python path for module discovery
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

try:
    from services.trading_service import trading_service
except ImportError:
    logging.warning("无法导入交易服务，使用模拟服务")
    trading_service = None

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/portfolio")
async def get_portfolio(user_id: int = Query(default=1, description="用户ID")):
    """获取投资组合"""
    try:
        if trading_service is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="交易服务不可用"
            )
        
        portfolio = await trading_service.get_portfolio(user_id)
        
        if "error" in portfolio:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=portfolio["error"]
            )
        
        return portfolio
        
    except Exception as e:
        logger.error(f"获取投资组合失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取投资组合失败"
        )

@router.get("/positions")
async def get_positions(user_id: int = Query(default=1, description="用户ID")):
    """获取持仓信息"""
    try:
        if trading_service is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="交易服务不可用"
            )
        
        positions = await trading_service.get_positions(user_id)
        return {"positions": positions}
        
    except Exception as e:
        logger.error(f"获取持仓失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取持仓失败"
        )

@router.get("/orders")
async def get_orders(
    user_id: int = Query(default=1, description="用户ID"),
    status: Optional[str] = Query(default=None, description="订单状态")
):
    """获取订单列表"""
    try:
        if trading_service is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="交易服务不可用"
            )
        
        orders = await trading_service.get_orders(user_id, status)
        return {"orders": orders}
        
    except Exception as e:
        logger.error(f"获取订单失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取订单失败"
        )

@router.post("/order")
async def place_order(
    stock_code: str = Query(..., description="股票代码"),
    order_type: str = Query(..., description="订单类型: market(市价单), limit(限价单)"),
    quantity: int = Query(..., description="数量"),
    price: Optional[float] = Query(None, description="价格(限价单必填)"),
    order_side: str = Query(default="buy", description="买卖方向: buy(买入), sell(卖出)"),
    user_id: int = Query(default=1, description="用户ID")
):
    """下单"""
    try:
        if trading_service is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="交易服务不可用"
            )
        
        result = await trading_service.place_order(
            user_id=user_id,
            stock_code=stock_code,
            order_type=order_type,
            quantity=quantity,
            price=price,
            order_side=order_side
        )
        
        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )
        
        return result
        
    except Exception as e:
        logger.error(f"下单失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="下单失败"
        )

@router.post("/cancel-order")
async def cancel_order(
    order_id: str = Query(..., description="订单ID"),
    user_id: int = Query(default=1, description="用户ID")
):
    """取消订单"""
    try:
        if trading_service is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="交易服务不可用"
            )
        
        result = await trading_service.cancel_order(user_id, order_id)
        
        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )
        
        return result
        
    except Exception as e:
        logger.error(f"取消订单失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="取消订单失败"
        )
