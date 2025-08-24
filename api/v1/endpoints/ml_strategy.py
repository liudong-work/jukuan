#!/usr/bin/env python3
"""
机器学习策略API端点
提供ML策略的训练、预测、优化等功能
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Form, Request
from typing import List, Optional, Dict, Any
import logging
import sys
import os
import traceback
from datetime import datetime, timedelta
import json
import pandas as pd
import numpy as np

# Add project root to Python path for module discovery
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

try:
    from src.strategies.ml_kdj_macd_strategy import MLKDJMACDStrategy
    from services.jq_service import jq_service
except ImportError:
    logging.warning("无法导入ML策略或聚宽服务，使用模拟服务")
    MLKDJMACDStrategy = None
    jq_service = None

logger = logging.getLogger(__name__)

router = APIRouter()

# 全局策略实例
ml_strategies = {}

@router.post("/train")
async def train_ml_strategy(
    request: Request,
    strategy_name: str = Form("ml_kdj_macd"),
    stock_code: str = Form("000001"),
    start_date: str = Form("2024-01-01"),
    end_date: str = Form("2024-12-31"),
    parameters: Optional[Dict[str, Any]] = None
):
    """训练ML策略"""
    try:
        if MLKDJMACDStrategy is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="ML策略模块不可用"
            )
        
        if jq_service is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="聚宽服务不可用"
            )
        
        # 解析日期
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="日期格式错误，请使用 YYYY-MM-DD 格式"
            )
        
        # 检查日期范围
        if start_dt >= end_dt:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="开始日期必须早于结束日期"
            )
        
        # 获取训练数据
        logger.info(f"开始获取股票 {stock_code} 的训练数据...")
        
        # 这里应该调用聚宽服务获取历史数据
        # 目前使用模拟数据
        try:
            training_data = _create_mock_training_data(start_dt, end_dt)
            logger.info(f"模拟数据创建成功，数据量: {len(training_data)}")
        except Exception as e:
            logger.error(f"模拟数据创建失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"模拟数据创建失败: {str(e)}"
            )
        
        if training_data.empty:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="无法获取训练数据"
            )
        
        # 创建策略实例
        if parameters is None:
            parameters = {}
        
        # 设置适合API的参数
        api_parameters = {
            'min_samples': 80,  # 降低最小样本数要求
            'retrain_frequency': 1
        }
        api_parameters.update(parameters)
        
        try:
            strategy = MLKDJMACDStrategy(api_parameters)
            logger.info(f"策略实例创建成功: {strategy.name}")
        except Exception as e:
            logger.error(f"策略实例创建失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"策略实例创建失败: {str(e)}"
            )
        
        # 训练模型
        logger.info(f"开始训练ML策略: {strategy_name}")
        try:
            # 检查数据
            logger.info(f"训练数据形状: {training_data.shape}")
            logger.info(f"训练数据列: {list(training_data.columns)}")
            logger.info(f"训练数据范围: {training_data.index.min()} 到 {training_data.index.max()}")
            
            training_success = strategy.train_model(training_data, force_retrain=True)
            logger.info(f"模型训练完成，结果: {training_success}")
        except Exception as e:
            logger.error(f"模型训练异常: {e}")
            logger.error(f"异常详情: {traceback.format_exc()}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"模型训练异常: {str(e)}"
            )
        
        if not training_success:
            logger.error("模型训练返回False")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="模型训练失败"
            )
        
        # 保存策略实例
        ml_strategies[strategy_name] = strategy
        
        # 获取模型信息
        model_info = strategy.get_model_info()
        
        return {
            "success": True,
            "data": {
                "strategy_name": strategy_name,
                "stock_code": stock_code,
                "training_period": f"{start_date} 到 {end_date}",
                "training_samples": len(training_data),
                "model_info": model_info,
                "training_date": datetime.now().isoformat()
            },
            "message": "ML策略训练成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"训练ML策略失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"训练ML策略失败: {str(e)}"
        )

@router.post("/predict")
async def predict_with_ml_strategy(
    request: Request,
    strategy_name: str = Form("ml_kdj_macd"),
    stock_code: str = Form("000001"),
    prediction_date: str = Form(...)
):
    """使用ML策略进行预测"""
    try:
        if strategy_name not in ml_strategies:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"策略 {strategy_name} 不存在，请先训练"
            )
        
        strategy = ml_strategies[strategy_name]
        
        # 检查模型是否已训练
        if not strategy.model:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="模型未训练，请先训练模型"
            )
        
        # 解析预测日期
        try:
            pred_dt = datetime.strptime(prediction_date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="日期格式错误，请使用 YYYY-MM-DD 格式"
            )
        
        # 获取预测数据
        # 这里应该获取到预测日期为止的历史数据
        end_dt = pred_dt
        start_dt = end_dt - timedelta(days=100)  # 获取100天的历史数据
        
        prediction_data = _create_mock_training_data(start_dt, end_dt)
        
        if prediction_data.empty:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="无法获取预测数据"
            )
        
        # 进行预测
        prediction_result = strategy.predict(prediction_data)
        
        # 获取最新预测结果
        latest_prediction = prediction_result.iloc[-1]
        
        # 生成交易信号
        signals = strategy.generate_signals(prediction_data)
        latest_signals = signals.iloc[-1]
        
        return {
            "success": True,
            "data": {
                "strategy_name": strategy_name,
                "stock_code": stock_code,
                "prediction_date": prediction_date,
                "prediction": {
                    "ml_prediction": latest_prediction.get('ml_prediction', None),
                    "ml_confidence": latest_prediction.get('ml_confidence', None),
                    "ml_probability": latest_prediction.get('ml_probability', None)
                },
                "signals": {
                    "signal": latest_signals.get('signal', 0),
                    "ml_signal": latest_signals.get('ml_signal', 0),
                    "technical_signal": latest_signals.get('technical_signal', 0),
                    "combined_signal": latest_signals.get('combined_signal', 0),
                    "signal_strength": latest_signals.get('signal_strength', 0)
                },
                "technical_indicators": {
                    "kdj_k": latest_signals.get('kdj_k', None),
                    "kdj_d": latest_signals.get('kdj_d', None),
                    "kdj_j": latest_signals.get('kdj_j', None),
                    "macd_line": latest_signals.get('macd_line', None),
                    "macd_signal": latest_signals.get('macd_signal', None),
                    "macd_histogram": latest_signals.get('macd_histogram', None)
                },
                "prediction_timestamp": datetime.now().isoformat()
            },
            "message": "ML策略预测成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"ML策略预测失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ML策略预测失败: {str(e)}"
        )

@router.post("/screen")
async def screen_stocks_with_ml_strategy(
    request: Request,
    strategy_name: str = Form("ml_kdj_macd"),
    stock_codes: str = Form("000001,000002,600036"),
    screening_date: str = Form(...)
):
    """使用ML策略进行股票筛选"""
    try:
        if strategy_name not in ml_strategies:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"策略 {strategy_name} 不存在，请先训练"
            )
        
        strategy = ml_strategies[strategy_name]
        
        # 检查模型是否已训练
        if not strategy.model:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="模型未训练，请先训练模型"
            )
        
        # 解析股票代码
        code_list = [code.strip() for code in stock_codes.split(",") if code.strip()]
        
        if not code_list:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="请提供有效的股票代码"
            )
        
        # 解析筛选日期
        try:
            screen_dt = datetime.strptime(screening_date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="日期格式错误，请使用 YYYY-MM-DD 格式"
            )
        
        # 获取股票数据
        stock_data = {}
        for code in code_list:
            try:
                # 这里应该调用聚宽服务获取股票数据
                # 目前使用模拟数据
                end_dt = screen_dt
                start_dt = end_dt - timedelta(days=100)
                stock_data[code] = _create_mock_training_data(start_dt, end_dt)
            except Exception as e:
                logger.warning(f"获取股票 {code} 数据失败: {e}")
                continue
        
        if not stock_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="无法获取任何股票数据"
            )
        
        # 进行股票筛选
        screening_result = strategy.screen_stocks(stock_data)
        
        return {
            "success": True,
            "data": {
                "strategy_name": strategy_name,
                "screening_date": screening_date,
                "screening_result": screening_result,
                "screening_timestamp": datetime.now().isoformat()
            },
            "message": "ML策略股票筛选成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"ML策略股票筛选失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ML策略股票筛选失败: {str(e)}"
        )

@router.post("/optimize")
async def optimize_ml_strategy(
    request: Request,
    strategy_name: str = Form("ml_kdj_macd"),
    stock_code: str = Form("000001"),
    start_date: str = Form("2024-01-01"),
    end_date: str = Form("2024-12-31"),
    optimization_type: str = Form("all")  # all, hyperparameters, weights, thresholds
):
    """优化ML策略"""
    try:
        if strategy_name not in ml_strategies:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"策略 {strategy_name} 不存在，请先训练"
            )
        
        strategy = ml_strategies[strategy_name]
        
        # 解析日期
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="日期格式错误，请使用 YYYY-MM-DD 格式"
            )
        
        # 获取优化数据
        optimization_data = _create_mock_training_data(start_dt, end_dt)
        
        if optimization_data.empty:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="无法获取优化数据"
            )
        
        # 执行策略优化
        if optimization_type == "all":
            optimization_result = strategy.optimize_strategy(optimization_data)
        elif optimization_type == "hyperparameters":
            optimization_result = {
                'hyperparameter_optimization': strategy.optimize_hyperparameters(optimization_data)
            }
        elif optimization_type == "weights":
            optimization_result = {
                'weight_optimization': strategy._optimize_weights(optimization_data)
            }
        elif optimization_type == "thresholds":
            optimization_result = {
                'threshold_optimization': strategy._optimize_thresholds(optimization_data)
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不支持的优化类型"
            )
        
        # 更新策略实例
        ml_strategies[strategy_name] = strategy
        
        return {
            "success": True,
            "data": {
                "strategy_name": strategy_name,
                "stock_code": stock_code,
                "optimization_type": optimization_type,
                "optimization_period": f"{start_date} 到 {end_date}",
                "optimization_result": optimization_result,
                "optimization_timestamp": datetime.now().isoformat()
            },
            "message": "ML策略优化成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"ML策略优化失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ML策略优化失败: {str(e)}"
        )

@router.get("/status")
async def get_ml_strategy_status():
    """获取ML策略状态"""
    try:
        strategy_status = {}
        
        for name, strategy in ml_strategies.items():
            model_info = strategy.get_model_info()
            strategy_status[name] = {
                'name': name,
                'is_trained': model_info['is_trained'],
                'model_type': model_info['model_type'],
                'feature_count': model_info['feature_count'],
                'last_training_date': model_info['last_training_date'],
                'model_performance': model_info['model_performance']
            }
        
        return {
            "success": True,
            "data": {
                "total_strategies": len(ml_strategies),
                "strategies": strategy_status,
                "timestamp": datetime.now().isoformat()
            },
            "message": "获取ML策略状态成功"
        }
        
    except Exception as e:
        logger.error(f"获取ML策略状态失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取ML策略状态失败: {str(e)}"
        )

@router.get("/info/{strategy_name}")
async def get_ml_strategy_info(strategy_name: str):
    """获取特定ML策略的详细信息"""
    try:
        if strategy_name not in ml_strategies:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"策略 {strategy_name} 不存在"
            )
        
        strategy = ml_strategies[strategy_name]
        model_info = strategy.get_model_info()
        strategy_summary = strategy.get_strategy_summary()
        
        return {
            "success": True,
            "data": {
                "strategy_name": strategy_name,
                "model_info": model_info,
                "strategy_summary": strategy_summary,
                "timestamp": datetime.now().isoformat()
            },
            "message": "获取ML策略信息成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取ML策略信息失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取ML策略信息失败: {str(e)}"
        )

@router.delete("/delete/{strategy_name}")
async def delete_ml_strategy(strategy_name: str):
    """删除ML策略"""
    try:
        if strategy_name not in ml_strategies:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"策略 {strategy_name} 不存在"
            )
        
        # 删除策略实例
        del ml_strategies[strategy_name]
        
        return {
            "success": True,
            "data": {
                "strategy_name": strategy_name,
                "deleted": True
            },
            "message": f"ML策略 {strategy_name} 删除成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除ML策略失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除ML策略失败: {str(e)}"
        )

def _create_mock_training_data(start_date: datetime, end_date: datetime) -> pd.DataFrame:
    """创建模拟训练数据"""
    try:
        # 生成日期序列 - 确保有足够的数据
        dates = pd.date_range(start=start_date, end=end_date, freq='D')
        
        # 排除周末
        dates = dates[dates.dayofweek < 5]
        
        # 如果数据量不足，扩展日期范围
        if len(dates) < 200:
            # 向前扩展日期范围
            extended_start = start_date - timedelta(days=100)
            dates = pd.date_range(start=extended_start, end=end_date, freq='D')
            dates = dates[dates.dayofweek < 5]
        
        if len(dates) == 0:
            return pd.DataFrame()
        
        # 设置随机种子以确保可重复性
        np.random.seed(42)
        
        # 生成模拟价格数据
        n_days = len(dates)
        base_price = 100.0
        
        # 生成随机游走价格
        price_changes = np.random.randn(n_days) * 0.02  # 2%的日波动率
        prices = base_price * np.exp(np.cumsum(price_changes))
        
        # 生成OHLCV数据
        data = pd.DataFrame({
            'open': prices * (1 + np.random.randn(n_days) * 0.005),
            'high': prices * (1 + np.abs(np.random.randn(n_days) * 0.01)),
            'low': prices * (1 - np.abs(np.random.randn(n_days) * 0.01)),
            'close': prices,
            'volume': np.random.randint(1000000, 10000000, n_days),
            'amount': prices * np.random.randint(1000000, 10000000, n_days)
        }, index=dates)
        
        # 确保OHLC逻辑正确
        data['high'] = data[['open', 'high', 'close']].max(axis=1)
        data['low'] = data[['open', 'low', 'close']].min(axis=1)
        
        logger.info(f"模拟数据创建成功，数据量: {len(data)}")
        return data
        
    except Exception as e:
        logger.error(f"创建模拟训练数据失败: {e}")
        return pd.DataFrame()
