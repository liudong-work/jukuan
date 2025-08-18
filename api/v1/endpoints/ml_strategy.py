"""
机器学习策略API端点 v1
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Form
from typing import List, Optional, Dict, Any
import logging
import sys
import os

# Add project root to Python path for module discovery
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

try:
    from services.ml_strategy_service import ml_strategy_service
except ImportError:
    logging.warning("无法导入机器学习策略服务，使用模拟服务")
    ml_strategy_service = None

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/strategies")
async def get_ml_strategies():
    """获取机器学习策略列表"""
    try:
        if ml_strategy_service is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="机器学习策略服务不可用"
            )
        
        strategies = await ml_strategy_service.get_strategies()
        return {"strategies": strategies}
        
    except Exception as e:
        logger.error(f"获取机器学习策略列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取机器学习策略列表失败"
        )

@router.get("/strategies/{strategy_id}")
async def get_ml_strategy(strategy_id: str):
    """获取单个机器学习策略"""
    try:
        if ml_strategy_service is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="机器学习策略服务不可用"
            )
        
        strategy = await ml_strategy_service.get_strategy(strategy_id)
        if not strategy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="策略不存在"
            )
        
        return strategy
        
    except Exception as e:
        logger.error(f"获取机器学习策略失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取机器学习策略失败"
        )

@router.post("/create-feature-set")
async def create_feature_set(
    name: str = Form(..., description="特征集名称"),
    description: str = Form(..., description="特征集描述"),
    calculation_method: str = Form(..., description="计算方法"),
    features: List[str] = Form(..., description="特征列表")
):
    """创建特征集"""
    try:
        if ml_strategy_service is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="机器学习策略服务不可用"
            )
        
        result = await ml_strategy_service.create_feature_set(
            name=name,
            description=description,
            calculation_method=calculation_method,
            features=features
        )
        
        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )
        
        return result
        
    except Exception as e:
        logger.error(f"创建特征集失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建特征集失败"
        )

@router.post("/train-model")
async def train_model(
    strategy_name: str = Form(..., description="策略名称"),
    model_type: str = Form(..., description="模型类型"),
    features: List[str] = Form(..., description="特征列表"),
    target_column: str = Form(..., description="目标列"),
    stock_code: str = Form(..., description="股票代码"),
    start_date: str = Form(..., description="开始日期"),
    end_date: str = Form(..., description="结束日期")
):
    """训练模型"""
    try:
        if ml_strategy_service is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="机器学习策略服务不可用"
            )
        
        # 计算特征
        features_df = await ml_strategy_service.calculate_features(
            stock_code=stock_code,
            start_date=start_date,
            end_date=end_date,
            feature_set="technical_indicators"
        )
        
        if features_df.empty:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="无法获取特征数据"
            )
        
        # 创建目标变量
        features_with_target = await ml_strategy_service.create_target_variable(
            features_df, method="future_return"
        )
        
        # 训练模型
        result = await ml_strategy_service.train_model(
            strategy_name=strategy_name,
            model_type=model_type,
            features=features,
            target_column=target_column,
            training_data=features_with_target
        )
        
        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )
        
        return result
        
    except Exception as e:
        logger.error(f"训练模型失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="训练模型失败"
        )

@router.post("/predict")
async def predict_signal(
    strategy_id: str = Form(..., description="策略ID"),
    stock_code: str = Form(..., description="股票代码")
):
    """预测交易信号"""
    try:
        if ml_strategy_service is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="机器学习策略服务不可用"
            )
        
        # 获取当前数据
        features_df = await ml_strategy_service.calculate_features(
            stock_code=stock_code,
            start_date="2024-12-01",
            end_date="2024-12-31",
            feature_set="technical_indicators"
        )
        
        if features_df.empty:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="无法获取特征数据"
            )
        
        # 预测信号
        result = await ml_strategy_service.predict_signal(
            strategy_id=strategy_id,
            stock_code=stock_code,
            current_data=features_df
        )
        
        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )
        
        return result
        
    except Exception as e:
        logger.error(f"预测信号失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="预测信号失败"
        )

@router.delete("/strategies/{strategy_id}")
async def delete_ml_strategy(strategy_id: str):
    """删除机器学习策略"""
    try:
        if ml_strategy_service is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="机器学习策略服务不可用"
            )
        
        result = await ml_strategy_service.delete_strategy(strategy_id)
        
        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )
        
        return result
        
    except Exception as e:
        logger.error(f"删除机器学习策略失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除机器学习策略失败"
        )
