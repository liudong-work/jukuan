"""
策略API端点 v1
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Form
from typing import List, Optional, Dict, Any
import logging
import sys
import os

# Add project root to Python path for module discovery
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

try:
    from services.strategy_service import strategy_service
except ImportError:
    logging.warning("无法导入策略服务，使用模拟服务")
    strategy_service = None

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/list")
async def get_strategies():
    """获取策略列表"""
    try:
        if strategy_service is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="策略服务不可用"
            )
        
        strategies = await strategy_service.get_strategies()
        return {"strategies": strategies}
        
    except Exception as e:
        logger.error(f"获取策略列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取策略列表失败"
        )

@router.get("/{strategy_id}")
async def get_strategy(strategy_id: int):
    """获取单个策略"""
    try:
        if strategy_service is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="策略服务不可用"
            )
        
        strategy = await strategy_service.get_strategy(strategy_id)
        if not strategy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="策略不存在"
            )
        
        return strategy
        
    except Exception as e:
        logger.error(f"获取策略失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取策略失败"
        )

@router.post("/create")
async def create_strategy(
    name: str = Form(..., description="策略名称"),
    strategy_type: str = Form(..., description="策略类型"),
    description: str = Form(..., description="策略描述"),
    parameters: Dict[str, Any] = Form(..., description="策略参数")
):
    """创建策略"""
    try:
        if strategy_service is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="策略服务不可用"
            )
        
        result = await strategy_service.create_strategy(
            name=name,
            strategy_type=strategy_type,
            description=description,
            parameters=parameters
        )
        
        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )
        
        return result
        
    except Exception as e:
        logger.error(f"创建策略失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="创建策略失败"
        )

@router.put("/{strategy_id}")
async def update_strategy(
    strategy_id: int,
    updates: Dict[str, Any]
):
    """更新策略"""
    try:
        if strategy_service is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="策略服务不可用"
            )
        
        result = await strategy_service.update_strategy(strategy_id, updates)
        
        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )
        
        return result
        
    except Exception as e:
        logger.error(f"更新策略失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="更新策略失败"
        )

@router.delete("/{strategy_id}")
async def delete_strategy(strategy_id: int):
    """删除策略"""
    try:
        if strategy_service is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="策略服务不可用"
            )
        
        result = await strategy_service.delete_strategy(strategy_id)
        
        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )
        
        return result
        
    except Exception as e:
        logger.error(f"删除策略失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="删除策略失败"
        )

@router.post("/{strategy_id}/backtest")
async def run_backtest(
    strategy_id: int,
    stock_code: str = Query(..., description="股票代码"),
    start_date: str = Query(..., description="开始日期"),
    end_date: str = Query(..., description="结束日期"),
    initial_capital: float = Query(default=100000.0, description="初始资金")
):
    """运行策略回测"""
    try:
        if strategy_service is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="策略服务不可用"
            )
        
        result = await strategy_service.run_backtest(
            strategy_id=strategy_id,
            stock_code=stock_code,
            start_date=start_date,
            end_date=end_date,
            initial_capital=initial_capital
        )
        
        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )
        
        return result
        
    except Exception as e:
        logger.error(f"运行回测失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="运行回测失败"
        )

@router.get("/backtest/results")
async def get_backtest_results(
    strategy_id: Optional[int] = Query(None, description="策略ID")
):
    """获取回测结果"""
    try:
        if strategy_service is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="策略服务不可用"
            )
        
        results = await strategy_service.get_backtest_results(strategy_id)
        return {"results": results}
        
    except Exception as e:
        logger.error(f"获取回测结果失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取回测结果失败"
        )

@router.post("/calculate-indicators")
async def calculate_technical_indicators(
    prices: List[float] = Query(..., description="价格列表"),
    volumes: Optional[List[float]] = Query(None, description="成交量列表")
):
    """计算技术指标"""
    try:
        if strategy_service is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="策略服务不可用"
            )
        
        indicators = await strategy_service.calculate_technical_indicators(prices, volumes)
        
        if "error" in indicators:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=indicators["error"]
            )
        
        return indicators
        
    except Exception as e:
        logger.error(f"计算技术指标失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="计算技术指标失败"
        )
