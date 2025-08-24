#!/usr/bin/env python3
"""
ML增强的KDJ+MACD策略
结合传统技术指标和机器学习预测，实现智能化选股和交易
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime, timedelta

from .ml_strategy_base import MLStrategyBase

logger = logging.getLogger(__name__)

class MLKDJMACDStrategy(MLStrategyBase):
    """ML增强的KDJ+MACD策略"""
    
    def __init__(self, parameters: Dict = None):
        """
        初始化ML增强的KDJ+MACD策略
        
        Args:
            parameters: 策略参数
        """
        # 设置默认参数
        default_params = {
            # ML参数
            'model_type': 'random_forest',
            'feature_window': 20,
            'prediction_horizon': 5,
            'retrain_frequency': 30,
            'min_samples': 1000,
            'cv_folds': 5,
            'random_state': 42,
            'position_size': 0.1,
            'confidence_threshold': 0.7,
            
            # KDJ参数
            'kdj_period': 9,
            'kdj_m1': 3,
            'kdj_m2': 3,
            'kdj_overbought': 80,
            'kdj_oversold': 20,
            
            # MACD参数
            'macd_fast': 12,
            'macd_slow': 26,
            'macd_signal': 9,
            
            # 筛选参数
            'volume_ranking': 'ascending',
            'exclude_st': True,
            'exclude_tech_board': True,
            'exclude_beijing': True,
            'limit_up_within_days': 19,
            'dividend_years': 5,
            'current_no_limit_up': True,
            'current_no_limit_down': True,
            
            # 组合权重
            'ml_weight': 0.6,        # ML预测权重
            'technical_weight': 0.4,  # 技术指标权重
        }
        
        if parameters:
            default_params.update(parameters)
        
        super().__init__("ML增强KDJ+MACD策略", default_params)
        
        # 提取策略特定参数
        self.kdj_period = self.parameters['kdj_period']
        self.kdj_m1 = self.parameters['kdj_m1']
        self.kdj_m2 = self.parameters['kdj_m2']
        self.kdj_overbought = self.parameters['kdj_overbought']
        self.kdj_oversold = self.parameters['kdj_oversold']
        
        self.macd_fast = self.parameters['macd_fast']
        self.macd_slow = self.parameters['macd_slow']
        self.macd_signal = self.parameters['macd_signal']
        
        self.volume_ranking = self.parameters['volume_ranking']
        self.exclude_st = self.parameters['exclude_st']
        self.exclude_tech_board = self.parameters['exclude_tech_board']
        self.exclude_beijing = self.parameters['exclude_beijing']
        self.limit_up_within_days = self.parameters['limit_up_within_days']
        self.dividend_years = self.parameters['dividend_years']
        self.current_no_limit_up = self.parameters['current_no_limit_up']
        self.current_no_limit_down = self.parameters['current_no_limit_down']
        
        self.ml_weight = self.parameters['ml_weight']
        self.technical_weight = self.parameters['technical_weight']
        
        logger.info(f"ML增强KDJ+MACD策略初始化完成")
        logger.info(f"ML权重: {self.ml_weight}, 技术指标权重: {self.technical_weight}")
    
    def _calculate_kdj(self, data: pd.DataFrame) -> pd.DataFrame:
        """计算KDJ指标"""
        result = data.copy()
        
        # 计算RSV
        low_min = result['low'].rolling(window=self.kdj_period).min()
        high_max = result['high'].rolling(window=self.kdj_period).max()
        rsv = 100 * ((result['close'] - low_min) / (high_max - low_min))
        
        # 计算K值
        result['kdj_k'] = rsv.ewm(span=self.kdj_m1).mean()
        
        # 计算D值
        result['kdj_d'] = result['kdj_k'].ewm(span=self.kdj_m2).mean()
        
        # 计算J值
        result['kdj_j'] = 3 * result['kdj_k'] - 2 * result['kdj_d']
        
        return result
    
    def _calculate_macd(self, data: pd.DataFrame) -> pd.DataFrame:
        """计算MACD指标"""
        result = data.copy()
        
        # 计算EMA
        ema_fast = result['close'].ewm(span=self.macd_fast).mean()
        ema_slow = result['close'].ewm(span=self.macd_slow).mean()
        
        # 计算MACD线
        result['macd_line'] = ema_fast - ema_slow
        
        # 计算信号线
        result['macd_signal'] = result['macd_line'].ewm(span=self.macd_signal).mean()
        
        # 计算MACD柱状图
        result['macd_histogram'] = result['macd_line'] - result['macd_signal']
        
        return result
    
    def _check_kdj_trend(self, data: pd.DataFrame, lookback: int = 3) -> pd.Series:
        """检查KDJ趋势"""
        result = pd.Series(0, index=data.index)
        
        # 检查K线向上趋势
        k_up_trend = (data['kdj_k'] > data['kdj_k'].shift(1)) & \
                     (data['kdj_k'].shift(1) > data['kdj_k'].shift(2))
        
        # 检查D线向上趋势
        d_up_trend = (data['kdj_d'] > data['kdj_d'].shift(1)) & \
                     (data['kdj_d'].shift(1) > data['kdj_d'].shift(2))
        
        # 检查J线向上趋势
        j_up_trend = (data['kdj_j'] > data['kdj_j'].shift(1)) & \
                     (data['kdj_j'].shift(1) > data['kdj_j'].shift(2))
        
        # 综合趋势判断
        result = (k_up_trend.astype(int) + d_up_trend.astype(int) + j_up_trend.astype(int)) / 3
        
        return result
    
    def _check_macd_trend(self, data: pd.DataFrame, lookback: int = 3) -> pd.Series:
        """检查MACD趋势"""
        result = pd.Series(0, index=data.index)
        
        # 检查MACD线向上趋势
        macd_up_trend = (data['macd_line'] > data['macd_line'].shift(1)) & \
                        (data['macd_line'].shift(1) > data['macd_line'].shift(2))
        
        # 检查MACD柱状图向上趋势
        histogram_up_trend = (data['macd_histogram'] > data['macd_histogram'].shift(1)) & \
                            (data['macd_histogram'].shift(1) > data['macd_histogram'].shift(2))
        
        # 检查MACD线在零轴上方
        macd_above_zero = data['macd_line'] > 0
        
        # 综合趋势判断
        result = (macd_up_trend.astype(int) + histogram_up_trend.astype(int) + macd_above_zero.astype(int)) / 3
        
        return result
    
    def _engineer_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """特征工程 - 扩展基础特征"""
        # 调用父类特征工程
        result = super()._engineer_features(data)
        
        # 添加KDJ特征
        result = self._calculate_kdj(result)
        result = self._calculate_macd(result)
        
        # KDJ趋势特征
        result['kdj_trend'] = self._check_kdj_trend(result)
        result['macd_trend'] = self._check_macd_trend(result)
        
        # KDJ位置特征
        result['kdj_k_position'] = (result['kdj_k'] - self.kdj_oversold) / (self.kdj_overbought - self.kdj_oversold)
        result['kdj_d_position'] = (result['kdj_d'] - self.kdj_oversold) / (self.kdj_overbought - self.kdj_oversold)
        result['kdj_j_position'] = (result['kdj_j'] - self.kdj_oversold) / (self.kdj_overbought - self.kdj_oversold)
        
        # MACD特征
        result['macd_cross'] = np.where(
            (result['macd_line'] > result['macd_signal']) & 
            (result['macd_line'].shift(1) <= result['macd_signal'].shift(1)), 
            1,  # 金叉
            np.where(
                (result['macd_line'] < result['macd_signal']) & 
                (result['macd_line'].shift(1) >= result['macd_signal'].shift(1)), 
                -1,  # 死叉
                0    # 无交叉
            )
        )
        
        # 成交量特征
        result['volume_surge'] = result['volume'] / result['volume'].rolling(window=20).mean()
        result['volume_trend'] = result['volume'].rolling(window=5).mean() / result['volume'].rolling(window=20).mean()
        
        # 价格动量特征
        result['momentum_5'] = result['close'] / result['close'].shift(5) - 1
        result['momentum_10'] = result['close'] / result['close'].shift(10) - 1
        result['momentum_20'] = result['close'] / result['close'].shift(20) - 1
        
        # 波动率特征
        result['volatility_ratio'] = result['volatility_5'] / result['volatility_20']
        
        return result
    
    def _create_labels(self, data: pd.DataFrame) -> pd.Series:
        """创建标签 - 优化标签定义"""
        # 计算未来价格变化
        future_return = data['close'].shift(-self.prediction_horizon) / data['close'] - 1
        
        # 使用更精细的标签分类
        labels = pd.cut(
            future_return,
            bins=[-np.inf, -0.03, -0.01, 0.01, 0.03, np.inf],
            labels=[-2, -1, 0, 1, 2],  # -2: 大跌, -1: 小跌, 0: 震荡, 1: 小涨, 2: 大涨
            include_lowest=True
        )
        
        # 移除包含NaN的标签
        labels = labels.dropna()
        
        return labels
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        生成交易信号 - 结合ML预测和技术指标
        """
        # 使用ML模型预测
        result = self.predict(data)
        
        # 计算技术指标
        result = self._calculate_kdj(result)
        result = self._calculate_macd(result)
        
        # 计算技术指标趋势
        result['kdj_trend'] = self._check_kdj_trend(result)
        result['macd_trend'] = self._check_macd_trend(result)
        
        # 初始化信号
        result['signal'] = 0
        result['ml_signal'] = 0
        result['technical_signal'] = 0
        result['combined_signal'] = 0
        result['signal_strength'] = 0.0
        
        # 生成ML信号
        if 'ml_prediction' in result.columns and 'ml_confidence' in result.columns:
            high_confidence_mask = result['ml_confidence'] >= self.confidence_threshold
            
            # ML买入信号
            ml_buy_mask = (result['ml_prediction'] >= 1) & high_confidence_mask
            result.loc[ml_buy_mask, 'ml_signal'] = 1
            
            # ML卖出信号
            ml_sell_mask = (result['ml_prediction'] <= -1) & high_confidence_mask
            result.loc[ml_sell_mask, 'ml_signal'] = -1
        
        # 生成技术指标信号
        # KDJ向上且MACD向上
        technical_buy_mask = (result['kdj_trend'] > 0.5) & (result['macd_trend'] > 0.5)
        result.loc[technical_buy_mask, 'technical_signal'] = 1
        
        # KDJ向下且MACD向下
        technical_sell_mask = (result['kdj_trend'] < 0.3) & (result['macd_trend'] < 0.3)
        result.loc[technical_sell_mask, 'technical_signal'] = -1
        
        # 组合信号
        result['combined_signal'] = (
            self.ml_weight * result['ml_signal'] + 
            self.technical_weight * result['technical_signal']
        )
        
        # 计算信号强度
        result['signal_strength'] = abs(result['combined_signal'])
        
        # 生成最终交易信号
        # 买入：组合信号大于0.3
        buy_mask = result['combined_signal'] > 0.3
        result.loc[buy_mask, 'signal'] = 1
        
        # 卖出：组合信号小于-0.3
        sell_mask = result['combined_signal'] < -0.3
        result.loc[sell_mask, 'signal'] = -1
        
        return result
    
    def calculate_position_size(self, signal: int, price: float, cash: float) -> int:
        """
        计算仓位大小 - 基于信号强度
        """
        if signal == 0:
            return 0
        
        # 获取信号强度
        signal_strength = getattr(self, 'last_signal_strength', 0.5)
        
        # 基于信号强度调整仓位
        adjusted_position_size = self.position_size * signal_strength
        
        # 计算仓位
        position_value = cash * adjusted_position_size
        quantity = int(position_value / price)
        
        return quantity if signal > 0 else -quantity
    
    def screen_stocks(self, stock_data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """
        股票筛选 - 结合技术指标和ML预测
        """
        try:
            screened_stocks = {}
            total_stocks = len(stock_data)
            
            for code, data in stock_data.items():
                try:
                    # 基础数据检查
                    if data.empty or len(data) < self.min_samples:
                        continue
                    
                    # 计算技术指标
                    data_with_indicators = self._calculate_kdj(data)
                    data_with_indicators = self._calculate_macd(data_with_indicators)
                    
                    # 获取最新数据
                    latest = data_with_indicators.iloc[-1]
                    
                    # 技术指标筛选
                    kdj_up = latest['kdj_k'] > latest['kdj_d'] and latest['kdj_j'] > latest['kdj_k']
                    macd_up = latest['macd_line'] > latest['macd_signal'] and latest['macd_histogram'] > 0
                    
                    # ML预测（如果有训练好的模型）
                    ml_score = 0
                    if self.model is not None:
                        prediction_result = self.predict(data)
                        if 'ml_prediction' in prediction_result.columns:
                            latest_prediction = prediction_result.iloc[-1]
                            ml_score = latest_prediction.get('ml_confidence', 0) * latest_prediction.get('ml_prediction', 0)
                    
                    # 综合评分
                    technical_score = (kdj_up + macd_up) / 2
                    combined_score = self.technical_weight * technical_score + self.ml_weight * ml_score
                    
                    # 筛选条件
                    if combined_score > 0.5:  # 综合评分大于0.5
                        screened_stocks[code] = {
                            'code': code,
                            'technical_score': technical_score,
                            'ml_score': ml_score,
                            'combined_score': combined_score,
                            'kdj_up': kdj_up,
                            'macd_up': macd_up,
                            'latest_price': latest['close'],
                            'volume': latest['volume']
                        }
                
                except Exception as e:
                    logger.warning(f"筛选股票 {code} 时出错: {e}")
                    continue
            
            # 按综合评分排序
            sorted_stocks = sorted(
                screened_stocks.values(), 
                key=lambda x: x['combined_score'], 
                reverse=True
            )
            
            return {
                'total_screened': total_stocks,
                'total_selected': len(sorted_stocks),
                'selected_stocks': sorted_stocks,
                'screening_criteria': {
                    'technical_weight': self.technical_weight,
                    'ml_weight': self.ml_weight,
                    'min_score_threshold': 0.5
                }
            }
            
        except Exception as e:
            logger.error(f"股票筛选失败: {e}")
            return {}
    
    def get_strategy_summary(self) -> Dict[str, Any]:
        """获取策略摘要"""
        base_summary = super().get_strategy_summary()
        
        strategy_summary = {
            **base_summary,
            'strategy_type': 'ML增强技术指标策略',
            'technical_indicators': ['KDJ', 'MACD'],
            'ml_enhancement': True,
            'signal_combination': f"ML权重: {self.ml_weight}, 技术指标权重: {self.technical_weight}",
            'screening_criteria': {
                'exclude_st': self.exclude_st,
                'exclude_tech_board': self.exclude_tech_board,
                'exclude_beijing': self.exclude_beijing,
                'limit_up_within_days': self.limit_up_within_days,
                'dividend_years': self.dividend_years
            }
        }
        
        return strategy_summary
    
    def optimize_strategy(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        策略优化 - 包括超参数优化和权重调整
        """
        try:
            logger.info("开始策略优化...")
            
            # 超参数优化
            hyperopt_result = self.optimize_hyperparameters(data)
            
            # 权重优化
            weight_optimization = self._optimize_weights(data)
            
            # 阈值优化
            threshold_optimization = self._optimize_thresholds(data)
            
            optimization_result = {
                'hyperparameter_optimization': hyperopt_result,
                'weight_optimization': weight_optimization,
                'threshold_optimization': threshold_optimization,
                'optimization_date': datetime.now().isoformat()
            }
            
            logger.info("策略优化完成")
            return optimization_result
            
        except Exception as e:
            logger.error(f"策略优化失败: {e}")
            return {}
    
    def _optimize_weights(self, data: pd.DataFrame) -> Dict[str, Any]:
        """优化ML和技术指标权重"""
        try:
            # 测试不同的权重组合
            weight_combinations = [
                (0.3, 0.7), (0.4, 0.6), (0.5, 0.5), (0.6, 0.4), (0.7, 0.3)
            ]
            
            best_weights = None
            best_score = -1
            
            for ml_w, tech_w in weight_combinations:
                # 临时设置权重
                original_ml_w = self.ml_weight
                original_tech_w = self.technical_weight
                
                self.ml_weight = ml_w
                self.technical_weight = tech_w
                
                # 生成信号并评估
                signals = self.generate_signals(data)
                score = self._evaluate_signals(signals)
                
                if score > best_score:
                    best_score = score
                    best_weights = (ml_w, tech_w)
                
                # 恢复原始权重
                self.ml_weight = original_ml_w
                self.technical_weight = original_tech_w
            
            # 应用最优权重
            if best_weights:
                self.ml_weight, self.technical_weight = best_weights
                self.parameters['ml_weight'] = self.ml_weight
                self.parameters['technical_weight'] = self.technical_weight
            
            return {
                'best_weights': best_weights,
                'best_score': best_score,
                'optimized_weights': {
                    'ml_weight': self.ml_weight,
                    'technical_weight': self.technical_weight
                }
            }
            
        except Exception as e:
            logger.error(f"权重优化失败: {e}")
            return {}
    
    def _optimize_thresholds(self, data: pd.DataFrame) -> Dict[str, Any]:
        """优化信号阈值"""
        try:
            # 测试不同的置信度阈值
            thresholds = [0.5, 0.6, 0.7, 0.8, 0.9]
            
            best_threshold = None
            best_score = -1
            
            for threshold in thresholds:
                # 临时设置阈值
                original_threshold = self.confidence_threshold
                self.confidence_threshold = threshold
                
                # 生成信号并评估
                signals = self.generate_signals(data)
                score = self._evaluate_signals(signals)
                
                if score > best_score:
                    best_score = score
                    best_threshold = threshold
                
                # 恢复原始阈值
                self.confidence_threshold = original_threshold
            
            # 应用最优阈值
            if best_threshold:
                self.confidence_threshold = best_threshold
                self.parameters['confidence_threshold'] = self.confidence_threshold
            
            return {
                'best_threshold': best_threshold,
                'best_score': best_score,
                'optimized_threshold': self.confidence_threshold
            }
            
        except Exception as e:
            logger.error(f"阈值优化失败: {e}")
            return {}
    
    def _evaluate_signals(self, signals: pd.DataFrame) -> float:
        """评估信号质量"""
        try:
            if 'signal' not in signals.columns:
                return 0.0
            
            # 计算信号变化率
            signal_changes = signals['signal'].diff().abs()
            signal_frequency = signal_changes.sum() / len(signals)
            
            # 计算信号一致性
            signal_consistency = 1 - signal_frequency  # 信号变化越少越好
            
            # 计算信号强度
            if 'signal_strength' in signals.columns:
                avg_strength = signals['signal_strength'].mean()
            else:
                avg_strength = 0.5
            
            # 综合评分
            score = (signal_consistency * 0.4 + avg_strength * 0.6)
            
            return score
            
        except Exception as e:
            logger.error(f"信号评估失败: {e}")
            return 0.0
