"""
策略执行引擎
自动执行策略信号，包含风险管理、仓位管理等功能
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
import json
import os
from dataclasses import dataclass, asdict
import uuid
import numpy as np # Added for RSI and Bollinger signals

# 导入相关服务
try:
    from .enhanced_trading_service import enhanced_trading_service, Order, Position
    from .strategy_service import strategy_service
except ImportError:
    enhanced_trading_service = None
    strategy_service = None

logger = logging.getLogger(__name__)

@dataclass
class StrategySignal:
    """策略信号数据结构"""
    signal_id: str
    strategy_id: int
    strategy_name: str
    stock_code: str
    stock_name: str
    action: str  # buy, sell, hold
    quantity: int
    price: Optional[float]
    confidence: float  # 0.0-1.0
    timestamp: datetime
    metadata: Dict[str, Any]  # 额外信息

@dataclass
class ExecutionResult:
    """执行结果数据结构"""
    signal_id: str
    order_id: Optional[str]
    status: str  # success, failed, partial
    executed_quantity: int
    executed_price: Optional[float]
    commission: float
    slippage: float
    timestamp: datetime
    message: str

class StrategyExecutor:
    """策略执行引擎"""
    
    def __init__(self):
        self.active_strategies = {}  # 活跃策略
        self.signal_queue = asyncio.Queue()  # 信号队列
        self.execution_history = []  # 执行历史
        self.risk_manager = RiskManager()
        self.position_manager = PositionManager()
        
        # 启动执行引擎
        asyncio.create_task(self._start_execution_engine())
        logger.info("策略执行引擎已启动")
    
    async def _start_execution_engine(self):
        """启动执行引擎"""
        while True:
            try:
                # 处理信号队列
                if not self.signal_queue.empty():
                    signal = await self.signal_queue.get()
                    await self._process_signal(signal)
                
                # 检查活跃策略
                await self._check_active_strategies()
                
                # 更新风险管理
                await self._update_risk_metrics()
                
                await asyncio.sleep(10)  # 每10秒检查一次
                
            except Exception as e:
                logger.error(f"执行引擎运行错误: {e}")
                await asyncio.sleep(30)
    
    async def _process_signal(self, signal: StrategySignal):
        """处理策略信号"""
        try:
            logger.info(f"处理策略信号: {signal.signal_id} - {signal.action} {signal.stock_code}")
            
            # 风险检查
            risk_check = await self.risk_manager.check_signal_risk(signal)
            if not risk_check["passed"]:
                logger.warning(f"信号风险检查未通过: {risk_check['reason']}")
                await self._record_execution_result(signal, None, "failed", 0, None, 
                                                 f"风险检查未通过: {risk_check['reason']}")
                return
            
            # 仓位管理
            position_check = await self.position_manager.check_position_limits(signal)
            if not position_check["passed"]:
                logger.warning(f"仓位检查未通过: {position_check['reason']}")
                await self._record_execution_result(signal, None, "failed", 0, None,
                                                 f"仓位检查未通过: {position_check['reason']}")
                return
            
            # 执行交易
            execution_result = await self._execute_signal(signal)
            
            # 记录执行结果
            await self._record_execution_result(
                signal, 
                execution_result.get("order_id"),
                execution_result.get("status", "failed"),
                execution_result.get("executed_quantity", 0),
                execution_result.get("executed_price"),
                execution_result.get("message", "执行完成")
            )
            
            logger.info(f"信号执行完成: {signal.signal_id}")
            
        except Exception as e:
            logger.error(f"处理信号失败: {e}")
            await self._record_execution_result(signal, None, "failed", 0, None, f"执行失败: {e}")
    
    async def _execute_signal(self, signal: StrategySignal) -> Dict[str, Any]:
        """执行策略信号"""
        try:
            if not enhanced_trading_service:
                return {"error": "交易服务不可用"}
            
            # 根据置信度调整数量
            adjusted_quantity = self._adjust_quantity_by_confidence(signal.quantity, signal.confidence)
            
            # 确定订单类型和价格
            order_type, price = self._determine_order_type_and_price(signal)
            
            # 执行交易
            if signal.action == "buy":
                result = await enhanced_trading_service.place_order(
                    user_id=1,
                    stock_code=signal.stock_code,
                    order_type=order_type,
                    quantity=adjusted_quantity,
                    price=price,
                    order_side="buy"
                )
            elif signal.action == "sell":
                result = await enhanced_trading_service.place_order(
                    user_id=1,
                    stock_code=signal.stock_code,
                    order_type=order_type,
                    quantity=adjusted_quantity,
                    price=price,
                    order_side="sell"
                )
            else:
                return {"error": "无效的操作类型"}
            
            if "error" in result:
                return {"status": "failed", "message": result["error"]}
            
            return {
                "status": "success",
                "order_id": result.get("order_id"),
                "executed_quantity": adjusted_quantity,
                "executed_price": price,
                "message": "执行成功"
            }
            
        except Exception as e:
            logger.error(f"执行信号失败: {e}")
            return {"status": "failed", "message": f"执行失败: {e}"}
    
    def _adjust_quantity_by_confidence(self, base_quantity: int, confidence: float) -> int:
        """根据置信度调整数量"""
        if confidence >= 0.9:
            return base_quantity
        elif confidence >= 0.8:
            return int(base_quantity * 0.8)
        elif confidence >= 0.7:
            return int(base_quantity * 0.6)
        elif confidence >= 0.6:
            return int(base_quantity * 0.4)
        else:
            return int(base_quantity * 0.2)
    
    def _determine_order_type_and_price(self, signal: StrategySignal) -> tuple:
        """确定订单类型和价格"""
        if signal.price and signal.price > 0:
            return "limit", signal.price
        else:
            return "market", None
    
    async def _check_active_strategies(self):
        """检查活跃策略"""
        try:
            if not strategy_service:
                return
            
            # 获取所有策略
            strategies = await strategy_service.get_strategies()
            
            for strategy in strategies:
                strategy_id = strategy.get("id")
                if strategy_id and strategy.get("is_active", False):
                    # 检查策略是否需要生成信号
                    await self._generate_strategy_signals(strategy)
                    
        except Exception as e:
            logger.error(f"检查活跃策略失败: {e}")
    
    async def _generate_strategy_signals(self, strategy: Dict[str, Any]):
        """生成策略信号"""
        try:
            strategy_id = strategy.get("id")
            strategy_name = strategy.get("name", "")
            strategy_type = strategy.get("strategy_type", "")
            
            if not strategy_id:
                logger.warning(f"策略ID缺失: {strategy_name}")
                return
            
            # 根据策略类型生成信号
            signals = []
            
            if strategy_type == "ma_cross":
                signals = await self._generate_ma_cross_signals(strategy)
            elif strategy_type == "kdj_macd":
                signals = await self._generate_kdj_macd_signals(strategy)
            elif strategy_type == "rsi":
                signals = await self._generate_rsi_signals(strategy)
            elif strategy_type == "bollinger":
                signals = await self._generate_bollinger_signals(strategy)
            elif strategy_type == "volume":
                signals = await self._generate_volume_signals(strategy)
            else:
                # 默认策略信号生成
                signals = await self._generate_default_signals(strategy)
            
            # 将信号加入队列
            for signal in signals:
                if signal and signal.action in ["buy", "sell"]:
                    await self.signal_queue.put(signal)
                    logger.info(f"策略信号已加入队列: {strategy_name} -> {signal.action} {signal.stock_code}")
                
        except Exception as e:
            logger.error(f"生成策略信号失败: {e}")
    
    async def _generate_ma_cross_signals(self, strategy: Dict[str, Any]) -> List[StrategySignal]:
        """生成均线交叉策略信号"""
        try:
            # 这里应该实现具体的均线交叉逻辑
            # 目前返回模拟信号
            signals = []
            
            # 模拟信号生成
            if datetime.now().hour in [9, 10, 14, 15]:  # 交易时间
                signal = StrategySignal(
                    signal_id=f"signal_{uuid.uuid4().hex[:8]}",
                    strategy_id=strategy.get("id"),
                    strategy_name=strategy.get("name", ""),
                    stock_code="000001.XSHE",  # 平安银行
                    stock_name="平安银行",
                    action="buy",
                    quantity=1000,
                    price=None,
                    confidence=0.8,
                    timestamp=datetime.now(),
                    metadata={"strategy_type": "ma_cross"}
                )
                signals.append(signal)
            
            return signals
            
        except Exception as e:
            logger.error(f"生成均线交叉信号失败: {e}")
            return []
    
    async def _generate_kdj_macd_signals(self, strategy: Dict[str, Any]) -> List[StrategySignal]:
        """生成KDJ+MACD策略信号"""
        try:
            # 这里应该实现具体的KDJ+MACD逻辑
            # 目前返回模拟信号
            signals = []
            
            # 模拟信号生成
            if datetime.now().minute % 30 == 0:  # 每30分钟检查一次
                signal = StrategySignal(
                    signal_id=f"signal_{uuid.uuid4().hex[:8]}",
                    strategy_id=strategy.get("id"),
                    strategy_name=strategy.get("name", ""),
                    stock_code="000002.XSHE",  # 万科A
                    stock_name="万科A",
                    action="sell",
                    quantity=500,
                    price=None,
                    confidence=0.7,
                    timestamp=datetime.now(),
                    metadata={"strategy_type": "kdj_macd"}
                )
                signals.append(signal)
            
            return signals
            
        except Exception as e:
            logger.error(f"生成KDJ+MACD信号失败: {e}")
            return []
    
    async def _generate_rsi_signals(self, strategy: Dict[str, Any]) -> List[StrategySignal]:
        """生成RSI策略信号"""
        try:
            signals = []
            
            # 模拟RSI信号生成
            if datetime.now().minute % 15 == 0:  # 每15分钟检查一次
                # 这里应该实现真实的RSI计算逻辑
                rsi_value = 50 + np.random.normal(0, 20)  # 模拟RSI值
                
                if rsi_value < 30:  # 超卖
                    signal = StrategySignal(
                        signal_id=f"signal_{uuid.uuid4().hex[:8]}",
                        strategy_id=strategy.get("id"),
                        strategy_name=strategy.get("name", ""),
                        stock_code="000001.XSHE",
                        stock_name="平安银行",
                        action="buy",
                        quantity=1000,
                        price=None,
                        confidence=0.8,
                        timestamp=datetime.now(),
                        metadata={"strategy_type": "rsi", "rsi_value": rsi_value}
                    )
                    signals.append(signal)
                elif rsi_value > 70:  # 超买
                    signal = StrategySignal(
                        signal_id=f"signal_{uuid.uuid4().hex[:8]}",
                        strategy_id=strategy.get("id"),
                        strategy_name=strategy.get("name", ""),
                        stock_code="000001.XSHE",
                        stock_name="平安银行",
                        action="sell",
                        quantity=1000,
                        price=None,
                        confidence=0.8,
                        timestamp=datetime.now(),
                        metadata={"strategy_type": "rsi", "rsi_value": rsi_value}
                    )
                    signals.append(signal)
            
            return signals
            
        except Exception as e:
            logger.error(f"生成RSI信号失败: {e}")
            return []
    
    async def _generate_bollinger_signals(self, strategy: Dict[str, Any]) -> List[StrategySignal]:
        """生成布林带策略信号"""
        try:
            signals = []
            
            # 模拟布林带信号生成
            if datetime.now().minute % 20 == 0:  # 每20分钟检查一次
                # 这里应该实现真实的布林带计算逻辑
                bb_position = np.random.uniform(0, 1)  # 模拟布林带位置
                
                if bb_position < 0.1:  # 接近下轨
                    signal = StrategySignal(
                        signal_id=f"signal_{uuid.uuid4().hex[:8]}",
                        strategy_id=strategy.get("id"),
                        strategy_name=strategy.get("name", ""),
                        stock_code="000002.XSHE",
                        stock_name="万科A",
                        action="buy",
                        quantity=800,
                        price=None,
                        confidence=0.75,
                        timestamp=datetime.now(),
                        metadata={"strategy_type": "bollinger", "bb_position": bb_position}
                    )
                    signals.append(signal)
                elif bb_position > 0.9:  # 接近上轨
                    signal = StrategySignal(
                        signal_id=f"signal_{uuid.uuid4().hex[:8]}",
                        strategy_id=strategy.get("id"),
                        strategy_name=strategy.get("name", ""),
                        stock_code="000002.XSHE",
                        stock_name="万科A",
                        action="sell",
                        quantity=800,
                        price=None,
                        confidence=0.75,
                        timestamp=datetime.now(),
                        metadata={"strategy_type": "bollinger", "bb_position": bb_position}
                    )
                    signals.append(signal)
            
            return signals
            
        except Exception as e:
            logger.error(f"生成布林带信号失败: {e}")
            return []
    
    async def _generate_volume_signals(self, strategy: Dict[str, Any]) -> List[StrategySignal]:
        """生成成交量策略信号"""
        try:
            signals = []
            
            # 模拟成交量信号生成
            if datetime.now().minute % 25 == 0:  # 每25分钟检查一次
                # 这里应该实现真实的成交量分析逻辑
                volume_ratio = np.random.uniform(0.5, 2.0)  # 模拟成交量比率
                
                if volume_ratio > 1.5:  # 放量
                    signal = StrategySignal(
                        signal_id=f"signal_{uuid.uuid4().hex[:8]}",
                        strategy_id=strategy.get("id"),
                        strategy_name=strategy.get("name", ""),
                        stock_code="000858.XSHE",
                        stock_name="五粮液",
                        action="buy",
                        quantity=600,
                        price=None,
                        confidence=0.7,
                        timestamp=datetime.now(),
                        metadata={"strategy_type": "volume", "volume_ratio": volume_ratio}
                    )
                    signals.append(signal)
            
            return signals
            
        except Exception as e:
            logger.error(f"生成成交量信号失败: {e}")
            return []
    
    async def _generate_default_signals(self, strategy: Dict[str, Any]) -> List[StrategySignal]:
        """生成默认策略信号"""
        try:
            signals = []
            
            # 默认信号生成逻辑
            if datetime.now().hour in [9, 10, 14, 15] and datetime.now().minute % 30 == 0:
                signal = StrategySignal(
                    signal_id=f"signal_{uuid.uuid4().hex[:8]}",
                    strategy_id=strategy.get("id"),
                    strategy_name=strategy.get("name", ""),
                    stock_code="000001.XSHE",
                    stock_name="平安银行",
                    action="hold",
                    quantity=0,
                    price=None,
                    confidence=0.5,
                    timestamp=datetime.now(),
                    metadata={"strategy_type": "default", "note": "默认策略，建议观望"}
                )
                signals.append(signal)
            
            return signals
            
        except Exception as e:
            logger.error(f"生成默认策略信号失败: {e}")
            return []
    
    async def _update_risk_metrics(self):
        """更新风险指标"""
        try:
            if not enhanced_trading_service:
                return
            
            # 获取风险指标
            risk_metrics = await enhanced_trading_service.get_risk_metrics()
            
            # 检查风险预警
            await self.risk_manager.check_risk_alerts(risk_metrics)
            
        except Exception as e:
            logger.error(f"更新风险指标失败: {e}")
    
    async def _record_execution_result(self, signal: StrategySignal, order_id: Optional[str],
                                     status: str, executed_quantity: int, executed_price: Optional[float],
                                     message: str):
        """记录执行结果"""
        try:
            result = ExecutionResult(
                signal_id=signal.signal_id,
                order_id=order_id,
                status=status,
                executed_quantity=executed_quantity,
                executed_price=executed_price,
                commission=0.0,  # 手续费
                slippage=0.0,    # 滑点
                timestamp=datetime.now(),
                message=message
            )
            
            self.execution_history.append(asdict(result))
            
            # 保存到文件
            await self._save_execution_history()
            
        except Exception as e:
            logger.error(f"记录执行结果失败: {e}")
    
    async def _save_execution_history(self):
        """保存执行历史"""
        try:
            history_file = "data/execution_history.json"
            os.makedirs("data", exist_ok=True)
            
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(self.execution_history, f, ensure_ascii=False, indent=2, default=str)
                
        except Exception as e:
            logger.error(f"保存执行历史失败: {e}")
    
    async def add_signal(self, signal: StrategySignal):
        """添加策略信号到队列"""
        try:
            await self.signal_queue.put(signal)
            logger.info(f"信号已添加到队列: {signal.signal_id}")
        except Exception as e:
            logger.error(f"添加信号到队列失败: {e}")
    
    async def get_execution_status(self) -> Dict[str, Any]:
        """获取执行状态"""
        try:
            return {
                "queue_size": self.signal_queue.qsize(),
                "active_strategies": len(self.active_strategies),
                "execution_history_count": len(self.execution_history),
                "last_execution": self.execution_history[-1] if self.execution_history else None,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"获取执行状态失败: {e}")
            return {"error": f"获取执行状态失败: {e}"}
    
    async def stop_strategy(self, strategy_id: int):
        """停止策略"""
        try:
            if strategy_id in self.active_strategies:
                del self.active_strategies[strategy_id]
                logger.info(f"策略已停止: {strategy_id}")
        except Exception as e:
            logger.error(f"停止策略失败: {e}")
    
    async def start_strategy(self, strategy_id: int):
        """启动策略"""
        try:
            if not strategy_service:
                return {"error": "策略服务不可用"}
            
            strategy = await strategy_service.get_strategy(strategy_id)
            if strategy:
                self.active_strategies[strategy_id] = strategy
                logger.info(f"策略已启动: {strategy_id}")
                return {"message": "策略启动成功"}
            else:
                return {"error": "策略不存在"}
                
        except Exception as e:
            logger.error(f"启动策略失败: {e}")
            return {"error": f"启动策略失败: {e}"}

class RiskManager:
    """风险管理器"""
    
    def __init__(self):
        self.risk_limits = {
            "max_daily_loss": 0.05,      # 日最大亏损5%
            "max_drawdown": 0.15,        # 最大回撤15%
            "max_position_concentration": 0.3,  # 单只股票最大集中度30%
            "max_sector_concentration": 0.5,    # 单个行业最大集中度50%
            "min_cash_ratio": 0.1,       # 最小现金比例10%
        }
        self.risk_alerts = []
    
    async def check_signal_risk(self, signal: StrategySignal) -> Dict[str, Any]:
        """检查信号风险"""
        try:
            # 检查置信度
            if signal.confidence < 0.5:
                return {"passed": False, "reason": "置信度过低"}
            
            # 检查数量合理性
            if signal.quantity <= 0 or signal.quantity > 100000:
                return {"passed": False, "reason": "数量不合理"}
            
            # 其他风险检查...
            
            return {"passed": True, "reason": "通过"}
            
        except Exception as e:
            logger.error(f"检查信号风险失败: {e}")
            return {"passed": False, "reason": f"风险检查失败: {e}"}
    
    async def check_risk_alerts(self, risk_metrics: Dict[str, Any]):
        """检查风险预警"""
        try:
            # 检查最大回撤
            if risk_metrics.get("max_drawdown", 0) > self.risk_limits["max_drawdown"]:
                await self._trigger_risk_alert("最大回撤超限", risk_metrics)
            
            # 检查现金比例
            if risk_metrics.get("cash_ratio", 1) < self.risk_limits["min_cash_ratio"]:
                await self._trigger_risk_alert("现金比例过低", risk_metrics)
            
            # 其他风险检查...
            
        except Exception as e:
            logger.error(f"检查风险预警失败: {e}")
    
    async def _trigger_risk_alert(self, alert_type: str, metrics: Dict[str, Any]):
        """触发风险预警"""
        try:
            alert = {
                "type": alert_type,
                "timestamp": datetime.now().isoformat(),
                "metrics": metrics,
                "severity": "high" if alert_type in ["最大回撤超限", "现金比例过低"] else "medium"
            }
            
            self.risk_alerts.append(alert)
            logger.warning(f"风险预警: {alert_type}")
            
            # 这里可以添加通知逻辑（邮件、短信等）
            
        except Exception as e:
            logger.error(f"触发风险预警失败: {e}")

class PositionManager:
    """仓位管理器"""
    
    def __init__(self):
        self.position_limits = {
            "max_single_position": 0.2,  # 单只股票最大仓位20%
            "max_total_positions": 0.8,  # 总仓位最大80%
            "min_position_size": 0.01,   # 最小仓位1%
        }
    
    async def check_position_limits(self, signal: StrategySignal) -> Dict[str, Any]:
        """检查仓位限制"""
        try:
            # 这里应该实现具体的仓位检查逻辑
            # 目前返回通过
            
            return {"passed": True, "reason": "通过"}
            
        except Exception as e:
            logger.error(f"检查仓位限制失败: {e}")
            return {"passed": False, "reason": f"仓位检查失败: {e}"}

# 创建全局策略执行引擎实例
strategy_executor = StrategyExecutor()
