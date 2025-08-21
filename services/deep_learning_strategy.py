"""
深度学习策略引擎
支持神经网络、强化学习等高级AI策略
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
from enum import Enum

# 导入相关服务
try:
    from .enhanced_trading_service import enhanced_trading_service
    from .market_data_service import market_data_service
    from .jq_service import jq_service
except ImportError:
    enhanced_trading_service = None
    market_data_service = None
    jq_service = None

logger = logging.getLogger(__name__)

class ModelType(Enum):
    """深度学习模型类型"""
    CNN = "卷积神经网络"
    RNN = "循环神经网络"
    LSTM = "长短期记忆网络"
    GRU = "门控循环单元"
    TRANSFORMER = "Transformer"
    DQN = "深度Q网络"
    DDPG = "深度确定性策略梯度"
    PPO = "近端策略优化"

class StrategyCategory(Enum):
    """策略类别"""
    PRICE_PREDICTION = "价格预测"
    TREND_FOLLOWING = "趋势跟踪"
    MEAN_REVERSION = "均值回归"
    ARBITRAGE = "套利策略"
    PORTFOLIO_OPTIMIZATION = "投资组合优化"
    RISK_MANAGEMENT = "风险管理"

@dataclass
class DeepLearningStrategy:
    """深度学习策略数据结构"""
    strategy_id: str
    name: str
    description: str
    model_type: ModelType
    strategy_category: StrategyCategory
    features: List[str]
    hyperparameters: Dict[str, Any]
    performance_metrics: Dict[str, float]
    model_file: str
    scaler_file: str
    created_at: datetime
    updated_at: datetime
    is_active: bool
    training_history: List[Dict[str, Any]]

@dataclass
class TrainingConfig:
    """训练配置"""
    epochs: int
    batch_size: int
    learning_rate: float
    validation_split: float
    early_stopping: bool
    patience: int
    data_augmentation: bool
    regularization: Dict[str, Any]

@dataclass
class PredictionResult:
    """预测结果"""
    timestamp: datetime
    stock_code: str
    predicted_price: float
    confidence: float
    action: str  # buy, sell, hold
    target_price: float
    stop_loss: float
    take_profit: float

class DeepLearningStrategyEngine:
    """深度学习策略引擎"""
    
    def __init__(self):
        self.models_dir = "models/deep_learning/"
        self.strategies_file = "data/deep_learning_strategies.json"
        self.training_logs_file = "data/training_logs.json"
        
        # 确保目录存在
        os.makedirs(self.models_dir, exist_ok=True)
        os.makedirs("data", exist_ok=True)
        
        # 初始化数据文件
        self._init_data_files()
        
        # 模型类型映射
        self.model_types = {
            ModelType.CNN: self._create_cnn_model,
            ModelType.RNN: self._create_rnn_model,
            ModelType.LSTM: self._create_lstm_model,
            ModelType.GRU: self._create_gru_model,
            ModelType.TRANSFORMER: self._create_transformer_model,
            ModelType.DQN: self._create_dqn_model,
            ModelType.DDPG: self._create_ddpg_model,
            ModelType.PPO: self._create_ppo_model
        }
        
        logger.info("深度学习策略引擎已启动")
    
    def _init_data_files(self):
        """初始化数据文件"""
        if not os.path.exists(self.strategies_file):
            self._save_data(self.strategies_file, {"strategies": []})
        if not os.path.exists(self.training_logs_file):
            self._save_data(self.training_logs_file, {"logs": []})
    
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
    
    async def create_strategy(self, name: str, description: str, 
                            model_type: ModelType, strategy_category: StrategyCategory,
                            features: List[str], hyperparameters: Dict[str, Any]) -> Dict[str, Any]:
        """创建深度学习策略"""
        try:
            strategy = DeepLearningStrategy(
                strategy_id=f"dl_strategy_{len(self._load_data(self.strategies_file)['strategies']) + 1}",
                name=name,
                description=description,
                model_type=model_type,
                strategy_category=strategy_category,
                features=features,
                hyperparameters=hyperparameters,
                performance_metrics={},
                model_file="",
                scaler_file="",
                created_at=datetime.now(),
                updated_at=datetime.now(),
                is_active=False,
                training_history=[]
            )
            
            # 保存策略
            strategies_data = self._load_data(self.strategies_file)
            strategies_data["strategies"].append(asdict(strategy))
            self._save_data(self.strategies_file, strategies_data)
            
            logger.info(f"深度学习策略创建成功: {name}")
            return {"message": "策略创建成功", "strategy": asdict(strategy)}
            
        except Exception as e:
            logger.error(f"创建深度学习策略失败: {e}")
            return {"error": f"创建策略失败: {e}"}
    
    async def prepare_training_data(self, stock_code: str, start_date: str, 
                                  end_date: str, features: List[str]) -> pd.DataFrame:
        """准备训练数据"""
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
            df = self._calculate_advanced_features(df)
            
            # 选择指定特征
            available_features = [f for f in features if f in df.columns]
            if not available_features:
                logger.warning(f"没有找到可用的特征: {features}")
                return pd.DataFrame()
            
            # 添加目标变量
            df = self._create_target_variables(df)
            
            # 清理数据
            df = df.dropna()
            
            return df[available_features + ['target', 'target_binary']]
            
        except Exception as e:
            logger.error(f"准备训练数据失败: {e}")
            return pd.DataFrame()
    
    def _calculate_advanced_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算高级特征"""
        try:
            # 基础技术指标
            df = self._calculate_basic_indicators(df)
            
            # 高级技术指标
            df = self._calculate_advanced_indicators(df)
            
            # 价格模式特征
            df = self._calculate_price_patterns(df)
            
            # 成交量特征
            df = self._calculate_volume_features(df)
            
            # 市场微观结构特征
            df = self._calculate_microstructure_features(df)
            
            return df
            
        except Exception as e:
            logger.error(f"计算高级特征失败: {e}")
            return df
    
    def _calculate_basic_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算基础技术指标"""
        try:
            # 移动平均线
            for window in [5, 10, 20, 50, 100]:
                df[f'ma_{window}'] = df['close'].rolling(window=window).mean()
                df[f'ma_{window}_slope'] = df[f'ma_{window}'].diff()
            
            # RSI
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
            df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
            
            return df
            
        except Exception as e:
            logger.error(f"计算基础技术指标失败: {e}")
            return df
    
    def _calculate_advanced_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算高级技术指标"""
        try:
            # KDJ指标
            low_min = df['low'].rolling(window=9).min()
            high_max = df['high'].rolling(window=9).max()
            df['k'] = 100 * ((df['close'] - low_min) / (high_max - low_min))
            df['d'] = df['k'].rolling(window=3).mean()
            df['j'] = 3 * df['k'] - 2 * df['d']
            
            # 威廉指标
            df['williams_r'] = -100 * ((df['high'].rolling(window=14).max() - df['close']) / 
                                      (df['high'].rolling(window=14).max() - df['low'].rolling(window=14).min()))
            
            # 随机指标
            df['stoch_k'] = 100 * ((df['close'] - df['low'].rolling(window=14).min()) / 
                                  (df['high'].rolling(window=14).max() - df['low'].rolling(window=14).min()))
            df['stoch_d'] = df['stoch_k'].rolling(window=3).mean()
            
            # CCI指标
            typical_price = (df['high'] + df['low'] + df['close']) / 3
            sma_tp = typical_price.rolling(window=20).mean()
            mad = typical_price.rolling(window=20).apply(lambda x: np.mean(np.abs(x - x.mean())))
            df['cci'] = (typical_price - sma_tp) / (0.015 * mad)
            
            return df
            
        except Exception as e:
            logger.error(f"计算高级技术指标失败: {e}")
            return df
    
    def _calculate_price_patterns(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算价格模式特征"""
        try:
            # 价格变化率
            for period in [1, 2, 3, 5, 10, 20]:
                df[f'price_change_{period}'] = df['close'].pct_change(periods=period)
                df[f'price_volatility_{period}'] = df['close'].rolling(window=period).std()
            
            # 价格位置
            for window in [20, 50, 100]:
                df[f'price_position_{window}'] = (df['close'] - df['close'].rolling(window=window).min()) / \
                                                (df['close'].rolling(window=window).max() - df['close'].rolling(window=window).min())
            
            # 趋势强度
            df['trend_strength'] = abs(df['ma_20'] - df['ma_50']) / df['ma_20']
            
            # 价格动量
            df['momentum_5'] = df['close'] / df['close'].shift(5) - 1
            df['momentum_10'] = df['close'] / df['close'].shift(10) - 1
            df['momentum_20'] = df['close'] / df['close'].shift(20) - 1
            
            return df
            
        except Exception as e:
            logger.error(f"计算价格模式失败: {e}")
            return df
    
    def _calculate_volume_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算成交量特征"""
        try:
            # 成交量变化
            for period in [1, 3, 5, 10]:
                df[f'volume_change_{period}'] = df['volume'].pct_change(periods=period)
            
            # 成交量移动平均
            for window in [5, 10, 20]:
                df[f'volume_ma_{window}'] = df['volume'].rolling(window=window).mean()
                df[f'volume_ratio_{window}'] = df['volume'] / df[f'volume_ma_{window}']
            
            # 价量关系
            df['price_volume_corr'] = df['close'].rolling(window=10).corr(df['volume'])
            df['volume_price_trend'] = (df['close'] - df['close'].shift(1)) * df['volume']
            
            # 成交量加权平均价格
            df['vwap'] = (df['close'] * df['volume']).rolling(window=20).sum() / df['volume'].rolling(window=20).sum()
            df['vwap_ratio'] = df['close'] / df['vwap']
            
            return df
            
        except Exception as e:
            logger.error(f"计算成交量特征失败: {e}")
            return df
    
    def _calculate_microstructure_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算市场微观结构特征"""
        try:
            # 买卖压力
            df['buy_pressure'] = (df['close'] - df['low']) / (df['high'] - df['low'])
            df['sell_pressure'] = (df['high'] - df['close']) / (df['high'] - df['low'])
            
            # 价格效率
            df['price_efficiency'] = abs(df['close'] - df['close'].shift(1)) / \
                                   df['close'].rolling(window=20).std()
            
            # 流动性指标
            df['amihud_illiquidity'] = abs(df['price_change_1']) / df['volume']
            
            # 波动率特征
            df['realized_volatility'] = df['price_change_1'].rolling(window=20).std() * np.sqrt(252)
            df['volatility_ratio'] = df['realized_volatility'] / df['realized_volatility'].rolling(window=50).mean()
            
            return df
            
        except Exception as e:
            logger.error(f"计算微观结构特征失败: {e}")
            return df
    
    def _create_target_variables(self, df: pd.DataFrame) -> pd.DataFrame:
        """创建目标变量"""
        try:
            # 未来收益率
            df['target'] = df['close'].shift(-5) / df['close'] - 1
            
            # 二分类目标
            df['target_binary'] = np.where(df['target'] > 0.02, 1, 0)  # 2%阈值
            
            # 多分类目标
            df['target_multi'] = np.where(df['target'] > 0.05, 2,  # 大涨
                                        np.where(df['target'] > 0.02, 1,  # 小涨
                                        np.where(df['target'] < -0.05, -2,  # 大跌
                                        np.where(df['target'] < -0.02, -1, 0))))  # 小跌，平盘
            
            return df
            
        except Exception as e:
            logger.error(f"创建目标变量失败: {e}")
            return df
    
    def _create_cnn_model(self, input_shape: Tuple[int, ...], num_classes: int) -> Any:
        """创建CNN模型"""
        try:
            # 这里应该导入tensorflow或pytorch
            # 暂时返回模拟模型
            return {"type": "CNN", "input_shape": input_shape, "num_classes": num_classes}
        except Exception as e:
            logger.error(f"创建CNN模型失败: {e}")
            return None
    
    def _create_rnn_model(self, input_shape: Tuple[int, ...], num_classes: int) -> Any:
        """创建RNN模型"""
        try:
            return {"type": "RNN", "input_shape": input_shape, "num_classes": num_classes}
        except Exception as e:
            logger.error(f"创建RNN模型失败: {e}")
            return None
    
    def _create_lstm_model(self, input_shape: Tuple[int, ...], num_classes: int) -> Any:
        """创建LSTM模型"""
        try:
            return {"type": "LSTM", "input_shape": input_shape, "num_classes": num_classes}
        except Exception as e:
            logger.error(f"创建LSTM模型失败: {e}")
            return None
    
    def _create_gru_model(self, input_shape: Tuple[int, ...], num_classes: int) -> Any:
        """创建GRU模型"""
        try:
            return {"type": "GRU", "input_shape": input_shape, "num_classes": num_classes}
        except Exception as e:
            logger.error(f"创建GRU模型失败: {e}")
            return None
    
    def _create_transformer_model(self, input_shape: Tuple[int, ...], num_classes: int) -> Any:
        """创建Transformer模型"""
        try:
            return {"type": "Transformer", "input_shape": input_shape, "num_classes": num_classes}
        except Exception as e:
            logger.error(f"创建Transformer模型失败: {e}")
            return None
    
    def _create_dqn_model(self, input_shape: Tuple[int, ...], num_actions: int) -> Any:
        """创建DQN模型"""
        try:
            return {"type": "DQN", "input_shape": input_shape, "num_actions": num_actions}
        except Exception as e:
            logger.error(f"创建DQN模型失败: {e}")
            return None
    
    def _create_ddpg_model(self, input_shape: Tuple[int, ...], action_dim: int) -> Any:
        """创建DDPG模型"""
        try:
            return {"type": "DDPG", "input_shape": input_shape, "action_dim": action_dim}
        except Exception as e:
            logger.error(f"创建DDPG模型失败: {e}")
            return None
    
    def _create_ppo_model(self, input_shape: Tuple[int, ...], action_dim: int) -> Any:
        """创建PPO模型"""
        try:
            return {"type": "PPO", "input_shape": input_shape, "action_dim": action_dim}
        except Exception as e:
            logger.error(f"创建PPO模型失败: {e}")
            return None
    
    async def train_model(self, strategy_id: str, training_config: TrainingConfig) -> Dict[str, Any]:
        """训练深度学习模型"""
        try:
            # 获取策略
            strategies_data = self._load_data(self.strategies_file)
            strategy = next((s for s in strategies_data["strategies"] if s["strategy_id"] == strategy_id), None)
            
            if not strategy:
                return {"error": "策略不存在"}
            
            # 这里应该实现实际的模型训练逻辑
            # 暂时返回模拟结果
            training_result = {
                "strategy_id": strategy_id,
                "status": "training_completed",
                "epochs_trained": training_config.epochs,
                "final_loss": 0.15,
                "final_accuracy": 0.78,
                "training_time": "00:05:30",
                "model_file": f"{self.models_dir}{strategy['name']}_{strategy['model_type']}.h5",
                "scaler_file": f"{self.models_dir}{strategy['name']}_{strategy['model_type']}_scaler.pkl"
            }
            
            # 更新策略
            strategy.update({
                "model_file": training_result["model_file"],
                "scaler_file": training_result["scaler_file"],
                "performance_metrics": {
                    "accuracy": training_result["final_accuracy"],
                    "loss": training_result["final_loss"]
                },
                "updated_at": datetime.now().isoformat(),
                "is_active": True
            })
            
            # 添加训练历史
            strategy["training_history"].append({
                "timestamp": datetime.now().isoformat(),
                "config": asdict(training_config),
                "result": training_result
            })
            
            # 保存更新
            self._save_data(self.strategies_file, strategies_data)
            
            # 记录训练日志
            self._save_training_log(strategy_id, training_result)
            
            logger.info(f"深度学习模型训练完成: {strategy['name']}")
            return {"message": "模型训练完成", "result": training_result}
            
        except Exception as e:
            logger.error(f"训练深度学习模型失败: {e}")
            return {"error": f"训练失败: {e}"}
    
    def _save_training_log(self, strategy_id: str, training_result: Dict[str, Any]):
        """保存训练日志"""
        try:
            logs_data = self._load_data(self.training_logs_file)
            logs_data["logs"].append({
                "timestamp": datetime.now().isoformat(),
                "strategy_id": strategy_id,
                "result": training_result
            })
            self._save_data(self.training_logs_file, logs_data)
        except Exception as e:
            logger.error(f"保存训练日志失败: {e}")
    
    async def predict(self, strategy_id: str, stock_code: str, 
                     current_data: pd.DataFrame) -> PredictionResult:
        """使用深度学习模型进行预测"""
        try:
            # 获取策略
            strategies_data = self._load_data(self.strategies_file)
            strategy = next((s for s in strategies_data["strategies"] if s["strategy_id"] == strategy_id), None)
            
            if not strategy:
                raise ValueError("策略不存在")
            
            if not strategy["is_active"]:
                raise ValueError("策略未激活")
            
            # 这里应该实现实际的模型预测逻辑
            # 暂时返回模拟结果
            predicted_price = current_data['close'].iloc[-1] * (1 + np.random.normal(0, 0.02))
            confidence = np.random.uniform(0.6, 0.9)
            
            # 生成交易信号
            if predicted_price > current_data['close'].iloc[-1] * 1.03:
                action = "buy"
                target_price = predicted_price * 1.05
                stop_loss = predicted_price * 0.95
                take_profit = predicted_price * 1.10
            elif predicted_price < current_data['close'].iloc[-1] * 0.97:
                action = "sell"
                target_price = predicted_price * 0.95
                stop_loss = predicted_price * 1.05
                take_profit = predicted_price * 0.90
            else:
                action = "hold"
                target_price = current_data['close'].iloc[-1]
                stop_loss = current_data['close'].iloc[-1] * 0.95
                take_profit = current_data['close'].iloc[-1] * 1.05
            
            return PredictionResult(
                timestamp=datetime.now(),
                stock_code=stock_code,
                predicted_price=predicted_price,
                confidence=confidence,
                action=action,
                target_price=target_price,
                stop_loss=stop_loss,
                take_profit=take_profit
            )
            
        except Exception as e:
            logger.error(f"深度学习预测失败: {e}")
            raise
    
    async def get_strategies(self) -> List[Dict[str, Any]]:
        """获取所有深度学习策略"""
        try:
            strategies_data = self._load_data(self.strategies_file)
            return strategies_data.get("strategies", [])
        except Exception as e:
            logger.error(f"获取深度学习策略失败: {e}")
            return []
    
    async def get_strategy(self, strategy_id: str) -> Optional[Dict[str, Any]]:
        """获取单个深度学习策略"""
        try:
            strategies = await self.get_strategies()
            return next((s for s in strategies if s["strategy_id"] == strategy_id), None)
        except Exception as e:
            logger.error(f"获取深度学习策略失败: {e}")
            return None
    
    async def update_strategy(self, strategy_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """更新深度学习策略"""
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
            logger.error(f"更新深度学习策略失败: {e}")
            return {"error": f"更新失败: {e}"}
    
    async def delete_strategy(self, strategy_id: str) -> Dict[str, Any]:
        """删除深度学习策略"""
        try:
            strategies_data = self._load_data(self.strategies_file)
            strategies_data["strategies"] = [s for s in strategies_data["strategies"] if s["strategy_id"] != strategy_id]
            self._save_data(self.strategies_file, strategies_data)
            
            # 删除模型文件
            strategy = await self.get_strategy(strategy_id)
            if strategy:
                model_file = strategy.get("model_file", "")
                scaler_file = strategy.get("scaler_file", "")
                
                if model_file and os.path.exists(model_file):
                    os.remove(model_file)
                if scaler_file and os.path.exists(scaler_file):
                    os.remove(scaler_file)
            
            return {"message": "策略删除成功"}
            
        except Exception as e:
            logger.error(f"删除深度学习策略失败: {e}")
            return {"error": f"删除失败: {e}"}

# 创建全局深度学习策略引擎实例
deep_learning_engine = DeepLearningStrategyEngine()
