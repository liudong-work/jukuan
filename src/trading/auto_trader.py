#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
自动交易模块
实现策略自动执行和交易功能
"""

import logging
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import pandas as pd

class OrderType(Enum):
    """订单类型"""
    BUY = "buy"      # 买入
    SELL = "sell"    # 卖出
    HOLD = "hold"    # 持有

class OrderStatus(Enum):
    """订单状态"""
    PENDING = "pending"      # 待执行
    EXECUTED = "executed"    # 已执行
    CANCELLED = "cancelled"  # 已取消
    FAILED = "failed"        # 执行失败

@dataclass
class TradeSignal:
    """交易信号"""
    stock_code: str          # 股票代码
    signal_type: OrderType   # 信号类型
    price: float             # 目标价格
    quantity: int            # 数量
    strategy: str            # 策略名称
    timestamp: datetime      # 信号时间
    confidence: float        # 信号置信度 (0-1)
    stop_loss: Optional[float] = None    # 止损价
    take_profit: Optional[float] = None  # 止盈价

@dataclass
class Order:
    """交易订单"""
    order_id: str            # 订单ID
    stock_code: str          # 股票代码
    order_type: OrderType    # 订单类型
    price: float             # 价格
    quantity: int            # 数量
    status: OrderStatus      # 订单状态
    timestamp: datetime      # 创建时间
    executed_time: Optional[datetime] = None  # 执行时间
    executed_price: Optional[float] = None    # 执行价格

class AutoTrader:
    """自动交易器"""
    
    def __init__(self, data_provider, strategy_manager, risk_manager=None):
        """
        初始化自动交易器
        
        Args:
            data_provider: 数据提供者
            strategy_manager: 策略管理器
            risk_manager: 风险管理器
        """
        self.data_provider = data_provider
        self.strategy_manager = strategy_manager
        self.risk_manager = risk_manager
        
        # 交易状态
        self.is_running = False
        self.trading_thread = None
        
        # 订单管理
        self.orders: Dict[str, Order] = {}
        self.positions: Dict[str, Dict] = {}  # 持仓信息
        
        # 配置参数
        self.config = {
            'max_position_size': 100000,      # 最大持仓金额
            'max_single_position': 20000,     # 单只股票最大持仓
            'stop_loss_ratio': 0.05,          # 止损比例
            'take_profit_ratio': 0.15,        # 止盈比例
            'min_confidence': 0.7,            # 最小信号置信度
            'check_interval': 60,             # 检查间隔(秒)
            'auto_execute': True,             # 自动执行
            'paper_trading': True             # 模拟交易
        }
        
        # 日志
        self.logger = logging.getLogger(__name__)
        
    def start_trading(self):
        """启动自动交易"""
        if self.is_running:
            self.logger.warning("自动交易已在运行中")
            return
            
        self.is_running = True
        self.trading_thread = threading.Thread(target=self._trading_loop, daemon=True)
        self.trading_thread.start()
        self.logger.info("自动交易已启动")
        
    def stop_trading(self):
        """停止自动交易"""
        self.is_running = False
        if self.trading_thread:
            self.trading_thread.join(timeout=5)
        self.logger.info("自动交易已停止")
        
    def _trading_loop(self):
        """交易主循环"""
        while self.is_running:
            try:
                # 1. 获取市场数据
                market_data = self._get_market_data()
                
                # 2. 执行策略分析
                signals = self._generate_signals(market_data)
                
                # 3. 风险管理
                filtered_signals = self._risk_management(signals)
                
                # 4. 执行交易
                if self.config['auto_execute']:
                    self._execute_signals(filtered_signals)
                
                # 5. 更新持仓
                self._update_positions()
                
                # 6. 检查止损止盈
                self._check_stop_orders()
                
                # 等待下次检查
                time.sleep(self.config['check_interval'])
                
            except Exception as e:
                self.logger.error(f"交易循环出错: {e}")
                time.sleep(10)  # 出错后等待10秒再继续
                
    def _get_market_data(self) -> Dict:
        """获取市场数据"""
        try:
            # 获取关注的股票数据
            watchlist = self._get_watchlist()
            market_data = {}
            
            for stock_code in watchlist:
                # 获取实时数据（这里用日线数据模拟）
                data = self.data_provider.get_daily_data(
                    stock_code, 
                    start_date=(datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
                    end_date=datetime.now().strftime('%Y-%m-%d')
                )
                
                if not data.empty:
                    market_data[stock_code] = data
                    
            return market_data
            
        except Exception as e:
            self.logger.error(f"获取市场数据失败: {e}")
            return {}
            
    def _generate_signals(self, market_data: Dict) -> List[TradeSignal]:
        """生成交易信号"""
        signals = []
        
        try:
            for stock_code, data in market_data.items():
                # 使用策略管理器生成信号
                stock_signals = self.strategy_manager.analyze_stock(stock_code, data)
                
                for signal in stock_signals:
                    # 转换为交易信号
                    trade_signal = TradeSignal(
                        stock_code=stock_code,
                        signal_type=signal['type'],
                        price=signal['price'],
                        quantity=signal['quantity'],
                        strategy=signal['strategy'],
                        timestamp=datetime.now(),
                        confidence=signal['confidence'],
                        stop_loss=signal.get('stop_loss'),
                        take_profit=signal.get('take_profit')
                    )
                    signals.append(trade_signal)
                    
        except Exception as e:
            self.logger.error(f"生成交易信号失败: {e}")
            
        return signals
        
    def _risk_management(self, signals: List[TradeSignal]) -> List[TradeSignal]:
        """风险管理"""
        filtered_signals = []
        
        for signal in signals:
            # 1. 置信度过滤
            if signal.confidence < self.config['min_confidence']:
                continue
                
            # 2. 持仓限制检查
            if not self._check_position_limit(signal):
                continue
                
            # 3. 资金检查
            if not self._check_capital(signal):
                continue
                
            # 4. 风险检查
            if self.risk_manager and not self.risk_manager.validate_signal(signal):
                continue
                
            filtered_signals.append(signal)
            
        return filtered_signals
        
    def _check_position_limit(self, signal: TradeSignal) -> bool:
        """检查持仓限制"""
        current_position = self.positions.get(signal.stock_code, {})
        current_value = current_position.get('value', 0)
        
        # 检查单只股票最大持仓
        if current_value + (signal.price * signal.quantity) > self.config['max_single_position']:
            self.logger.warning(f"{signal.stock_code} 超过单只股票最大持仓限制")
            return False
            
        return True
        
    def _check_capital(self, signal: TradeSignal) -> bool:
        """检查资金"""
        # 这里应该检查实际可用资金
        # 暂时返回True
        return True
        
    def _execute_signals(self, signals: List[TradeSignal]):
        """执行交易信号"""
        for signal in signals:
            try:
                # 创建订单
                order = self._create_order(signal)
                
                if self.config['paper_trading']:
                    # 模拟交易
                    self._execute_paper_order(order)
                else:
                    # 实盘交易
                    self._execute_real_order(order)
                    
            except Exception as e:
                self.logger.error(f"执行信号失败 {signal.stock_code}: {e}")
                
    def _create_order(self, signal: TradeSignal) -> Order:
        """创建交易订单"""
        order_id = f"order_{int(time.time() * 1000)}"
        
        order = Order(
            order_id=order_id,
            stock_code=signal.stock_code,
            order_type=signal.signal_type,
            price=signal.price,
            quantity=signal.quantity,
            status=OrderStatus.PENDING,
            timestamp=datetime.now()
        )
        
        self.orders[order_id] = order
        self.logger.info(f"创建订单: {order_id} {signal.stock_code} {signal.signal_type.value}")
        
        return order
        
    def _execute_paper_order(self, order: Order):
        """执行模拟订单"""
        # 模拟订单执行
        time.sleep(1)  # 模拟执行时间
        
        order.status = OrderStatus.EXECUTED
        order.executed_time = datetime.now()
        order.executed_price = order.price
        
        # 更新持仓
        self._update_position_from_order(order)
        
        self.logger.info(f"模拟订单执行成功: {order.order_id}")
        
    def _execute_real_order(self, order: Order):
        """执行实盘订单"""
        # 这里应该调用实际的交易接口
        # 暂时用模拟执行
        self._execute_paper_order(order)
        
    def _update_position_from_order(self, order: Order):
        """根据订单更新持仓"""
        stock_code = order.stock_code
        
        if stock_code not in self.positions:
            self.positions[stock_code] = {
                'quantity': 0,
                'avg_price': 0,
                'value': 0
            }
            
        position = self.positions[stock_code]
        
        if order.order_type == OrderType.BUY:
            # 买入：增加持仓
            new_quantity = position['quantity'] + order.quantity
            new_value = position['value'] + (order.executed_price * order.quantity)
            new_avg_price = new_value / new_quantity if new_quantity > 0 else 0
            
            position['quantity'] = new_quantity
            position['avg_price'] = new_avg_price
            position['value'] = new_value
            
        elif order.order_type == OrderType.SELL:
            # 卖出：减少持仓
            new_quantity = position['quantity'] - order.quantity
            if new_quantity <= 0:
                # 完全卖出
                del self.positions[stock_code]
            else:
                # 部分卖出
                position['quantity'] = new_quantity
                position['value'] = position['avg_price'] * new_quantity
                
    def _update_positions(self):
        """更新持仓信息"""
        # 这里应该从交易账户获取实际持仓
        # 暂时跳过
        pass
        
    def _check_stop_orders(self):
        """检查止损止盈"""
        for stock_code, position in self.positions.items():
            try:
                # 获取当前价格
                current_data = self.data_provider.get_daily_data(
                    stock_code,
                    start_date=datetime.now().strftime('%Y-%m-%d'),
                    end_date=datetime.now().strftime('%Y-%m-%d')
                )
                
                if current_data.empty:
                    continue
                    
                current_price = current_data.iloc[-1]['close']
                
                # 检查止损
                if position['avg_price'] * (1 - self.config['stop_loss_ratio']) >= current_price:
                    self._create_stop_order(stock_code, OrderType.SELL, "止损")
                    
                # 检查止盈
                if position['avg_price'] * (1 + self.config['take_profit_ratio']) <= current_price:
                    self._create_stop_order(stock_code, OrderType.SELL, "止盈")
                    
            except Exception as e:
                self.logger.error(f"检查止损止盈失败 {stock_code}: {e}")
                
    def _create_stop_order(self, stock_code: str, order_type: OrderType, reason: str):
        """创建止损止盈订单"""
        position = self.positions[stock_code]
        
        signal = TradeSignal(
            stock_code=stock_code,
            signal_type=order_type,
            price=0,  # 市价单
            quantity=position['quantity'],
            strategy=f"自动{reason}",
            timestamp=datetime.now(),
            confidence=1.0
        )
        
        # 直接执行
        order = self._create_order(signal)
        if self.config['paper_trading']:
            self._execute_paper_order(order)
        else:
            self._execute_real_order(order)
            
    def _get_watchlist(self) -> List[str]:
        """获取关注列表"""
        # 这里应该从配置文件或数据库获取
        # 暂时返回一些示例股票
        return ['000001.XSHE', '000002.XSHE', '600000.XSHG']
        
    def get_trading_status(self) -> Dict:
        """获取交易状态"""
        return {
            'is_running': self.is_running,
            'total_orders': len(self.orders),
            'total_positions': len(self.positions),
            'config': self.config
        }
        
    def get_orders(self) -> List[Dict]:
        """获取订单列表"""
        return [
            {
                'order_id': order.order_id,
                'stock_code': order.stock_code,
                'order_type': order.order_type.value,
                'price': order.price,
                'quantity': order.quantity,
                'status': order.status.value,
                'timestamp': order.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'executed_time': order.executed_time.strftime('%Y-%m-%d %H:%M:%S') if order.executed_time else None,
                'executed_price': order.executed_price
            }
            for order in self.orders.values()
        ]
        
    def get_positions(self) -> Dict:
        """获取持仓信息"""
        return {
            stock_code: {
                'quantity': pos['quantity'],
                'avg_price': pos['avg_price'],
                'value': pos['value']
            }
            for stock_code, pos in self.positions.items()
        }
