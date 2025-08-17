"""
KDJ+MACD金叉策略
结合KDJ和MACD两个技术指标，当两个指标同时出现金叉时买入，死叉时卖出
"""

import pandas as pd
import numpy as np
from typing import Dict
import logging
from .base_strategy import BaseStrategy

class KDJMACDStrategy(BaseStrategy):
    """KDJ+MACD金叉策略"""
    
    def __init__(self, parameters: Dict = None):
        """
        初始化策略
        
        Args:
            parameters: 策略参数
                - kdj_n: KDJ计算周期 (默认9)
                - kdj_m1: KDJ的M1参数 (默认3)
                - kdj_m2: KDJ的M2参数 (默认3)
                - macd_fast: MACD快线周期 (默认12)
                - macd_slow: MACD慢线周期 (默认26)
                - macd_signal: MACD信号线周期 (默认9)
                - position_size: 仓位比例 (默认0.1)
        """
        default_params = {
            'kdj_n': 9,
            'kdj_m1': 3,
            'kdj_m2': 3,
            'macd_fast': 12,
            'macd_slow': 26,
            'macd_signal': 9,
            'position_size': 0.1
        }
        
        if parameters:
            default_params.update(parameters)
        
        super().__init__("KDJ+MACD金叉策略", default_params)
        
        self.kdj_n = self.parameters['kdj_n']
        self.kdj_m1 = self.parameters['kdj_m1']
        self.kdj_m2 = self.parameters['kdj_m2']
        self.macd_fast = self.parameters['macd_fast']
        self.macd_slow = self.parameters['macd_slow']
        self.macd_signal = self.parameters['macd_signal']
        self.position_size = self.parameters['position_size']
        
        logging.info(f"KDJ+MACD策略初始化: KDJ({self.kdj_n},{self.kdj_m1},{self.kdj_m2}), MACD({self.macd_fast},{self.macd_slow},{self.macd_signal})")
    
    def calculate_kdj(self, data: pd.DataFrame) -> pd.DataFrame:
        """计算KDJ指标"""
        result = data.copy()
        
        # 计算RSV
        low_min = result['low'].rolling(window=self.kdj_n).min()
        high_max = result['high'].rolling(window=self.kdj_n).max()
        rsv = 100 * ((result['close'] - low_min) / (high_max - low_min))
        
        # 计算K值
        result['K'] = rsv.ewm(span=self.kdj_m1).mean()
        
        # 计算D值
        result['D'] = result['K'].ewm(span=self.kdj_m2).mean()
        
        # 计算J值
        result['J'] = 3 * result['K'] - 2 * result['D']
        
        return result
    
    def calculate_macd(self, data: pd.DataFrame) -> pd.DataFrame:
        """计算MACD指标"""
        result = data.copy()
        
        # 计算EMA
        ema_fast = result['close'].ewm(span=self.macd_fast).mean()
        ema_slow = result['close'].ewm(span=self.macd_slow).mean()
        
        # 计算MACD线
        result['MACD'] = ema_fast - ema_slow
        
        # 计算信号线
        result['MACD_Signal'] = result['MACD'].ewm(span=self.macd_signal).mean()
        
        # 计算MACD柱状图
        result['MACD_Histogram'] = result['MACD'] - result['MACD_Signal']
        
        return result
    
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
        
        # 计算KDJ指标
        result = self.calculate_kdj(result)
        
        # 计算MACD指标
        result = self.calculate_macd(result)
        
        # 生成信号
        result['signal'] = 0
        
        # 计算金叉和死叉
        # KDJ金叉：K线上穿D线
        kdj_golden_cross = (result['K'] > result['D']) & (result['K'].shift(1) <= result['D'].shift(1))
        
        # KDJ死叉：K线下穿D线
        kdj_death_cross = (result['K'] < result['D']) & (result['K'].shift(1) >= result['D'].shift(1))
        
        # MACD金叉：MACD线上穿信号线
        macd_golden_cross = (result['MACD'] > result['MACD_Signal']) & (result['MACD'].shift(1) <= result['MACD_Signal'].shift(1))
        
        # MACD死叉：MACD线下穿信号线
        macd_death_cross = (result['MACD'] < result['MACD_Signal']) & (result['MACD'].shift(1) >= result['MACD_Signal'].shift(1))
        
        # 双重金叉买入信号：KDJ和MACD同时金叉
        result.loc[kdj_golden_cross & macd_golden_cross, 'signal'] = 1
        
        # 双重死叉卖出信号：KDJ和MACD同时死叉
        result.loc[kdj_death_cross & macd_death_cross, 'signal'] = -1
        
        # 过滤掉前期的无效信号
        min_period = max(self.kdj_n + self.kdj_m2, self.macd_slow + self.macd_signal)
        result.loc[:min_period, 'signal'] = 0
        
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
            'type': '技术指标组合',
            'kdj_n': self.kdj_n,
            'kdj_m1': self.kdj_m1,
            'kdj_m2': self.kdj_m2,
            'macd_fast': self.macd_fast,
            'macd_slow': self.macd_slow,
            'macd_signal': self.macd_signal,
            'position_size': self.position_size,
            'description': f'KDJ({self.kdj_n},{self.kdj_m1},{self.kdj_m2})和MACD({self.macd_fast},{self.macd_slow},{self.macd_signal})双重金叉策略'
        }
    
    def get_technical_indicators(self) -> Dict:
        """获取技术指标值"""
        return {
            'kdj_k': self.K if hasattr(self, 'K') else None,
            'kdj_d': self.D if hasattr(self, 'D') else None,
            'kdj_j': self.J if hasattr(self, 'J') else None,
            'macd': self.MACD if hasattr(self, 'MACD') else None,
            'macd_signal': self.MACD_Signal if hasattr(self, 'MACD_Signal') else None,
            'macd_histogram': self.MACD_Histogram if hasattr(self, 'MACD_Histogram') else None
        }
