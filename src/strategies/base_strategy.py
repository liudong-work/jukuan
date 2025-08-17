"""
策略基类
定义所有交易策略的通用接口
"""

from abc import ABC, abstractmethod
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime

class BaseStrategy(ABC):
    """策略基类"""
    
    def __init__(self, name: str, parameters: Dict = None):
        """
        初始化策略
        
        Args:
            name: 策略名称
            parameters: 策略参数
        """
        self.name = name
        self.parameters = parameters or {}
        self.positions = {}  # 当前持仓
        self.trades = []     # 交易记录
        self.cash = 1000000  # 初始资金
        self.equity_curve = []  # 权益曲线
        
        # 策略状态
        self.is_active = False
        self.start_time = None
        self.end_time = None
        
        logging.info(f"策略 {name} 初始化完成")
    
    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        生成交易信号
        
        Args:
            data: 市场数据
            
        Returns:
            pd.DataFrame: 包含交易信号的数据
        """
        pass
    
    @abstractmethod
    def calculate_position_size(self, signal: int, price: float, cash: float) -> int:
        """
        计算仓位大小
        
        Args:
            signal: 交易信号 (1=买入, -1=卖出, 0=持有)
            price: 当前价格
            cash: 可用资金
            
        Returns:
            int: 交易数量
        """
        pass
    
    def execute_trade(self, security: str, signal: int, price: float, 
                     timestamp: datetime, quantity: int = None) -> bool:
        """
        执行交易
        
        Args:
            security: 证券代码
            signal: 交易信号
            price: 交易价格
            timestamp: 交易时间
            quantity: 交易数量
            
        Returns:
            bool: 交易是否成功
        """
        try:
            if quantity is None:
                quantity = self.calculate_position_size(signal, price, self.cash)
            
            if quantity == 0:
                return False
            
            # 记录交易
            trade = {
                'timestamp': timestamp,
                'security': security,
                'signal': signal,
                'price': price,
                'quantity': quantity,
                'value': price * quantity
            }
            
            # 更新持仓
            if security not in self.positions:
                self.positions[security] = 0
            
            old_position = self.positions[security]
            self.positions[security] += quantity * signal
            
            # 更新现金
            self.cash -= price * quantity * signal
            
            # 记录交易
            self.trades.append(trade)
            
            # 更新权益曲线
            self._update_equity_curve(timestamp, price, quantity, signal)
            
            logging.info(f"执行交易: {security} {signal} {quantity} @ {price}")
            return True
            
        except Exception as e:
            logging.error(f"执行交易失败: {e}")
            return False
    
    def _update_equity_curve(self, timestamp: datetime, price: float, 
                            quantity: int, signal: int):
        """更新权益曲线"""
        # 计算当前总资产
        total_value = self.cash
        for sec, pos in self.positions.items():
            if pos != 0:
                total_value += pos * price  # 简化处理，使用当前价格
        
        self.equity_curve.append({
            'timestamp': timestamp,
            'equity': total_value,
            'cash': self.cash
        })
    
    def get_performance_metrics(self) -> Dict:
        """
        获取策略性能指标
        
        Returns:
            Dict: 性能指标字典
        """
        if not self.equity_curve:
            return {}
        
        equity_df = pd.DataFrame(self.equity_curve)
        equity_df.set_index('timestamp', inplace=True)
        
        # 计算收益率
        equity_df['returns'] = equity_df['equity'].pct_change()
        
        # 计算性能指标
        total_return = (equity_df['equity'].iloc[-1] / equity_df['equity'].iloc[0]) - 1
        annual_return = total_return * (252 / len(equity_df))
        volatility = equity_df['returns'].std() * np.sqrt(252)
        sharpe_ratio = annual_return / volatility if volatility > 0 else 0
        
        # 最大回撤
        equity_df['cummax'] = equity_df['equity'].cummax()
        equity_df['drawdown'] = (equity_df['equity'] - equity_df['cummax']) / equity_df['cummax']
        max_drawdown = equity_df['drawdown'].min()
        
        return {
            'total_return': total_return,
            'annual_return': annual_return,
            'volatility': volatility,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'total_trades': len(self.trades),
            'win_rate': self._calculate_win_rate()
        }
    
    def _calculate_win_rate(self) -> float:
        """计算胜率"""
        if not self.trades:
            return 0.0
        
        # 简化计算，基于信号方向
        buy_trades = [t for t in self.trades if t['signal'] == 1]
        sell_trades = [t for t in self.trades if t['signal'] == -1]
        
        if not buy_trades or not sell_trades:
            return 0.0
        
        # 这里简化处理，实际应该基于价格变化计算盈亏
        return 0.5  # 默认50%胜率
    
    def start(self, start_time: datetime = None):
        """启动策略"""
        self.is_active = True
        self.start_time = start_time or datetime.now()
        logging.info(f"策略 {self.name} 启动")
    
    def stop(self, end_time: datetime = None):
        """停止策略"""
        self.is_active = False
        self.end_time = end_time or datetime.now()
        logging.info(f"策略 {self.name} 停止")
    
    def reset(self):
        """重置策略状态"""
        self.positions = {}
        self.trades = []
        self.cash = 1000000
        self.equity_curve = []
        self.is_active = False
        self.start_time = None
        self.end_time = None
        logging.info(f"策略 {self.name} 重置")
    
    def get_status(self) -> Dict:
        """获取策略状态"""
        return {
            'name': self.name,
            'is_active': self.is_active,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'positions': self.positions,
            'cash': self.cash,
            'total_trades': len(self.trades)
        }
