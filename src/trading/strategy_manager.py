#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
策略管理器
负责分析股票并生成交易信号
"""

import logging
from typing import Dict, List, Optional
import pandas as pd
import numpy as np
from datetime import datetime

class StrategyManager:
    """策略管理器"""
    
    def __init__(self, data_provider):
        """
        初始化策略管理器
        
        Args:
            data_provider: 数据提供者
        """
        self.data_provider = data_provider
        self.logger = logging.getLogger(__name__)
        
        # 策略配置
        self.strategies = {
            'ma_cross': self._ma_cross_strategy,
            'kdj_macd': self._kdj_macd_strategy,
            'rsi_momentum': self._rsi_momentum_strategy,
            'volume_breakout': self._volume_breakout_strategy
        }
        
    def analyze_stock(self, stock_code: str, data: pd.DataFrame) -> List[Dict]:
        """
        分析股票并生成交易信号
        
        Args:
            stock_code: 股票代码
            data: 股票数据
            
        Returns:
            List[Dict]: 交易信号列表
        """
        signals = []
        
        try:
            # 使用多个策略分析
            for strategy_name, strategy_func in self.strategies.items():
                try:
                    strategy_signals = strategy_func(stock_code, data)
                    if strategy_signals:
                        signals.extend(strategy_signals)
                except Exception as e:
                    self.logger.warning(f"策略 {strategy_name} 分析失败 {stock_code}: {e}")
                    continue
                    
        except Exception as e:
            self.logger.error(f"分析股票失败 {stock_code}: {e}")
            
        return signals
        
    def _ma_cross_strategy(self, stock_code: str, data: pd.DataFrame) -> List[Dict]:
        """均线交叉策略"""
        signals = []
        
        if len(data) < 20:
            return signals
            
        try:
            # 计算均线
            data['MA5'] = data['close'].rolling(window=5).mean()
            data['MA20'] = data['close'].rolling(window=20).mean()
            
            # 获取最新数据
            latest = data.iloc[-1]
            prev = data.iloc[-2]
            
            # 检查金叉
            if (latest['MA5'] > latest['MA20'] and 
                prev['MA5'] <= prev['MA20']):
                
                # 计算信号强度
                strength = self._calculate_signal_strength(data, 'ma_cross')
                
                signal = {
                    'type': 'buy',
                    'price': latest['close'],
                    'quantity': self._calculate_position_size(latest['close']),
                    'strategy': 'MA交叉策略',
                    'confidence': strength,
                    'stop_loss': latest['close'] * 0.95,  # 5%止损
                    'take_profit': latest['close'] * 1.15  # 15%止盈
                }
                signals.append(signal)
                
            # 检查死叉
            elif (latest['MA5'] < latest['MA20'] and 
                  prev['MA5'] >= prev['MA20']):
                
                strength = self._calculate_signal_strength(data, 'ma_cross')
                
                signal = {
                    'type': 'sell',
                    'price': latest['close'],
                    'quantity': self._calculate_position_size(latest['close']),
                    'strategy': 'MA交叉策略',
                    'confidence': strength,
                    'stop_loss': None,
                    'take_profit': None
                }
                signals.append(signal)
                
        except Exception as e:
            self.logger.error(f"MA交叉策略分析失败 {stock_code}: {e}")
            
        return signals
        
    def _kdj_macd_strategy(self, stock_code: str, data: pd.DataFrame) -> List[Dict]:
        """KDJ+MACD策略"""
        signals = []
        
        if len(data) < 30:
            return signals
            
        try:
            # 计算KDJ
            low_min = data['low'].rolling(window=9).min()
            high_max = data['high'].rolling(window=9).max()
            rsv = 100 * ((data['close'] - low_min) / (high_max - low_min))
            
            data['K'] = rsv.ewm(span=3).mean()
            data['D'] = data['K'].ewm(span=3).mean()
            data['J'] = 3 * data['K'] - 2 * data['D']
            
            # 计算MACD
            ema12 = data['close'].ewm(span=12).mean()
            ema26 = data['close'].ewm(span=26).mean()
            data['MACD'] = ema12 - ema26
            data['MACD_Signal'] = data['MACD'].ewm(span=9).mean()
            
            # 获取最新数据
            latest = data.iloc[-1]
            prev = data.iloc[-2]
            
            # 检查双重金叉
            kdj_golden = (latest['K'] > latest['D'] and prev['K'] <= prev['D'])
            macd_golden = (latest['MACD'] > latest['MACD_Signal'] and 
                          prev['MACD'] <= prev['MACD_Signal'])
            
            if kdj_golden and macd_golden:
                strength = self._calculate_signal_strength(data, 'kdj_macd')
                
                signal = {
                    'type': 'buy',
                    'price': latest['close'],
                    'quantity': self._calculate_position_size(latest['close']),
                    'strategy': 'KDJ+MACD双重金叉',
                    'confidence': strength,
                    'stop_loss': latest['close'] * 0.92,  # 8%止损
                    'take_profit': latest['close'] * 1.20  # 20%止盈
                }
                signals.append(signal)
                
        except Exception as e:
            self.logger.error(f"KDJ+MACD策略分析失败 {stock_code}: {e}")
            
        return signals
        
    def _rsi_momentum_strategy(self, stock_code: str, data: pd.DataFrame) -> List[Dict]:
        """RSI动量策略"""
        signals = []
        
        if len(data) < 14:
            return signals
            
        try:
            # 计算RSI
            delta = data['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            data['RSI'] = 100 - (100 / (1 + rs))
            
            # 计算动量
            data['momentum'] = data['close'].pct_change(5)
            
            latest = data.iloc[-1]
            
            # RSI超卖 + 动量向上
            if (latest['RSI'] < 30 and latest['momentum'] > 0.02):
                strength = self._calculate_signal_strength(data, 'rsi_momentum')
                
                signal = {
                    'type': 'buy',
                    'price': latest['close'],
                    'quantity': self._calculate_position_size(latest['close']),
                    'strategy': 'RSI动量策略',
                    'confidence': strength,
                    'stop_loss': latest['close'] * 0.90,  # 10%止损
                    'take_profit': latest['close'] * 1.25  # 25%止盈
                }
                signals.append(signal)
                
            # RSI超买 + 动量向下
            elif (latest['RSI'] > 70 and latest['momentum'] < -0.02):
                strength = self._calculate_signal_strength(data, 'rsi_momentum')
                
                signal = {
                    'type': 'sell',
                    'price': latest['close'],
                    'quantity': self._calculate_position_size(latest['close']),
                    'strategy': 'RSI动量策略',
                    'confidence': strength,
                    'stop_loss': None,
                    'take_profit': None
                }
                signals.append(signal)
                
        except Exception as e:
            self.logger.error(f"RSI动量策略分析失败 {stock_code}: {e}")
            
        return signals
        
    def _volume_breakout_strategy(self, stock_code: str, data: pd.DataFrame) -> List[Dict]:
        """放量突破策略"""
        signals = []
        
        if len(data) < 20:
            return signals
            
        try:
            # 计算成交量均线
            data['Volume_MA5'] = data['volume'].rolling(window=5).mean()
            data['Volume_MA10'] = data['volume'].rolling(window=10).mean()
            
            # 计算价格变化
            data['price_change'] = data['close'].pct_change()
            
            latest = data.iloc[-1]
            
            # 放量突破
            volume_breakout = (latest['volume'] > 2.0 * latest['Volume_MA5'] and
                             latest['volume'] > 1.5 * latest['Volume_MA10'])
            
            price_breakout = abs(latest['price_change']) > 0.05  # 5%以上价格变化
            
            if volume_breakout and price_breakout:
                strength = self._calculate_signal_strength(data, 'volume_breakout')
                
                signal_type = 'buy' if latest['price_change'] > 0 else 'sell'
                
                signal = {
                    'type': signal_type,
                    'price': latest['close'],
                    'quantity': self._calculate_position_size(latest['close']),
                    'strategy': '放量突破策略',
                    'confidence': strength,
                    'stop_loss': latest['close'] * (0.95 if signal_type == 'buy' else 1.05),
                    'take_profit': latest['close'] * (1.15 if signal_type == 'buy' else 0.85)
                }
                signals.append(signal)
                
        except Exception as e:
            self.logger.error(f"放量突破策略分析失败 {stock_code}: {e}")
            
        return signals
        
    def _calculate_signal_strength(self, data: pd.DataFrame, strategy: str) -> float:
        """计算信号强度 (0-1)"""
        try:
            if strategy == 'ma_cross':
                # 基于均线距离和成交量
                latest = data.iloc[-1]
                ma_distance = abs(latest['MA5'] - latest['MA20']) / latest['MA20']
                volume_ratio = latest['volume'] / data['volume'].rolling(window=20).mean().iloc[-1]
                
                strength = min(0.9, 0.5 + ma_distance * 10 + min(0.3, volume_ratio * 0.1))
                
            elif strategy == 'kdj_macd':
                # 基于KDJ和MACD的背离程度
                latest = data.iloc[-1]
                kdj_strength = (latest['K'] - latest['D']) / 100
                macd_strength = abs(latest['MACD'] - latest['MACD_Signal']) / abs(latest['MACD_Signal'])
                
                strength = min(0.95, 0.6 + abs(kdj_strength) * 0.3 + min(0.2, macd_strength * 0.2))
                
            elif strategy == 'rsi_momentum':
                # 基于RSI极值和动量强度
                latest = data.iloc[-1]
                rsi_extreme = abs(latest['RSI'] - 50) / 50
                momentum_strength = abs(latest['momentum'])
                
                strength = min(0.9, 0.5 + rsi_extreme * 0.3 + min(0.2, momentum_strength * 5))
                
            elif strategy == 'volume_breakout':
                # 基于放量程度和价格变化
                latest = data.iloc[-1]
                volume_strength = latest['volume'] / data['volume'].rolling(window=20).mean().iloc[-1]
                price_strength = abs(latest['price_change'])
                
                strength = min(0.95, 0.6 + min(0.3, (volume_strength - 1) * 0.1) + min(0.2, price_strength * 2))
                
            else:
                strength = 0.7  # 默认强度
                
            return max(0.1, min(0.95, strength))  # 限制在0.1-0.95之间
            
        except Exception as e:
            self.logger.warning(f"计算信号强度失败: {e}")
            return 0.7  # 默认强度
            
    def _calculate_position_size(self, price: float) -> int:
        """计算持仓数量"""
        # 这里应该基于资金管理规则计算
        # 暂时返回固定数量
        base_amount = 10000  # 基础投资金额
        return int(base_amount / price / 100) * 100  # 按手数(100股)计算
