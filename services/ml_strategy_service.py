"""
机器学习策略服务
提供基于机器学习的量化策略开发、训练和优化功能
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import json
import os
import numpy as np
import pandas as pd
from dataclasses import dataclass, asdict
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import joblib

# 导入相关服务
try:
    from .jq_service import jq_service
    from .enhanced_trading_service import enhanced_trading_service
except ImportError:
    jq_service = None
    enhanced_trading_service = None

logger = logging.getLogger(__name__)

@dataclass
class MLStrategy:
    """机器学习策略数据结构"""
    strategy_id: str
    name: str
    description: str
    model_type: str  # random_forest, gradient_boosting, logistic_regression
    features: List[str]
    target_column: str
    parameters: Dict[str, Any]
    performance_metrics: Dict[str, float]
    created_at: datetime
    updated_at: datetime
    is_active: bool

@dataclass
class FeatureSet:
    """特征集数据结构"""
    feature_id: str
    name: str
    description: str
    features: List[str]
    calculation_method: str
    created_at: datetime

@dataclass
class ModelPerformance:
    """模型性能数据结构"""
    model_id: str
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    cross_val_score: float
    backtest_return: float
    backtest_sharpe: float
    backtest_max_drawdown: float
    timestamp: datetime

class MLStrategyService:
    """机器学习策略服务类"""
    
    def __init__(self):
        self.models_dir = "models/"
        self.features_dir = "data/features/"
        self.strategies_file = "data/ml_strategies.json"
        self.features_file = "data/feature_sets.json"
        self.performance_file = "data/model_performance.json"
        
        # 确保目录存在
        os.makedirs(self.models_dir, exist_ok=True)
        os.makedirs(self.features_dir, exist_ok=True)
        os.makedirs("data", exist_ok=True)
        
        # 初始化数据文件
        self._init_data_files()
        
        # 模型类型映射
        self.model_types = {
            "random_forest": RandomForestClassifier,
            "gradient_boosting": GradientBoostingClassifier,
            "logistic_regression": LogisticRegression
        }
        
        # 特征计算器
        self.feature_calculators = {
            "technical_indicators": self._calculate_technical_features,
            "price_patterns": self._calculate_price_features,
            "volume_analysis": self._calculate_volume_features,
            "market_sentiment": self._calculate_sentiment_features
        }
        
        logger.info("机器学习策略服务已启动")
    
    def _init_data_files(self):
        """初始化数据文件"""
        if not os.path.exists(self.strategies_file):
            self._save_data(self.strategies_file, {"strategies": []})
        if not os.path.exists(self.features_file):
            self._save_data(self.features_file, {"feature_sets": []})
        if not os.path.exists(self.performance_file):
            self._save_data(self.performance_file, {"performance": []})
    
    def _save_data(self, file_path: str, data: Any):
        """保存数据到文件"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        except Exception as e:
            logger.error(f"保存数据失败 {file_path}: {e}")
    
    def _load_data(self, file_path: str) -> Any:
        """从文件加载数据"""
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return None
        except Exception as e:
            logger.error(f"加载数据失败 {file_path}: {e}")
            return None
    
    async def create_feature_set(self, name: str, description: str, 
                                calculation_method: str, features: List[str]) -> Dict[str, Any]:
        """创建特征集"""
        try:
            feature_set = FeatureSet(
                feature_id=f"features_{len(self._load_data(self.features_file)['feature_sets']) + 1}",
                name=name,
                description=description,
                features=features,
                calculation_method=calculation_method,
                created_at=datetime.now()
            )
            
            # 保存特征集
            features_data = self._load_data(self.features_file)
            features_data["feature_sets"].append(asdict(feature_set))
            self._save_data(self.features_file, features_data)
            
            logger.info(f"特征集创建成功: {name}")
            return {"message": "特征集创建成功", "feature_set": asdict(feature_set)}
            
        except Exception as e:
            logger.error(f"创建特征集失败: {e}")
            return {"error": f"创建特征集失败: {e}"}
    
    async def calculate_features(self, stock_code: str, start_date: str, 
                               end_date: str, feature_set: str) -> pd.DataFrame:
        """计算特征"""
        try:
            if not jq_service:
                return pd.DataFrame()
            
            # 获取历史数据
            daily_data = await jq_service.get_daily_data(stock_code, start_date, end_date)
            if not daily_data:
                return pd.DataFrame()
            
            # 转换为DataFrame
            df = pd.DataFrame(daily_data)
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')
            
            # 计算技术指标特征
            df = self._calculate_technical_features(df)
            
            # 计算价格特征
            df = self._calculate_price_features(df)
            
            # 计算成交量特征
            df = self._calculate_volume_features(df)
            
            # 计算市场情绪特征
            df = self._calculate_sentiment_features(df)
            
            # 清理数据
            df = df.dropna()
            
            return df
            
        except Exception as e:
            logger.error(f"计算特征失败: {e}")
            return pd.DataFrame()
    
    def _calculate_technical_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算技术指标特征"""
        try:
            # 移动平均线
            df['ma_5'] = df['close'].rolling(window=5).mean()
            df['ma_10'] = df['close'].rolling(window=10).mean()
            df['ma_20'] = df['close'].rolling(window=20).mean()
            df['ma_60'] = df['close'].rolling(window=60).mean()
            
            # 相对强弱指数 (RSI)
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['rsi'] = 100 - (100 / (1 + rs))
            
            # MACD
            exp1 = df['close'].ewm(span=12).mean()
            exp2 = df['close'].ewm(span=26).mean()
            df['macd'] = exp1 - exp2
            df['macd_signal'] = df['macd'].ewm(span=9).mean()
            df['macd_histogram'] = df['macd'] - df['macd_signal']
            
            # 布林带
            df['bb_middle'] = df['close'].rolling(window=20).mean()
            bb_std = df['close'].rolling(window=20).std()
            df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
            df['bb_lower'] = df['bb_middle'] - (bb_std * 2)
            df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']
            
            # KDJ指标
            low_min = df['low'].rolling(window=9).min()
            high_max = df['high'].rolling(window=9).max()
            df['k'] = 100 * ((df['close'] - low_min) / (high_max - low_min))
            df['d'] = df['k'].rolling(window=3).mean()
            df['j'] = 3 * df['k'] - 2 * df['d']
            
            return df
            
        except Exception as e:
            logger.error(f"计算技术指标特征失败: {e}")
            return df
    
    def _calculate_price_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算价格特征"""
        try:
            # 价格变化
            df['price_change'] = df['close'].pct_change()
            df['price_change_5'] = df['close'].pct_change(periods=5)
            df['price_change_10'] = df['close'].pct_change(periods=10)
            
            # 价格位置
            df['price_position_5'] = (df['close'] - df['close'].rolling(window=5).min()) / \
                                    (df['close'].rolling(window=5).max() - df['close'].rolling(window=5).min())
            df['price_position_20'] = (df['close'] - df['close'].rolling(window=20).min()) / \
                                     (df['close'].rolling(window=20).max() - df['close'].rolling(window=20).min())
            
            # 价格波动
            df['volatility_5'] = df['close'].rolling(window=5).std()
            df['volatility_20'] = df['close'].rolling(window=20).std()
            
            # 价格趋势
            df['trend_5'] = np.where(df['ma_5'] > df['ma_5'].shift(1), 1, -1)
            df['trend_20'] = np.where(df['ma_20'] > df['ma_20'].shift(1), 1, -1)
            
            return df
            
        except Exception as e:
            logger.error(f"计算价格特征失败: {e}")
            return df
    
    def _calculate_volume_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算成交量特征"""
        try:
            # 成交量变化
            df['volume_change'] = df['volume'].pct_change()
            df['volume_ma_5'] = df['volume'].rolling(window=5).mean()
            df['volume_ma_20'] = df['volume'].rolling(window=20).mean()
            
            # 成交量比率
            df['volume_ratio_5'] = df['volume'] / df['volume_ma_5']
            df['volume_ratio_20'] = df['volume'] / df['volume_ma_20']
            
            # 价量关系
            df['price_volume_corr'] = df['close'].rolling(window=10).corr(df['volume'])
            
            # 成交量趋势
            df['volume_trend'] = np.where(df['volume'] > df['volume_ma_5'], 1, -1)
            
            return df
            
        except Exception as e:
            logger.error(f"计算成交量特征失败: {e}")
            return df
    
    def _calculate_sentiment_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算市场情绪特征"""
        try:
            # 涨跌比例
            df['up_down_ratio'] = np.where(df['close'] > df['close'].shift(1), 1, 0)
            df['up_down_ratio_5'] = df['up_down_ratio'].rolling(window=5).mean()
            df['up_down_ratio_20'] = df['up_down_ratio'].rolling(window=20).mean()
            
            # 连续涨跌
            df['consecutive_up'] = (df['close'] > df['close'].shift(1)).astype(int).groupby(
                (df['close'] <= df['close'].shift(1)).astype(int).cumsum()
            ).cumsum()
            df['consecutive_down'] = (df['close'] < df['close'].shift(1)).astype(int).groupby(
                (df['close'] >= df['close'].shift(1)).astype(int).cumsum()
            ).cumsum()
            
            # 市场强度
            df['market_strength'] = (df['close'] - df['close'].rolling(window=20).min()) / \
                                   (df['close'].rolling(window=20).max() - df['close'].rolling(window=20).min())
            
            return df
            
        except Exception as e:
            logger.error(f"计算市场情绪特征失败: {e}")
            return df
    
    async def create_target_variable(self, df: pd.DataFrame, method: str = "future_return") -> pd.DataFrame:
        """创建目标变量"""
        try:
            if method == "future_return":
                # 未来5日收益率
                df['target'] = df['close'].shift(-5) / df['close'] - 1
                # 二分类：涨跌
                df['target_binary'] = np.where(df['target'] > 0, 1, 0)
            elif method == "trend":
                # 趋势判断
                df['target'] = np.where(df['close'].shift(-5) > df['close'], 1, 0)
            elif method == "volatility":
                # 波动率预测
                df['target'] = df['close'].rolling(window=5).std().shift(-1)
            
            return df
            
        except Exception as e:
            logger.error(f"创建目标变量失败: {e}")
            return df
    
    async def train_model(self, strategy_name: str, model_type: str, 
                         features: List[str], target_column: str,
                         training_data: pd.DataFrame) -> Dict[str, Any]:
        """训练模型"""
        try:
            # 准备训练数据
            X = training_data[features].fillna(0)
            y = training_data[target_column].fillna(0)
            
            # 数据分割
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            
            # 特征标准化
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            
            # 选择模型
            if model_type not in self.model_types:
                return {"error": f"不支持的模型类型: {model_type}"}
            
            model_class = self.model_types[model_type]
            model = model_class(random_state=42)
            
            # 训练模型
            model.fit(X_train_scaled, y_train)
            
            # 预测和评估
            y_pred = model.predict(X_test_scaled)
            
            # 计算性能指标
            accuracy = accuracy_score(y_test, y_pred)
            precision = precision_score(y_test, y_pred, average='weighted', zero_division=0)
            recall = recall_score(y_test, y_pred, average='weighted', zero_division=0)
            f1 = f1_score(y_test, y_pred, average='weighted', zero_division=0)
            
            # 交叉验证
            cv_scores = cross_val_score(model, X_train_scaled, y_train, cv=5)
            cv_score = cv_scores.mean()
            
            # 保存模型
            model_filename = f"{self.models_dir}{strategy_name}_{model_type}.joblib"
            scaler_filename = f"{self.models_dir}{strategy_name}_{model_type}_scaler.joblib"
            
            joblib.dump(model, model_filename)
            joblib.dump(scaler, scaler_filename)
            
            # 创建策略记录
            strategy = MLStrategy(
                strategy_id=f"ml_strategy_{len(self._load_data(self.strategies_file)['strategies']) + 1}",
                name=strategy_name,
                description=f"基于{model_type}的机器学习策略",
                model_type=model_type,
                features=features,
                target_column=target_column,
                parameters={"test_size": 0.2, "random_state": 42},
                performance_metrics={
                    "accuracy": accuracy,
                    "precision": precision,
                    "recall": recall,
                    "f1_score": f1,
                    "cross_val_score": cv_score
                },
                created_at=datetime.now(),
                updated_at=datetime.now(),
                is_active=True
            )
            
            # 保存策略
            strategies_data = self._load_data(self.strategies_file)
            strategies_data["strategies"].append(asdict(strategy))
            self._save_data(self.strategies_file, strategies_data)
            
            # 保存性能记录
            performance = ModelPerformance(
                model_id=strategy.strategy_id,
                accuracy=accuracy,
                precision=precision,
                recall=recall,
                f1_score=f1,
                cross_val_score=cv_score,
                backtest_return=0.0,  # 待回测后更新
                backtest_sharpe=0.0,
                backtest_max_drawdown=0.0,
                timestamp=datetime.now()
            )
            
            performance_data = self._load_data(self.performance_file)
            performance_data["performance"].append(asdict(performance))
            self._save_data(self.performance_file, performance_data)
            
            logger.info(f"模型训练成功: {strategy_name}")
            return {
                "message": "模型训练成功",
                "strategy": asdict(strategy),
                "performance": asdict(performance)
            }
            
        except Exception as e:
            logger.error(f"模型训练失败: {e}")
            return {"error": f"模型训练失败: {e}"}
    
    async def predict_signal(self, strategy_id: str, stock_code: str, 
                           current_data: pd.DataFrame) -> Dict[str, Any]:
        """预测交易信号"""
        try:
            # 加载策略
            strategies_data = self._load_data(self.strategies_file)
            strategy = next((s for s in strategies_data["strategies"] if s["strategy_id"] == strategy_id), None)
            
            if not strategy:
                return {"error": "策略不存在"}
            
            if not strategy["is_active"]:
                return {"error": "策略未激活"}
            
            # 加载模型和标准化器
            model_filename = f"{self.models_dir}{strategy['name']}_{strategy['model_type']}.joblib"
            scaler_filename = f"{self.models_dir}{strategy['name']}_{strategy['model_type']}_scaler.joblib"
            
            if not os.path.exists(model_filename) or not os.path.exists(scaler_filename):
                return {"error": "模型文件不存在"}
            
            model = joblib.load(model_filename)
            scaler = joblib.load(scaler_filename)
            
            # 准备特征数据
            features = strategy["features"]
            X = current_data[features].fillna(0)
            X_scaled = scaler.transform(X)
            
            # 预测
            prediction = model.predict(X_scaled)
            prediction_proba = model.predict_proba(X_scaled)
            
            # 生成信号
            if strategy["target_column"] == "target_binary":
                # 二分类：买入/卖出
                action = "buy" if prediction[-1] == 1 else "sell"
                confidence = max(prediction_proba[-1])
            else:
                # 回归：根据预测值判断
                pred_value = prediction[-1]
                if pred_value > 0.05:  # 预期收益>5%
                    action = "buy"
                    confidence = min(abs(pred_value) / 0.1, 1.0)  # 标准化置信度
                elif pred_value < -0.05:  # 预期亏损>5%
                    action = "sell"
                    confidence = min(abs(pred_value) / 0.1, 1.0)
                else:
                    action = "hold"
                    confidence = 0.5
            
            return {
                "strategy_id": strategy_id,
                "stock_code": stock_code,
                "action": action,
                "confidence": confidence,
                "prediction": prediction[-1],
                "prediction_proba": prediction_proba[-1].tolist() if len(prediction_proba) > 0 else [],
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"预测信号失败: {e}")
            return {"error": f"预测信号失败: {e}"}
    
    async def get_strategies(self) -> List[Dict[str, Any]]:
        """获取所有策略"""
        try:
            strategies_data = self._load_data(self.strategies_file)
            return strategies_data.get("strategies", [])
        except Exception as e:
            logger.error(f"获取策略失败: {e}")
            return []
    
    async def get_strategy(self, strategy_id: str) -> Optional[Dict[str, Any]]:
        """获取单个策略"""
        try:
            strategies = await self.get_strategies()
            return next((s for s in strategies if s["strategy_id"] == strategy_id), None)
        except Exception as e:
            logger.error(f"获取策略失败: {e}")
            return None
    
    async def update_strategy(self, strategy_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """更新策略"""
        try:
            strategies_data = self._load_data(self.strategies_file)
            for strategy in strategies_data["strategies"]:
                if strategy["strategy_id"] == strategy_id:
                    strategy.update(updates)
                    strategy["updated_at"] = datetime.now().isoformat()
                    self._save_data(self.strategies_file, strategies_data)
                    return {"message": "策略更新成功"}
            
            return {"error": "策略不存在"}
            
        except Exception as e:
            logger.error(f"更新策略失败: {e}")
            return {"error": f"更新策略失败: {e}"}
    
    async def delete_strategy(self, strategy_id: str) -> Dict[str, Any]:
        """删除策略"""
        try:
            strategies_data = self._load_data(self.strategies_file)
            strategies_data["strategies"] = [s for s in strategies_data["strategies"] if s["strategy_id"] != strategy_id]
            self._save_data(self.strategies_file, strategies_data)
            
            # 删除模型文件
            strategy = await self.get_strategy(strategy_id)
            if strategy:
                model_filename = f"{self.models_dir}{strategy['name']}_{strategy['model_type']}.joblib"
                scaler_filename = f"{self.models_dir}{strategy['name']}_{strategy['model_type']}_scaler.joblib"
                
                if os.path.exists(model_filename):
                    os.remove(model_filename)
                if os.path.exists(scaler_filename):
                    os.remove(scaler_filename)
            
            return {"message": "策略删除成功"}
            
        except Exception as e:
            logger.error(f"删除策略失败: {e}")
            return {"error": f"删除策略失败: {e}"}

# 创建全局机器学习策略服务实例
ml_strategy_service = MLStrategyService()
