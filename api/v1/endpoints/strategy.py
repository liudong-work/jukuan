"""
策略API端点 v1
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Form
from typing import List, Optional, Dict, Any
import logging
import sys
import os
from datetime import datetime

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

@router.get("/status")
async def get_strategy_system_status():
    """获取策略系统状态"""
    try:
        if strategy_service is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="策略服务不可用"
            )
        
        # 获取策略统计信息
        strategies = await strategy_service.get_strategies()
        combinations = await strategy_service.get_strategy_combinations()
        
        # 计算状态分布
        status_distribution = {}
        type_distribution = {}
        
        for strategy in strategies:
            # 状态分布
            status = strategy.get('status', 'unknown')
            status_distribution[status] = status_distribution.get(status, 0) + 1
            
            # 类型分布
            strategy_type = strategy.get('type', 'unknown')
            type_distribution[strategy_type] = type_distribution.get(strategy_type, 0) + 1
        
        return {
            "total_strategies": len(strategies),
            "total_combinations": len(combinations),
            "service_status": "running",
            "status_distribution": status_distribution,
            "type_distribution": type_distribution,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"获取策略系统状态失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取策略系统状态失败"
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
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
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
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
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
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除策略失败"
        )

@router.post("/{strategy_id}/backtest")
async def run_backtest(
    strategy_id: int,
    stock_code: str = Form(..., description="股票代码"),
    start_date: str = Form(..., description="开始日期"),
    end_date: str = Form(..., description="结束日期"),
    initial_capital: float = Form(100000.0, description="初始资金")
):
    """运行策略回测"""
    try:
        if strategy_service is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="策略服务不可用"
            )
        
        result = await strategy_service.run_backtest(
            strategy_id, stock_code, start_date, end_date, initial_capital
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
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="运行回测失败"
        )

@router.get("/{strategy_id}/backtest-results")
async def get_backtest_results(strategy_id: int):
    """获取策略回测结果"""
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

@router.post("/{strategy_id}/validate")
async def validate_strategy(
    strategy_id: int,
    parameters: Dict[str, Any]
):
    """验证策略参数"""
    try:
        if strategy_service is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="策略服务不可用"
            )
        
        # 获取策略类型
        strategy = await strategy_service.get_strategy(strategy_id)
        if not strategy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="策略不存在"
            )
        
        validation = await strategy_service.validate_strategy(
            strategy["type"], parameters
        )
        
        return validation
        
    except Exception as e:
        logger.error(f"验证策略失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="验证策略失败"
        )

@router.post("/{strategy_id}/optimize")
async def optimize_strategy(
    strategy_id: int,
    optimization_params: Dict[str, Any]
):
    """优化策略参数"""
    try:
        if strategy_service is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="策略服务不可用"
            )
        
        result = await strategy_service.optimize_strategy(strategy_id, optimization_params)
        
        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )
        
        return result
        
    except Exception as e:
        logger.error(f"优化策略失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="优化策略失败"
        )

@router.get("/{strategy_id}/performance")
async def get_strategy_performance(strategy_id: int):
    """获取策略性能指标"""
    try:
        if strategy_service is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="策略服务不可用"
            )
        
        performance = await strategy_service.get_strategy_performance(strategy_id)
        if not performance:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="策略性能数据不存在"
            )
        
        return performance
        
    except Exception as e:
        logger.error(f"获取策略性能失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取策略性能失败"
        )

@router.post("/combinations/create")
async def create_strategy_combination(
    name: str = Form(..., description="组合名称"),
    strategy_ids: str = Form(..., description="策略ID列表(JSON字符串)"),
    allocation: str = Form(..., description="分配比例列表(JSON字符串)")
):
    """创建策略组合"""
    try:
        if strategy_service is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="策略服务不可用"
            )
        
        # 解析JSON字符串
        try:
            strategy_ids_list = json.loads(strategy_ids)
            allocation_list = json.loads(allocation)
        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"参数格式错误: {e}"
            )
        
        result = await strategy_service.create_strategy_combination(
            name, strategy_ids_list, allocation_list
        )
        
        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )
        
        return result
        
    except Exception as e:
        logger.error(f"创建策略组合失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建策略组合失败"
        )

@router.get("/combinations/list")
async def get_strategy_combinations():
    """获取策略组合列表"""
    try:
        if strategy_service is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="策略服务不可用"
            )
        
        combinations = await strategy_service.get_strategy_combinations()
        return {"combinations": combinations}
        
    except Exception as e:
        logger.error(f"获取策略组合失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取策略组合失败"
        )

@router.post("/combinations/{combination_id}/backtest")
async def run_combination_backtest(
    combination_id: int,
    stock_codes: List[str] = Form(..., description="股票代码列表"),
    start_date: str = Form(..., description="开始日期"),
    end_date: str = Form(..., description="结束日期"),
    initial_capital: float = Form(100000.0, description="初始资金")
):
    """运行策略组合回测"""
    try:
        if strategy_service is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="策略服务不可用"
            )
        
        result = await strategy_service.run_combination_backtest(
            combination_id, stock_codes, start_date, end_date, initial_capital
        )
        
        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )
        
        return result
        
    except Exception as e:
        logger.error(f"运行组合回测失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="运行组合回测失败"
        )

@router.post("/calculate-indicators")
async def calculate_technical_indicators(
    prices: List[float] = Form(..., description="价格列表"),
    volumes: Optional[List[float]] = Form(None, description="成交量列表")
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
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="计算技术指标失败"
        )

@router.get("/types")
async def get_strategy_types():
    """获取支持的策略类型"""
    try:
        from services.strategy_service import StrategyType
        
        types = [{"value": t.value, "name": t.name, "description": t.__doc__} 
                for t in StrategyType]
        
        return {"strategy_types": types}
        
    except Exception as e:
        logger.error(f"获取策略类型失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取策略类型失败"
        )
