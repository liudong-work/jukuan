#!/usr/bin/env python3
"""
机器学习策略基类
提供特征工程、模型训练、预测等核心功能
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
import joblib
import os
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.model_selection import train_test_split, GridSearchCV, cross_val_score
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
from sklearn.metrics import classification_report, confusion_matrix
import warnings
warnings.filterwarnings('ignore')

from .base_strategy import BaseStrategy

logger = logging.getLogger(__name__)

class MLStrategyBase(BaseStrategy):
    """机器学习策略基类"""
    
    def __init__(self, name: str, parameters: Dict = None):
        """
        初始化ML策略
        
        Args:
            name: 策略名称
            parameters: 策略参数
        """
        # 设置默认ML参数
        default_params = {
            'model_type': 'random_forest',  # 模型类型
            'feature_window': 20,          # 特征窗口
            'prediction_horizon': 5,       # 预测周期
            'retrain_frequency': 30,       # 重训练频率（天）
            'min_samples': 1000,           # 最小训练样本数
            'cv_folds': 5,                 # 交叉验证折数
            'random_state': 42,            # 随机种子
            'position_size': 0.1,          # 仓位比例
            'confidence_threshold': 0.7,   # 置信度阈值
        }
        
        if parameters:
            default_params.update(parameters)
        
        super().__init__(name, default_params)
        
        # 提取ML参数
        self.model_type = self.parameters['model_type']
        self.feature_window = self.parameters['feature_window']
        self.prediction_horizon = self.parameters['prediction_horizon']
        self.retrain_frequency = self.parameters['retrain_frequency']
        self.min_samples = self.parameters['min_samples']
        self.cv_folds = self.parameters['cv_folds']
        self.random_state = self.parameters['random_state']
        self.confidence_threshold = self.parameters['confidence_threshold']
        
        # ML模型相关
        self.model = None
        self.scaler = StandardScaler()
        self.feature_columns = []
        self.last_training_date = None
        self.model_performance = {}
        
        # 模型文件路径
        self.model_dir = "models"
        os.makedirs(self.model_dir, exist_ok=True)
        
        logger.info(f"ML策略 {name} 初始化完成，模型类型: {self.model_type}")
    
    def _create_model(self) -> Any:
        """创建ML模型"""
        if self.model_type == 'random_forest':
            return RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=self.random_state,
                n_jobs=-1
            )
        elif self.model_type == 'gradient_boosting':
            return GradientBoostingClassifier(
                n_estimators=100,
                learning_rate=0.1,
                max_depth=6,
                random_state=self.random_state
            )
        elif self.model_type == 'logistic_regression':
            return LogisticRegression(
                random_state=self.random_state,
                max_iter=1000,
                solver='liblinear'
            )
        elif self.model_type == 'svm':
            return SVC(
                probability=True,
                random_state=self.random_state,
                kernel='rbf'
            )
        else:
            raise ValueError(f"不支持的模型类型: {self.model_type}")
    
    def _engineer_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        特征工程
        
        Args:
            data: 原始OHLCV数据
            
        Returns:
            pd.DataFrame: 包含特征的DataFrame
        """
        result = data.copy()
        
        # 价格特征
        result['price_change'] = result['close'].pct_change()
        result['price_change_5'] = result['close'].pct_change(periods=5)
        result['price_change_10'] = result['close'].pct_change(periods=10)
        result['price_change_20'] = result['close'].pct_change(periods=20)
        
        # 移动平均特征
        result['ma_5'] = result['close'].rolling(window=5).mean()
        result['ma_10'] = result['close'].rolling(window=10).mean()
        result['ma_20'] = result['close'].rolling(window=20).mean()
        result['ma_50'] = result['close'].rolling(window=50).mean()
        
        # 价格相对位置
        result['price_vs_ma5'] = (result['close'] - result['ma_5']) / result['ma_5']
        result['price_vs_ma10'] = (result['close'] - result['ma_10']) / result['ma_10']
        result['price_vs_ma20'] = (result['close'] - result['ma_20']) / result['ma_20']
        result['price_vs_ma50'] = (result['close'] - result['ma_50']) / result['ma_50']
        
        # 成交量特征
        result['volume_ma_5'] = result['volume'].rolling(window=5).mean()
        result['volume_ma_20'] = result['volume'].rolling(window=20).mean()
        result['volume_ratio'] = result['volume'] / result['volume_ma_20']
        
        # 波动率特征
        result['volatility_5'] = result['price_change'].rolling(window=5).std()
        result['volatility_20'] = result['price_change'].rolling(window=20).std()
        
        # 技术指标特征
        result = self._add_technical_indicators(result)
        
        # 时间特征
        result['day_of_week'] = result.index.dayofweek
        result['month'] = result.index.month
        result['quarter'] = result.index.quarter
        
        # 滞后特征
        for i in range(1, self.feature_window + 1):
            result[f'price_lag_{i}'] = result['close'].shift(i)
            result[f'volume_lag_{i}'] = result['volume'].shift(i)
            result[f'price_change_lag_{i}'] = result['price_change'].shift(i)
        
        # 滚动统计特征
        result['price_rolling_mean_5'] = result['close'].rolling(window=5).mean()
        result['price_rolling_std_5'] = result['close'].rolling(window=5).std()
        result['price_rolling_min_5'] = result['close'].rolling(window=5).min()
        result['price_rolling_max_5'] = result['close'].rolling(window=5).max()
        
        return result
    
    def _add_technical_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """添加技术指标特征"""
        result = data.copy()
        
        # RSI
        delta = result['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        result['rsi'] = 100 - (100 / (1 + rs))
        
        # MACD
        ema_12 = result['close'].ewm(span=12).mean()
        ema_26 = result['close'].ewm(span=26).mean()
        result['macd'] = ema_12 - ema_26
        result['macd_signal'] = result['macd'].ewm(span=9).mean()
        result['macd_histogram'] = result['macd'] - result['macd_signal']
        
        # 布林带
        result['bb_middle'] = result['close'].rolling(window=20).mean()
        bb_std = result['close'].rolling(window=20).std()
        result['bb_upper'] = result['bb_middle'] + (bb_std * 2)
        result['bb_lower'] = result['bb_middle'] - (bb_std * 2)
        result['bb_width'] = (result['bb_upper'] - result['bb_lower']) / result['bb_middle']
        result['bb_position'] = (result['close'] - result['bb_lower']) / (result['bb_upper'] - result['bb_lower'])
        
        # KDJ
        low_min = result['low'].rolling(window=9).min()
        high_max = result['high'].rolling(window=9).max()
        rsv = 100 * ((result['close'] - low_min) / (high_max - low_min))
        result['k'] = rsv.ewm(span=3).mean()
        result['d'] = result['k'].ewm(span=3).mean()
        result['j'] = 3 * result['k'] - 2 * result['d']
        
        return result
    
    def _create_labels(self, data: pd.DataFrame) -> pd.Series:
        """
        创建标签（未来价格走势）
        
        Args:
            data: 包含特征的DataFrame
            
        Returns:
            pd.Series: 标签序列
        """
        # 计算未来价格变化
        future_return = data['close'].shift(-self.prediction_horizon) / data['close'] - 1
        
        # 创建分类标签
        labels = pd.cut(
            future_return,
            bins=[-np.inf, -0.02, 0.02, np.inf],
            labels=[-1, 0, 1],  # -1: 下跌, 0: 震荡, 1: 上涨
            include_lowest=True
        )
        
        # 移除包含NaN的标签
        labels = labels.dropna()
        
        return labels
    
    def _prepare_training_data(self, data: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
        """
        准备训练数据
        
        Args:
            data: 原始数据
            
        Returns:
            Tuple[pd.DataFrame, pd.Series]: 特征和标签
        """
        # 特征工程
        feature_data = self._engineer_features(data)
        
        # 创建标签
        labels = self._create_labels(feature_data)
        
        # 确保特征和标签对齐
        common_index = feature_data.index.intersection(labels.index)
        feature_data = feature_data.loc[common_index]
        labels = labels.loc[common_index]
        
        # 移除包含NaN的行
        feature_data = feature_data.dropna()
        labels = labels[feature_data.index]
        
        # 选择特征列
        exclude_columns = ['open', 'high', 'low', 'close', 'volume', 'amount']
        self.feature_columns = [col for col in feature_data.columns 
                               if col not in exclude_columns and not col.startswith('label')]
        
        X = feature_data[self.feature_columns]
        y = labels
        
        return X, y
    
    def train_model(self, data: pd.DataFrame, force_retrain: bool = False) -> bool:
        """
        训练模型
        
        Args:
            data: 训练数据
            force_retrain: 是否强制重训练
            
        Returns:
            bool: 训练是否成功
        """
        try:
            # 检查是否需要重训练
            if not force_retrain and self._should_skip_training():
                logger.info("跳过模型训练，使用现有模型")
                return True
            
            # 检查数据量是否足够
            if len(data) < self.min_samples:
                logger.warning(f"数据量不足，需要至少 {self.min_samples} 条，当前只有 {len(data)} 条")
                return False
            
            logger.info(f"开始训练模型，数据量: {len(data)}")
            
            # 准备训练数据
            X, y = self._prepare_training_data(data)
            
            if len(X) < self.min_samples:
                logger.warning(f"特征数据量不足，需要至少 {self.min_samples} 条，当前只有 {len(X)} 条")
                return False
            
            # 数据标准化
            X_scaled = self.scaler.fit_transform(X)
            
            # 分割训练集和验证集
            X_train, X_val, y_train, y_val = train_test_split(
                X_scaled, y, test_size=0.2, random_state=self.random_state, stratify=y
            )
            
            # 创建模型
            self.model = self._create_model()
            
            # 训练模型
            self.model.fit(X_train, y_train)
            
            # 评估模型
            train_score = self.model.score(X_train, y_train)
            val_score = self.model.score(X_val, y_val)
            
            # 预测验证集
            y_pred = self.model.predict(X_val)
            y_pred_proba = self.model.predict_proba(X_val)
            
            # 计算详细指标
            self.model_performance = {
                'train_accuracy': train_score,
                'val_accuracy': val_score,
                'precision': precision_score(y_val, y_pred, average='weighted'),
                'recall': recall_score(y_val, y_pred, average='weighted'),
                'f1': f1_score(y_val, y_pred, average='weighted'),
                'roc_auc': roc_auc_score(pd.get_dummies(y_val), y_pred_proba, multi_class='ovr'),
                'training_date': datetime.now().isoformat(),
                'training_samples': len(X_train),
                'validation_samples': len(X_val)
            }
            
            # 更新训练日期
            self.last_training_date = datetime.now()
            
            # 保存模型
            self._save_model()
            
            logger.info(f"模型训练完成，验证准确率: {val_score:.4f}")
            logger.info(f"模型性能: {self.model_performance}")
            
            return True
            
        except Exception as e:
            logger.error(f"模型训练失败: {e}")
            return False
    
    def _should_skip_training(self) -> bool:
        """检查是否应该跳过训练"""
        if self.model is None:
            return False
        
        if self.last_training_date is None:
            return False
        
        days_since_training = (datetime.now() - self.last_training_date).days
        return days_since_training < self.retrain_frequency
    
    def predict(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        使用模型进行预测
        
        Args:
            data: 输入数据
            
        Returns:
            pd.DataFrame: 包含预测结果的DataFrame
        """
        if self.model is None:
            logger.warning("模型未训练，无法进行预测")
            return data
        
        try:
            # 特征工程
            feature_data = self._engineer_features(data)
            
            # 选择特征
            if not self.feature_columns:
                logger.warning("特征列未定义，无法进行预测")
                return data
            
            X = feature_data[self.feature_columns].dropna()
            
            if X.empty:
                logger.warning("没有有效的特征数据")
                return data
            
            # 数据标准化
            X_scaled = self.scaler.transform(X)
            
            # 预测
            predictions = self.model.predict(X_scaled)
            prediction_proba = self.model.predict_proba(X_scaled)
            
            # 创建结果DataFrame
            result = data.copy()
            result['ml_prediction'] = np.nan
            result['ml_confidence'] = np.nan
            result['ml_probability'] = np.nan
            
            # 填充预测结果
            for i, idx in enumerate(X.index):
                result.loc[idx, 'ml_prediction'] = predictions[i]
                result.loc[idx, 'ml_confidence'] = np.max(prediction_proba[i])
                result.loc[idx, 'ml_probability'] = prediction_proba[i][1]  # 上涨概率
            
            return result
            
        except Exception as e:
            logger.error(f"模型预测失败: {e}")
            return data
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        生成交易信号
        
        Args:
            data: 输入数据
            
        Returns:
            pd.DataFrame: 包含交易信号的数据
        """
        # 使用ML模型预测
        result = self.predict(data)
        
        # 生成交易信号
        result['signal'] = 0  # 默认无信号
        
        # 基于ML预测和置信度生成信号
        if 'ml_prediction' in result.columns and 'ml_confidence' in result.columns:
            # 高置信度预测
            high_confidence_mask = result['ml_confidence'] >= self.confidence_threshold
            
            # 买入信号：预测上涨且高置信度
            buy_mask = (result['ml_prediction'] == 1) & high_confidence_mask
            result.loc[buy_mask, 'signal'] = 1
            
            # 卖出信号：预测下跌且高置信度
            sell_mask = (result['ml_prediction'] == -1) & high_confidence_mask
            result.loc[sell_mask, 'signal'] = -1
        
        return result
    
    def calculate_position_size(self, signal: int, price: float, cash: float) -> int:
        """
        计算仓位大小
        
        Args:
            signal: 交易信号
            price: 当前价格
            cash: 可用资金
            
        Returns:
            int: 交易数量
        """
        if signal == 0:
            return 0
        
        # 基于置信度调整仓位
        confidence = getattr(self, 'last_confidence', 0.5)
        adjusted_position_size = self.position_size * confidence
        
        # 计算仓位
        position_value = cash * adjusted_position_size
        quantity = int(position_value / price)
        
        return quantity if signal > 0 else -quantity
    
    def _save_model(self):
        """保存模型"""
        try:
            model_path = os.path.join(self.model_dir, f"{self.name}_model.pkl")
            scaler_path = os.path.join(self.model_dir, f"{self.name}_scaler.pkl")
            
            joblib.dump(self.model, model_path)
            joblib.dump(self.scaler, scaler_path)
            
            logger.info(f"模型保存成功: {model_path}")
            
        except Exception as e:
            logger.error(f"模型保存失败: {e}")
    
    def load_model(self) -> bool:
        """加载模型"""
        try:
            model_path = os.path.join(self.model_dir, f"{self.name}_model.pkl")
            scaler_path = os.path.join(self.model_dir, f"{self.name}_scaler.pkl")
            
            if os.path.exists(model_path) and os.path.exists(scaler_path):
                self.model = joblib.load(model_path)
                self.scaler = joblib.load(scaler_path)
                
                # 尝试加载性能指标
                performance_path = os.path.join(self.model_dir, f"{self.name}_performance.json")
                if os.path.exists(performance_path):
                    with open(performance_path, 'r') as f:
                        self.model_performance = json.load(f)
                
                logger.info(f"模型加载成功: {model_path}")
                return True
            else:
                logger.warning("模型文件不存在，需要先训练模型")
                return False
                
        except Exception as e:
            logger.error(f"模型加载失败: {e}")
            return False
    
    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        return {
            'name': self.name,
            'model_type': self.model_type,
            'feature_count': len(self.feature_columns),
            'feature_columns': self.feature_columns,
            'last_training_date': self.last_training_date.isoformat() if self.last_training_date else None,
            'retrain_frequency_days': self.retrain_frequency,
            'min_samples': self.min_samples,
            'model_performance': self.model_performance,
            'is_trained': self.model is not None
        }
    
    def optimize_hyperparameters(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        超参数优化
        
        Args:
            data: 训练数据
            
        Returns:
            Dict: 最优参数
        """
        try:
            logger.info("开始超参数优化...")
            
            # 准备数据
            X, y = self._prepare_training_data(data)
            X_scaled = self.scaler.fit_transform(X)
            
            # 定义参数网格
            if self.model_type == 'random_forest':
                param_grid = {
                    'n_estimators': [50, 100, 200],
                    'max_depth': [5, 10, 15, None],
                    'min_samples_split': [2, 5, 10],
                    'min_samples_leaf': [1, 2, 4]
                }
            elif self.model_type == 'gradient_boosting':
                param_grid = {
                    'n_estimators': [50, 100, 200],
                    'learning_rate': [0.05, 0.1, 0.2],
                    'max_depth': [3, 6, 9],
                    'subsample': [0.8, 0.9, 1.0]
                }
            else:
                logger.warning(f"模型类型 {self.model_type} 暂不支持超参数优化")
                return {}
            
            # 网格搜索
            grid_search = GridSearchCV(
                self._create_model(),
                param_grid,
                cv=self.cv_folds,
                scoring='accuracy',
                n_jobs=-1,
                verbose=1
            )
            
            grid_search.fit(X_scaled, y)
            
            # 更新最优参数
            best_params = grid_search.best_params_
            best_score = grid_search.best_score_
            
            logger.info(f"超参数优化完成，最优分数: {best_score:.4f}")
            logger.info(f"最优参数: {best_params}")
            
            # 使用最优参数重新训练
            self.parameters.update(best_params)
            self.train_model(data, force_retrain=True)
            
            return {
                'best_params': best_params,
                'best_score': best_score,
                'optimization_date': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"超参数优化失败: {e}")
            return {}
