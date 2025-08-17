"""
移动平均线交叉策略
当短期均线上穿长期均线时买入，下穿时卖出
"""

import pandas as pd
import numpy as np
from typing import Dict
import logging
from .base_strategy import BaseStrategy

class MACrossStrategy(BaseStrategy):
    """移动平均线交叉策略"""
    
    def __init__(self, parameters: Dict = None):
        """
        初始化策略
        
        Args:
            parameters: 策略参数
                - short_window: 短期均线周期 (默认5)
                - long_window: 长期均线周期 (默认20)
                - position_size: 仓位比例 (默认0.1)
        """
        default_params = {
            'short_window': 5,
            'long_window': 20,
            'position_size': 0.1
        }
        
        if parameters:
            default_params.update(parameters)
        
        super().__init__("MA交叉策略", default_params)
        
        self.short_window = self.parameters['short_window']
        self.long_window = self.parameters['long_window']
        self.position_size = self.parameters['position_size']
        
        logging.info(f"MA交叉策略初始化: 短期{self.short_window}日, 长期{self.long_window}日")
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        生成交易信号
        
        Args:
            data: 包含OHLCV数据的DataFrame
            
        Returns:
            pd.DataFrame: 包含交易信号的数据
        """
        if data.empty:
            return data
        
        result = data.copy()
        
        # 计算移动平均线
        result['MA_short'] = result['close'].rolling(window=self.short_window).mean()
        result['MA_long'] = result['close'].rolling(window=self.long_window).mean()
        
        # 生成信号
        result['signal'] = 0
        
        # 金叉：短期均线上穿长期均线
        result.loc[(result['MA_short'] > result['MA_long']) & 
                   (result['MA_short'].shift(1) <= result['MA_long'].shift(1)), 'signal'] = 1
        
        # 死叉：短期均线下穿长期均线
        result.loc[(result['MA_short'] < result['MA_long']) & 
                   (result['MA_short'].shift(1) >= result['MA_long'].shift(1)), 'signal'] = -1
        
        # 过滤掉前期的无效信号
        result.loc[:self.long_window, 'signal'] = 0
        
        return result
    
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
        if signal == 0:
            return 0
        
        if signal == 1:  # 买入
            # 使用可用资金的一定比例
            available_cash = cash * self.position_size
            quantity = int(available_cash / price)
            return quantity
        else:  # 卖出
            # 卖出全部持仓
            return abs(self.positions.get('current_security', 0))
    
    def get_strategy_info(self) -> Dict:
        """获取策略信息"""
        return {
            'name': self.name,
            'type': '趋势跟踪',
            'short_window': self.short_window,
            'long_window': self.long_window,
            'position_size': self.position_size,
            'description': f'当{self.short_window}日均线上穿{self.long_window}日均线时买入，下穿时卖出'
        }
