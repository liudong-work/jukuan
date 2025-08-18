"""
策略服务模块
提供量化策略管理、回测、技术指标计算等功能
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import json
import os
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

class StrategyService:
    """策略服务类"""
    
    def __init__(self):
        self.strategies_file = "data/strategies.json"
        self.backtest_results_file = "data/backtest_results.json"
        self._ensure_data_dir()
        self._init_default_strategies()
    
    def _ensure_data_dir(self):
        """确保数据目录存在"""
        os.makedirs("data", exist_ok=True)
    
    def _init_default_strategies(self):
        """初始化默认策略"""
        if not os.path.exists(self.strategies_file):
            default_strategies = {
                "strategies": [
                    {
                        "id": 1,
                        "name": "MA交叉策略",
                        "type": "ma_cross",
                        "description": "双均线交叉策略，短期均线上穿长期均线买入，下穿卖出",
                        "parameters": {
                            "short_period": 5,
                            "long_period": 20,
                            "stop_loss": 0.05,
                            "take_profit": 0.15
                        },
                        "is_active": True,
                        "created_at": datetime.now().isoformat(),
                        "updated_at": datetime.now().isoformat()
                    },
                    {
                        "id": 2,
                        "name": "KDJ+MACD策略",
                        "type": "kdj_macd",
                        "description": "KDJ和MACD组合策略，双重确认信号",
                        "parameters": {
                            "kdj_period": 9,
                            "macd_fast": 12,
                            "macd_slow": 26,
                            "macd_signal": 9,
                            "stop_loss": 0.08,
                            "take_profit": 0.20
                        },
                        "is_active": True,
                        "created_at": datetime.now().isoformat(),
                        "updated_at": datetime.now().isoformat()
                    },
                    {
                        "id": 3,
                        "name": "RSI超买超卖策略",
                        "type": "rsi_strategy",
                        "description": "RSI超买超卖策略，RSI<30买入，RSI>70卖出",
                        "parameters": {
                            "rsi_period": 14,
                            "oversold": 30,
                            "overbought": 70,
                            "stop_loss": 0.06,
                            "take_profit": 0.12
                        },
                        "is_active": False,
                        "created_at": datetime.now().isoformat(),
                        "updated_at": datetime.now().isoformat()
                    }
                ]
            }
            self._save_data(self.strategies_file, default_strategies)
    
    def _save_data(self, file_path: str, data: Any):
        """保存数据到文件"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
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
    
    async def get_strategies(self) -> List[Dict[str, Any]]:
        """获取策略列表"""
        try:
            strategies_data = self._load_data(self.strategies_file)
            if strategies_data and "strategies" in strategies_data:
                return strategies_data["strategies"]
            return []
        except Exception as e:
            logger.error(f"获取策略列表失败: {e}")
            return []
    
    async def get_strategy(self, strategy_id: int) -> Optional[Dict[str, Any]]:
        """获取单个策略"""
        try:
            strategies = await self.get_strategies()
            for strategy in strategies:
                if strategy["id"] == strategy_id:
                    return strategy
            return None
        except Exception as e:
            logger.error(f"获取策略失败: {e}")
            return None
    
    async def create_strategy(self, 
                            name: str,
                            strategy_type: str,
                            description: str,
                            parameters: Dict[str, Any]) -> Dict[str, Any]:
        """创建新策略"""
        try:
            strategies_data = self._load_data(self.strategies_file) or {"strategies": []}
            strategies = strategies_data["strategies"]
            
            # 生成新ID
            new_id = max([s["id"] for s in strategies], default=0) + 1
            
            new_strategy = {
                "id": new_id,
                "name": name,
                "type": strategy_type,
                "description": description,
                "parameters": parameters,
                "is_active": False,  # 新策略默认不激活
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            strategies.append(new_strategy)
            self._save_data(self.strategies_file, strategies_data)
            
            logger.info(f"策略创建成功: {name}")
            return {
                "message": "策略创建成功",
                "strategy_id": new_id,
                "strategy": new_strategy
            }
            
        except Exception as e:
            logger.error(f"创建策略失败: {e}")
            return {"error": f"创建策略失败: {e}"}
    
    async def update_strategy(self, 
                            strategy_id: int,
                            updates: Dict[str, Any]) -> Dict[str, Any]:
        """更新策略"""
        try:
            strategies_data = self._load_data(self.strategies_file)
            if not strategies_data or "strategies" not in strategies_data:
                return {"error": "策略数据不存在"}
            
            strategies = strategies_data["strategies"]
            for strategy in strategies:
                if strategy["id"] == strategy_id:
                    # 更新字段
                    for key, value in updates.items():
                        if key in strategy:
                            strategy[key] = value
                    
                    strategy["updated_at"] = datetime.now().isoformat()
                    self._save_data(self.strategies_file, strategies_data)
                    
                    logger.info(f"策略更新成功: {strategy_id}")
                    return {
                        "message": "策略更新成功",
                        "strategy": strategy
                    }
            
            return {"error": "策略不存在"}
            
        except Exception as e:
            logger.error(f"更新策略失败: {e}")
            return {"error": f"更新策略失败: {e}"}
    
    async def delete_strategy(self, strategy_id: int) -> Dict[str, Any]:
        """删除策略"""
        try:
            strategies_data = self._load_data(self.strategies_file)
            if not strategies_data or "strategies" not in strategies_data:
                return {"error": "策略数据不存在"}
            
            strategies = strategies_data["strategies"]
            for i, strategy in enumerate(strategies):
                if strategy["id"] == strategy_id:
                    deleted_strategy = strategies.pop(i)
                    self._save_data(self.strategies_file, strategies_data)
                    
                    logger.info(f"策略删除成功: {strategy_id}")
                    return {
                        "message": "策略删除成功",
                        "deleted_strategy": deleted_strategy
                    }
            
            return {"error": "策略不存在"}
            
        except Exception as e:
            logger.error(f"删除策略失败: {e}")
            return {"error": f"删除策略失败: {e}"}
    
    async def run_backtest(self, 
                          strategy_id: int,
                          stock_code: str,
                          start_date: str,
                          end_date: str,
                          initial_capital: float = 100000.0) -> Dict[str, Any]:
        """运行策略回测"""
        try:
            # 获取策略信息
            strategy = await self.get_strategy(strategy_id)
            if not strategy:
                return {"error": "策略不存在"}
            
            # 模拟回测结果（实际项目中需要实现真实的回测逻辑）
            backtest_result = await self._simulate_backtest(
                strategy, stock_code, start_date, end_date, initial_capital
            )
            
            # 保存回测结果
            await self._save_backtest_result(strategy_id, stock_code, backtest_result)
            
            return {
                "message": "回测完成",
                "strategy_id": strategy_id,
                "stock_code": stock_code,
                "results": backtest_result
            }
            
        except Exception as e:
            logger.error(f"运行回测失败: {e}")
            return {"error": f"运行回测失败: {e}"}
    
    async def _simulate_backtest(self, 
                                strategy: Dict[str, Any],
                                stock_code: str,
                                start_date: str,
                                end_date: str,
                                initial_capital: float) -> Dict[str, Any]:
        """模拟回测（实际项目中需要实现真实的回测逻辑）"""
        try:
            # 这里应该实现真实的回测逻辑
            # 包括获取历史数据、计算技术指标、执行策略信号等
            
            # 模拟回测结果
            import random
            random.seed(hash(f"{strategy['id']}{stock_code}{start_date}{end_date}"))
            
            # 模拟收益率
            total_return = random.uniform(-0.2, 0.4)
            final_capital = initial_capital * (1 + total_return)
            
            # 模拟最大回撤
            max_drawdown = random.uniform(0.05, 0.25)
            
            # 模拟交易次数
            trade_count = random.randint(5, 25)
            
            # 模拟胜率
            win_rate = random.uniform(0.4, 0.7)
            
            return {
                "initial_capital": initial_capital,
                "final_capital": final_capital,
                "total_return": total_return,
                "annualized_return": total_return * 252 / 365,  # 年化收益率
                "max_drawdown": max_drawdown,
                "trade_count": trade_count,
                "win_rate": win_rate,
                "sharpe_ratio": random.uniform(0.5, 2.0),
                "start_date": start_date,
                "end_date": end_date,
                "backtest_date": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"模拟回测失败: {e}")
            return {"error": f"模拟回测失败: {e}"}
    
    async def _save_backtest_result(self, 
                                   strategy_id: int,
                                   stock_code: str,
                                   result: Dict[str, Any]):
        """保存回测结果"""
        try:
            backtest_results = self._load_data(self.backtest_results_file) or {"results": []}
            
            # 检查是否已存在相同策略和股票的回测结果
            existing_result = None
            for i, res in enumerate(backtest_results["results"]):
                if res["strategy_id"] == strategy_id and res["stock_code"] == stock_code:
                    existing_result = i
                    break
            
            new_result = {
                "strategy_id": strategy_id,
                "stock_code": stock_code,
                "result": result,
                "created_at": datetime.now().isoformat()
            }
            
            if existing_result is not None:
                backtest_results["results"][existing_result] = new_result
            else:
                backtest_results["results"].append(new_result)
            
            self._save_data(self.backtest_results_file, backtest_results)
            
        except Exception as e:
            logger.error(f"保存回测结果失败: {e}")
    
    async def get_backtest_results(self, strategy_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """获取回测结果"""
        try:
            backtest_results = self._load_data(self.backtest_results_file)
            if not backtest_results or "results" not in backtest_results:
                return []
            
            results = backtest_results["results"]
            if strategy_id:
                results = [r for r in results if r["strategy_id"] == strategy_id]
            
            return results
            
        except Exception as e:
            logger.error(f"获取回测结果失败: {e}")
            return []
    
    async def calculate_technical_indicators(self, 
                                           prices: List[float],
                                           volumes: Optional[List[float]] = None) -> Dict[str, Any]:
        """计算技术指标"""
        try:
            if not prices or len(prices) < 20:
                return {"error": "价格数据不足"}
            
            prices_array = np.array(prices)
            
            indicators = {}
            
            # 移动平均线
            indicators["ma5"] = self._calculate_ma(prices_array, 5)
            indicators["ma10"] = self._calculate_ma(prices_array, 10)
            indicators["ma20"] = self._calculate_ma(prices_array, 20)
            
            # RSI
            indicators["rsi"] = self._calculate_rsi(prices_array, 14)
            
            # MACD
            macd_data = self._calculate_macd(prices_array)
            indicators["macd"] = macd_data["macd"]
            indicators["macd_signal"] = macd_data["signal"]
            indicators["macd_histogram"] = macd_data["histogram"]
            
            # KDJ
            if volumes:
                kdj_data = self._calculate_kdj(prices_array, np.array(volumes))
                indicators["kdj_k"] = kdj_data["k"]
                indicators["kdj_d"] = kdj_data["d"]
                indicators["kdj_j"] = kdj_data["j"]
            
            # 布林带
            bb_data = self._calculate_bollinger_bands(prices_array, 20)
            indicators["bb_upper"] = bb_data["upper"]
            indicators["bb_middle"] = bb_data["middle"]
            indicators["bb_lower"] = bb_data["lower"]
            
            return indicators
            
        except Exception as e:
            logger.error(f"计算技术指标失败: {e}")
            return {"error": f"计算技术指标失败: {e}"}
    
    def _calculate_ma(self, prices: np.ndarray, period: int) -> List[float]:
        """计算移动平均线"""
        ma = []
        for i in range(len(prices)):
            if i < period - 1:
                ma.append(None)
            else:
                ma.append(np.mean(prices[i-period+1:i+1]))
        return ma
    
    def _calculate_rsi(self, prices: np.ndarray, period: int = 14) -> List[float]:
        """计算RSI指标"""
        if len(prices) < period + 1:
            return [None] * len(prices)
        
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        rsi = []
        for i in range(len(prices)):
            if i < period:
                rsi.append(None)
            else:
                avg_gain = np.mean(gains[i-period:i])
                avg_loss = np.mean(losses[i-period:i])
                if avg_loss == 0:
                    rsi.append(100)
                else:
                    rs = avg_gain / avg_loss
                    rsi.append(100 - (100 / (1 + rs)))
        
        return rsi
    
    def _calculate_macd(self, prices: np.ndarray, 
                        fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, List[float]]:
        """计算MACD指标"""
        if len(prices) < slow:
            return {"macd": [0.0] * len(prices), "signal": [0.0] * len(prices), "histogram": [0.0] * len(prices)}
        
        ema_fast = self._calculate_ema(prices, fast)
        ema_slow = self._calculate_ema(prices, slow)
        
        macd_line = []
        for i in range(len(prices)):
            if ema_fast[i] is not None and ema_slow[i] is not None:
                macd_line.append(ema_fast[i] - ema_slow[i])
            else:
                macd_line.append(0.0)
        
        # 过滤掉None值，确保有足够的数据计算信号线
        valid_macd = [x for x in macd_line if x != 0.0]
        if len(valid_macd) < signal:
            signal_line = [0.0] * len(prices)
        else:
            signal_line = self._calculate_ema(np.array(valid_macd), signal)
        
        # 填充信号线
        signal_filled = [0.0] * len(prices)
        signal_idx = 0
        for i in range(len(prices)):
            if macd_line[i] != 0.0:
                if signal_idx < len(signal_line) and signal_line[signal_idx] is not None:
                    signal_filled[i] = signal_line[signal_idx]
                    signal_idx += 1
        
        histogram = []
        for i in range(len(prices)):
            if macd_line[i] != 0.0 and signal_filled[i] != 0.0:
                histogram.append(macd_line[i] - signal_filled[i])
            else:
                histogram.append(0.0)
        
        return {
            "macd": macd_line,
            "signal": signal_filled,
            "histogram": histogram
        }
    
    def _calculate_ema(self, prices: np.ndarray, period: int) -> List[float]:
        """计算指数移动平均线"""
        if len(prices) < period:
            return [0.0] * len(prices)
        
        ema = []
        multiplier = 2 / (period + 1)
        
        # 第一个EMA值使用简单移动平均
        first_ema = np.mean(prices[:period])
        ema.extend([0.0] * (period - 1))
        ema.append(first_ema)
        
        # 计算后续的EMA值
        for i in range(period, len(prices)):
            ema_value = (prices[i] * multiplier) + (ema[i-1] * (1 - multiplier))
            ema.append(ema_value)
        
        return ema
    
    def _calculate_kdj(self, prices: np.ndarray, volumes: np.ndarray, 
                       period: int = 9) -> Dict[str, List[float]]:
        """计算KDJ指标"""
        if len(prices) < period:
            return {"k": [50.0] * len(prices), "d": [50.0] * len(prices), "j": [50.0] * len(prices)}
        
        k_values = []
        d_values = []
        j_values = []
        
        for i in range(len(prices)):
            if i < period - 1:
                k_values.append(50.0)
                d_values.append(50.0)
                j_values.append(50.0)
            else:
                # 计算RSV
                high = np.max(prices[i-period+1:i+1])
                low = np.min(prices[i-period+1:i+1])
                close = prices[i]
                
                if high == low:
                    rsv = 50
                else:
                    rsv = (close - low) / (high - low) * 100
                
                # 计算K值
                if k_values[i-1] == 50.0:  # 初始值
                    k = 50
                else:
                    k = (2/3) * k_values[i-1] + (1/3) * rsv
                k_values.append(k)
                
                # 计算D值
                if d_values[i-1] == 50.0:  # 初始值
                    d = 50
                else:
                    d = (2/3) * d_values[i-1] + (1/3) * k
                d_values.append(d)
                
                # 计算J值
                j = 3 * k - 2 * d
                j_values.append(j)
        
        return {
            "k": k_values,
            "d": d_values,
            "j": j_values
        }
    
    def _calculate_bollinger_bands(self, prices: np.ndarray, period: int = 20, 
                                   std_dev: float = 2) -> Dict[str, List[float]]:
        """计算布林带"""
        if len(prices) < period:
            return {"upper": [prices[0] if len(prices) > 0 else 0.0] * len(prices), 
                    "middle": [prices[0] if len(prices) > 0 else 0.0] * len(prices), 
                    "lower": [prices[0] if len(prices) > 0 else 0.0] * len(prices)}
        
        upper = []
        middle = []
        lower = []
        
        for i in range(len(prices)):
            if i < period - 1:
                # 对于前period-1个点，使用当前价格作为默认值
                upper.append(prices[i])
                middle.append(prices[i])
                lower.append(prices[i])
            else:
                window = prices[i-period+1:i+1]
                ma = np.mean(window)
                std = np.std(window)
                
                middle.append(ma)
                upper.append(ma + std_dev * std)
                lower.append(ma - std_dev * std)
        
        return {
            "upper": upper,
            "middle": middle,
            "lower": lower
        }

# 创建全局策略服务实例
strategy_service = StrategyService()
