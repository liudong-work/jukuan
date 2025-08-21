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
from dataclasses import dataclass, asdict
from enum import Enum
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)

class StrategyType(Enum):
    """策略类型枚举"""
    MA_CROSS = "ma_cross"
    KDJ_MACD = "kdj_macd"
    RSI_STRATEGY = "rsi_strategy"
    BOLLINGER_BANDS = "bollinger_bands"
    VOLUME_BREAKOUT = "volume_breakout"
    MOMENTUM = "momentum"
    MEAN_REVERSION = "mean_reversion"
    ARBITRAGE = "arbitrage"
    PAIRS_TRADING = "pairs_trading"
    GRID_TRADING = "grid_trading"

class StrategyStatus(Enum):
    """策略状态枚举"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PAUSED = "paused"
    ERROR = "error"
    OPTIMIZING = "optimizing"

@dataclass
class StrategyPerformance:
    """策略性能数据类"""
    total_return: float
    annualized_return: float
    max_drawdown: float
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    win_rate: float
    profit_factor: float
    trade_count: int
    avg_trade_return: float
    max_consecutive_losses: int
    volatility: float
    beta: float
    alpha: float

@dataclass
class StrategyValidation:
    """策略验证结果"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    risk_score: float
    complexity_score: float

class StrategyService:
    """策略服务类"""
    
    def __init__(self):
        self.strategies_file = "data/strategies.json"
        self.backtest_results_file = "data/backtest_results.json"
        self.strategy_performance_file = "data/strategy_performance.json"
        self.strategy_combinations_file = "data/strategy_combinations.json"
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
                        "type": StrategyType.MA_CROSS.value,
                        "description": "双均线交叉策略，短期均线上穿长期均线买入，下穿卖出",
                        "parameters": {
                            "short_period": 5,
                            "long_period": 20,
                            "stop_loss": 0.05,
                            "take_profit": 0.15,
                            "position_size": 0.1
                        },
                        "status": StrategyStatus.ACTIVE.value,
                        "risk_level": "medium",
                        "expected_return": 0.15,
                        "max_drawdown": 0.20,
                        "created_at": datetime.now().isoformat(),
                        "updated_at": datetime.now().isoformat()
                    },
                    {
                        "id": 2,
                        "name": "KDJ+MACD策略",
                        "type": StrategyType.KDJ_MACD.value,
                        "description": "KDJ和MACD组合策略，双重确认信号",
                        "parameters": {
                            "kdj_period": 9,
                            "macd_fast": 12,
                            "macd_slow": 26,
                            "macd_signal": 9,
                            "stop_loss": 0.08,
                            "take_profit": 0.20,
                            "position_size": 0.15
                        },
                        "status": StrategyStatus.ACTIVE.value,
                        "risk_level": "high",
                        "expected_return": 0.25,
                        "max_drawdown": 0.30,
                        "created_at": datetime.now().isoformat(),
                        "updated_at": datetime.now().isoformat()
                    },
                    {
                        "id": 3,
                        "name": "RSI超买超卖策略",
                        "type": StrategyType.RSI_STRATEGY.value,
                        "description": "RSI超买超卖策略，RSI<30买入，RSI>70卖出",
                        "parameters": {
                            "rsi_period": 14,
                            "oversold": 30,
                            "overbought": 70,
                            "stop_loss": 0.06,
                            "take_profit": 0.12,
                            "position_size": 0.08
                        },
                        "status": StrategyStatus.INACTIVE.value,
                        "risk_level": "low",
                        "expected_return": 0.10,
                        "max_drawdown": 0.15,
                        "created_at": datetime.now().isoformat(),
                        "updated_at": datetime.now().isoformat()
                    },
                    {
                        "id": 4,
                        "name": "布林带突破策略",
                        "type": StrategyType.BOLLINGER_BANDS.value,
                        "description": "价格突破布林带上轨买入，跌破下轨卖出",
                        "parameters": {
                            "period": 20,
                            "std_dev": 2.0,
                            "stop_loss": 0.05,
                            "take_profit": 0.15,
                            "position_size": 0.12
                        },
                        "status": StrategyStatus.ACTIVE.value,
                        "risk_level": "medium",
                        "expected_return": 0.18,
                        "max_drawdown": 0.22,
                        "created_at": datetime.now().isoformat(),
                        "updated_at": datetime.now().isoformat()
                    },
                    {
                        "id": 5,
                        "name": "放量突破策略",
                        "type": StrategyType.VOLUME_BREAKOUT.value,
                        "description": "成交量放大突破关键价位时买入",
                        "parameters": {
                            "volume_multiplier": 2.0,
                            "price_threshold": 0.02,
                            "stop_loss": 0.04,
                            "take_profit": 0.12,
                            "position_size": 0.10
                        },
                        "status": StrategyStatus.ACTIVE.value,
                        "risk_level": "high",
                        "expected_return": 0.22,
                        "max_drawdown": 0.25,
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

    async def validate_strategy(self, strategy_type: str, parameters: Dict[str, Any]) -> StrategyValidation:
        """验证策略参数"""
        errors = []
        warnings = []
        risk_score = 0.0
        complexity_score = 0.0
        
        try:
            # 基础参数验证
            if not parameters:
                errors.append("策略参数不能为空")
                return StrategyValidation(False, errors, warnings, 1.0, 0.0)
            
            # 根据策略类型进行特定验证
            if strategy_type == StrategyType.MA_CROSS.value:
                validation_result = self._validate_ma_cross(parameters)
            elif strategy_type == StrategyType.KDJ_MACD.value:
                validation_result = self._validate_kdj_macd(parameters)
            elif strategy_type == StrategyType.RSI_STRATEGY.value:
                validation_result = self._validate_rsi_strategy(parameters)
            elif strategy_type == StrategyType.BOLLINGER_BANDS.value:
                validation_result = self._validate_bollinger_bands(parameters)
            elif strategy_type == StrategyType.VOLUME_BREAKOUT.value:
                validation_result = self._validate_volume_breakout(parameters)
            else:
                errors.append(f"不支持的策略类型: {strategy_type}")
                return StrategyValidation(False, errors, warnings, 1.0, 0.0)
            
            errors.extend(validation_result.get("errors", []))
            warnings.extend(validation_result.get("warnings", []))
            risk_score = validation_result.get("risk_score", 0.5)
            complexity_score = validation_result.get("complexity_score", 0.5)
            
            # 通用参数验证
            if "stop_loss" in parameters:
                if parameters["stop_loss"] <= 0 or parameters["stop_loss"] > 0.5:
                    errors.append("止损比例应在0-50%之间")
            
            if "take_profit" in parameters:
                if parameters["take_profit"] <= 0 or parameters["take_profit"] > 1.0:
                    errors.append("止盈比例应在0-100%之间")
            
            if "position_size" in parameters:
                if parameters["position_size"] <= 0 or parameters["position_size"] > 1.0:
                    errors.append("仓位大小应在0-100%之间")
            
            is_valid = len(errors) == 0
            
            return StrategyValidation(is_valid, errors, warnings, risk_score, complexity_score)
            
        except Exception as e:
            logger.error(f"策略验证失败: {e}")
            errors.append(f"策略验证异常: {e}")
            return StrategyValidation(False, errors, warnings, 1.0, 0.0)
    
    def _validate_ma_cross(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """验证MA交叉策略参数"""
        errors = []
        warnings = []
        risk_score = 0.3
        complexity_score = 0.2
        
        if "short_period" not in parameters or "long_period" not in parameters:
            errors.append("MA交叉策略需要短期和长期周期参数")
        else:
            short_period = parameters["short_period"]
            long_period = parameters["long_period"]
            
            if short_period >= long_period:
                errors.append("短期周期必须小于长期周期")
            
            if short_period < 2 or long_period > 200:
                warnings.append("周期参数可能过大或过小")
            
            if long_period - short_period < 5:
                warnings.append("长短周期差异过小，可能产生过多信号")
        
        return {"errors": errors, "warnings": warnings, "risk_score": risk_score, "complexity_score": complexity_score}
    
    def _validate_kdj_macd(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """验证KDJ+MACD策略参数"""
        errors = []
        warnings = []
        risk_score = 0.7
        complexity_score = 0.6
        
        required_params = ["kdj_period", "macd_fast", "macd_slow", "macd_signal"]
        for param in required_params:
            if param not in parameters:
                errors.append(f"KDJ+MACD策略需要{param}参数")
        
        if "kdj_period" in parameters and parameters["kdj_period"] < 5:
            warnings.append("KDJ周期过小可能产生噪声信号")
        
        return {"errors": errors, "warnings": warnings, "risk_score": risk_score, "complexity_score": complexity_score}
    
    def _validate_rsi_strategy(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """验证RSI策略参数"""
        errors = []
        warnings = []
        risk_score = 0.4
        complexity_score = 0.3
        
        if "rsi_period" not in parameters:
            errors.append("RSI策略需要周期参数")
        elif parameters["rsi_period"] < 5 or parameters["rsi_period"] > 50:
            warnings.append("RSI周期应在5-50之间")
        
        if "oversold" in parameters and "overbought" in parameters:
            oversold = parameters["oversold"]
            overbought = parameters["overbought"]
            if oversold >= overbought:
                errors.append("超卖值必须小于超买值")
            if oversold < 10 or overbought > 90:
                warnings.append("超买超卖值应在10-90之间")
        
        return {"errors": errors, "warnings": warnings, "risk_score": risk_score, "complexity_score": complexity_score}
    
    def _validate_bollinger_bands(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """验证布林带策略参数"""
        errors = []
        warnings = []
        risk_score = 0.5
        complexity_score = 0.4
        
        if "period" not in parameters:
            errors.append("布林带策略需要周期参数")
        elif parameters["period"] < 10 or parameters["period"] > 100:
            warnings.append("布林带周期应在10-100之间")
        
        if "std_dev" in parameters:
            if parameters["std_dev"] < 1.0 or parameters["std_dev"] > 3.0:
                warnings.append("标准差倍数应在1.0-3.0之间")
        
        return {"errors": errors, "warnings": warnings, "risk_score": risk_score, "complexity_score": complexity_score}
    
    def _validate_volume_breakout(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """验证放量突破策略参数"""
        errors = []
        warnings = []
        risk_score = 0.8
        complexity_score = 0.5
        
        if "volume_multiplier" not in parameters:
            errors.append("放量突破策略需要成交量倍数参数")
        elif parameters["volume_multiplier"] < 1.5:
            warnings.append("成交量倍数过小可能产生假信号")
        
        if "price_threshold" in parameters:
            if parameters["price_threshold"] < 0.01 or parameters["price_threshold"] > 0.10:
                warnings.append("价格阈值应在1%-10%之间")
        
        return {"errors": errors, "warnings": warnings, "risk_score": risk_score, "complexity_score": complexity_score}

    async def optimize_strategy(self, strategy_id: int, optimization_params: Dict[str, Any]) -> Dict[str, Any]:
        """优化策略参数"""
        try:
            strategy = await self.get_strategy(strategy_id)
            if not strategy:
                return {"error": "策略不存在"}
            
            # 获取优化范围
            param_ranges = optimization_params.get("param_ranges", {})
            optimization_target = optimization_params.get("target", "sharpe_ratio")
            iterations = optimization_params.get("iterations", 100)
            
            best_params = strategy["parameters"].copy()
            best_performance = 0.0
            
            # 网格搜索优化
            for i in range(iterations):
                # 生成随机参数组合
                test_params = self._generate_test_params(strategy["parameters"], param_ranges)
                
                # 运行回测
                backtest_result = await self._simulate_backtest(
                    {**strategy, "parameters": test_params},
                    "000001.XSHE",  # 测试股票
                    "2024-01-01",
                    "2024-12-31",
                    100000.0
                )
                
                if "error" not in backtest_result:
                    performance = backtest_result.get(optimization_target, 0.0)
                    if performance > best_performance:
                        best_performance = performance
                        best_params = test_params.copy()
            
            # 更新策略参数
            await self.update_strategy(strategy_id, {"parameters": best_params})
            
            return {
                "message": "策略优化完成",
                "original_params": strategy["parameters"],
                "optimized_params": best_params,
                "performance_improvement": best_performance,
                "optimization_target": optimization_target
            }
            
        except Exception as e:
            logger.error(f"策略优化失败: {e}")
            return {"error": f"策略优化失败: {e}"}
    
    def _generate_test_params(self, base_params: Dict[str, Any], param_ranges: Dict[str, Any]) -> Dict[str, Any]:
        """生成测试参数"""
        test_params = base_params.copy()
        
        for param, range_info in param_ranges.items():
            if param in test_params:
                if isinstance(range_info, dict):
                    min_val = range_info.get("min", test_params[param] * 0.5)
                    max_val = range_info.get("max", test_params[param] * 1.5)
                    step = range_info.get("step", (max_val - min_val) / 10)
                    
                    # 随机选择参数值
                    import random
                    test_params[param] = round(random.uniform(min_val, max_val) / step) * step
                elif isinstance(range_info, list):
                    import random
                    test_params[param] = random.choice(range_info)
        
        return test_params

    async def create_strategy_combination(self, name: str, strategy_ids: List[int], 
                                        allocation: List[float]) -> Dict[str, Any]:
        """创建策略组合"""
        try:
            logger.info(f"创建策略组合: name={name}, strategy_ids={strategy_ids}, allocation={allocation}")
            
            if len(strategy_ids) != len(allocation):
                return {"error": "策略ID和分配比例数量不匹配"}
            
            if abs(sum(allocation) - 1.0) > 0.01:
                return {"error": f"分配比例总和必须为100%，当前总和: {sum(allocation)}"}
            
            # 验证策略是否存在
            strategies = []
            for strategy_id in strategy_ids:
                strategy = await self.get_strategy(strategy_id)
                if not strategy:
                    return {"error": f"策略ID {strategy_id} 不存在"}
                strategies.append(strategy)
            
            # 加载现有组合
            combinations_data = self._load_data(self.strategy_combinations_file) or {"combinations": []}
            combinations = combinations_data["combinations"]
            
            # 生成新ID
            new_id = max([c["id"] for c in combinations], default=0) + 1
            
            new_combination = {
                "id": new_id,
                "name": name,
                "strategies": strategy_ids,
                "allocation": allocation,
                "status": "active",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            combinations.append(new_combination)
            self._save_data(self.strategy_combinations_file, combinations_data)
            
            logger.info(f"策略组合创建成功: {name}")
            return {
                "message": "策略组合创建成功",
                "combination_id": new_id,
                "combination": new_combination
            }
            
        except Exception as e:
            logger.error(f"创建策略组合失败: {e}")
            return {"error": f"创建策略组合失败: {e}"}
    
    async def get_strategy_combinations(self) -> List[Dict[str, Any]]:
        """获取策略组合列表"""
        try:
            combinations_data = self._load_data(self.strategy_combinations_file)
            if combinations_data and "combinations" in combinations_data:
                return combinations_data["combinations"]
            return []
        except Exception as e:
            logger.error(f"获取策略组合失败: {e}")
            return []
    
    async def run_combination_backtest(self, combination_id: int, 
                                     stock_codes: List[str],
                                     start_date: str,
                                     end_date: str,
                                     initial_capital: float = 100000.0) -> Dict[str, Any]:
        """运行策略组合回测"""
        try:
            combinations = await self.get_strategy_combinations()
            combination = next((c for c in combinations if c["id"] == combination_id), None)
            
            if not combination:
                return {"error": "策略组合不存在"}
            
            # 运行各策略回测
            individual_results = []
            total_return = 0.0
            total_risk = 0.0
            
            for i, strategy_id in enumerate(combination["strategies"]):
                allocation = combination["allocation"][i]
                strategy_capital = initial_capital * allocation
                
                strategy = await self.get_strategy(strategy_id)
                if strategy:
                    result = await self._simulate_backtest(
                        strategy, stock_codes[i % len(stock_codes)], start_date, end_date, strategy_capital
                    )
                    
                    if "error" not in result:
                        weighted_return = result["total_return"] * allocation
                        weighted_risk = result["max_drawdown"] * allocation
                        
                        total_return += weighted_return
                        total_risk += weighted_risk
                        
                        individual_results.append({
                            "strategy_id": strategy_id,
                            "strategy_name": strategy["name"],
                            "allocation": allocation,
                            "result": result,
                            "weighted_return": weighted_return,
                            "weighted_risk": weighted_risk
                        })
            
            # 计算组合整体表现
            combination_result = {
                "total_return": total_return,
                "annualized_return": total_return * 252 / 365,
                "max_drawdown": total_risk,
                "sharpe_ratio": total_return / (total_risk + 0.01),  # 避免除零
                "individual_results": individual_results,
                "start_date": start_date,
                "end_date": end_date,
                "backtest_date": datetime.now().isoformat()
            }
            
            return {
                "message": "组合回测完成",
                "combination_id": combination_id,
                "results": combination_result
            }
            
        except Exception as e:
            logger.error(f"组合回测失败: {e}")
            return {"error": f"组合回测失败: {e}"}

    async def get_strategy_performance(self, strategy_id: int) -> Optional[StrategyPerformance]:
        """获取策略性能指标"""
        try:
            # 获取回测结果
            backtest_results = await self.get_backtest_results(strategy_id)
            if not backtest_results:
                return None
            
            # 计算综合性能指标
            total_return = 0.0
            max_drawdown = 0.0
            trade_count = 0
            win_count = 0
            
            for result in backtest_results:
                if "result" in result:
                    result_data = result["result"]
                    total_return += result_data.get("total_return", 0.0)
                    max_drawdown = max(max_drawdown, result_data.get("max_drawdown", 0.0))
                    trade_count += result_data.get("trade_count", 0)
                    if result_data.get("total_return", 0.0) > 0:
                        win_count += 1
            
            if not backtest_results:
                return None
            
            avg_return = total_return / len(backtest_results)
            win_rate = win_count / len(backtest_results) if backtest_results else 0.0
            
            # 计算其他指标
            sharpe_ratio = avg_return / (max_drawdown + 0.01)
            sortino_ratio = avg_return / (max_drawdown + 0.01)  # 简化计算
            calmar_ratio = avg_return / (max_drawdown + 0.01)  # 简化计算
            
            return StrategyPerformance(
                total_return=avg_return,
                annualized_return=avg_return * 252 / 365,
                max_drawdown=max_drawdown,
                sharpe_ratio=sharpe_ratio,
                sortino_ratio=sortino_ratio,
                calmar_ratio=calmar_ratio,
                win_rate=win_rate,
                profit_factor=win_rate / (1 - win_rate) if win_rate < 1 else 10.0,
                trade_count=trade_count,
                avg_trade_return=avg_return / max(trade_count, 1),
                max_consecutive_losses=0,  # 需要更复杂的计算
                volatility=max_drawdown,  # 简化计算
                beta=1.0,  # 需要市场数据计算
                alpha=avg_return  # 简化计算
            )
            
        except Exception as e:
            logger.error(f"获取策略性能失败: {e}")
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
            # 验证策略参数
            validation = await self.validate_strategy(strategy_type, parameters)
            if not validation.is_valid:
                return {"error": f"策略验证失败: {'; '.join(validation.errors)}"}
            
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
                "status": StrategyStatus.INACTIVE.value,  # 新策略默认不激活
                "risk_level": "medium",
                "expected_return": 0.15,
                "max_drawdown": 0.20,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            strategies.append(new_strategy)
            self._save_data(self.strategies_file, strategies_data)
            
            logger.info(f"策略创建成功: {name}")
            return {
                "message": "策略创建成功",
                "strategy_id": new_id,
                "strategy": new_strategy,
                "validation": asdict(validation)
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
