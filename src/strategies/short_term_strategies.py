"""
短期策略优化模块
专门针对有限数据范围（1年左右）的策略优化

适用于聚宽账号权限限制的情况
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional
import logging
from datetime import datetime, timedelta

class ShortTermStrategies:
    """短期策略优化类"""
    
    def __init__(self, data_provider):
        """
        初始化短期策略
        
        Args:
            data_provider: 数据提供者实例
        """
        self.data_provider = data_provider
        self.logger = logging.getLogger(__name__)
        
        # 短期策略参数配置
        self.config = {
            'ma_cross': {
                'short_window': 3,    # 3日均线
                'long_window': 8,     # 8日均线
                'min_data_points': 10  # 最少需要10个数据点
            },
            'kdj_macd': {
                'kdj_n': 5,           # 5日KDJ
                'kdj_m1': 2,          # 快速平滑
                'kdj_m2': 2,          # 慢速平滑
                'macd_fast': 5,       # 5日EMA
                'macd_slow': 10,      # 10日EMA
                'macd_signal': 3,     # 3日信号线
                'min_data_points': 12
            },
            'rsi_momentum': {
                'rsi_period': 5,      # 5日RSI
                'rsi_oversold': 35,   # RSI超卖阈值
                'rsi_overbought': 65, # RSI超买阈值
                'momentum_period': 3, # 3日动量
                'min_data_points': 8
            },
            'volume_price': {
                'volume_ma': 5,       # 5日成交量均线
                'price_ma': 5,        # 5日价格均线
                'volume_ratio': 1.3,  # 成交量放大倍数
                'price_change': 0.02, # 价格变化阈值
                'min_data_points': 8
            }
        }
    
    def screen_by_short_term_ma(self, stock_list: List[str], 
                                min_price: float = 5.0, 
                                max_price: float = 100.0) -> List[Dict]:
        """
        短期均线交叉策略
        
        Args:
            stock_list: 股票代码列表
            min_price: 最低价格
            max_price: 最高价格
            
        Returns:
            List[Dict]: 符合条件的股票列表
        """
        selected_stocks = []
        config = self.config['ma_cross']
        
        for stock_code in stock_list[:30]:  # 限制数量提高效率
            try:
                # 获取股票数据（适应聚宽权限限制）
                end_date = '2025-05-14'
                start_date = '2024-05-07'
                
                data = self.data_provider.get_daily_data(stock_code, start_date, end_date)
                
                if data.empty or len(data) < config['min_data_points']:
                    continue
                
                # 计算短期均线
                data['MA_short'] = data['close'].rolling(window=config['short_window']).mean()
                data['MA_long'] = data['close'].rolling(window=config['long_window']).mean()
                
                # 获取最新数据
                latest = data.iloc[-1]
                prev = data.iloc[-2]
                
                # 检查价格范围
                if not (min_price <= latest['close'] <= max_price):
                    continue
                
                # 检查短期金叉
                golden_cross = (latest['MA_short'] > latest['MA_long'] and 
                               prev['MA_short'] <= prev['MA_long'])
                
                # 检查均线趋势
                ma_trend = (latest['MA_short'] > latest['MA_short'] * 0.98 and  # 短期均线向上
                           latest['MA_long'] > latest['MA_long'] * 0.98)        # 长期均线向上
                
                if golden_cross and ma_trend:
                    selected_stocks.append({
                        'code': stock_code,
                        'name': self._get_stock_name(stock_code),
                        'price': latest['close'],
                        'ma_short': latest['MA_short'],
                        'ma_long': latest['MA_long'],
                        'volume': latest['volume'],
                        'strategy': '短期均线交叉',
                        'signal': '短期金叉买入',
                        'data_points': len(data)
                    })
                
            except Exception as e:
                self.logger.warning(f"处理股票 {stock_code} 时出错: {e}")
                continue
        
        return selected_stocks
    
    def screen_by_short_term_kdj_macd(self, stock_list: List[str],
                                     min_price: float = 5.0, 
                                     max_price: float = 100.0) -> List[Dict]:
        """
        短期KDJ+MACD策略
        
        Args:
            stock_list: 股票代码列表
            min_price: 最低价格
            max_price: 最高价格
            
        Returns:
            List[Dict]: 符合条件的股票列表
        """
        selected_stocks = []
        config = self.config['kdj_macd']
        
        for stock_code in stock_list[:30]:
            try:
                # 获取股票数据
                end_date = '2025-05-14'
                start_date = '2024-05-07'
                
                data = self.data_provider.get_daily_data(stock_code, start_date, end_date)
                
                if data.empty or len(data) < config['min_data_points']:
                    continue
                
                # 计算短期KDJ
                data['K'] = self._calculate_kdj_k(data, config['kdj_n'], config['kdj_m1'])
                data['D'] = self._calculate_kdj_d(data, config['kdj_m2'])
                data['J'] = 3 * data['K'] - 2 * data['D']
                
                # 计算短期MACD
                data['EMA_fast'] = data['close'].ewm(span=config['macd_fast']).mean()
                data['EMA_slow'] = data['close'].ewm(span=config['macd_slow']).mean()
                data['MACD'] = data['EMA_fast'] - data['EMA_slow']
                data['MACD_Signal'] = data['MACD'].ewm(span=config['macd_signal']).mean()
                
                # 获取最新数据
                latest = data.iloc[-1]
                prev = data.iloc[-2]
                
                # 检查价格范围
                if not (min_price <= latest['close'] <= max_price):
                    continue
                
                # 检查短期双重金叉
                kdj_golden = (latest['K'] > latest['D'] and prev['K'] <= prev['D'])
                macd_golden = (latest['MACD'] > latest['MACD_Signal'] and 
                              prev['MACD'] <= prev['MACD_Signal'])
                
                # 检查指标强度
                kdj_strength = latest['K'] > 50 and latest['D'] > 40
                macd_strength = latest['MACD'] > 0
                
                if kdj_golden and macd_golden and kdj_strength and macd_strength:
                    selected_stocks.append({
                        'code': stock_code,
                        'name': self._get_stock_name(stock_code),
                        'price': latest['close'],
                        'kdj_k': latest['K'],
                        'kdj_d': latest['D'],
                        'kdj_j': latest['J'],
                        'macd': latest['MACD'],
                        'macd_signal': latest['MACD_Signal'],
                        'volume': latest['volume'],
                        'strategy': '短期KDJ+MACD',
                        'signal': '短期双重金叉',
                        'data_points': len(data)
                    })
                
            except Exception as e:
                self.logger.warning(f"处理股票 {stock_code} 时出错: {e}")
                continue
        
        return selected_stocks
    
    def screen_by_rsi_momentum(self, stock_list: List[str],
                              min_price: float = 5.0, 
                              max_price: float = 100.0) -> List[Dict]:
        """
        短期RSI+动量策略
        
        Args:
            stock_list: 股票代码列表
            min_price: 最低价格
            max_price: 最高价格
            
        Returns:
            List[Dict]: 符合条件的股票列表
        """
        selected_stocks = []
        config = self.config['rsi_momentum']
        
        for stock_code in stock_list[:30]:
            try:
                # 获取股票数据
                end_date = '2025-05-14'
                start_date = '2024-05-07'
                
                data = self.data_provider.get_daily_data(stock_code, start_date, end_date)
                
                if data.empty or len(data) < config['min_data_points']:
                    continue
                
                # 计算短期RSI
                data['RSI'] = self._calculate_rsi(data, config['rsi_period'])
                
                # 计算短期动量
                data['momentum'] = data['close'].pct_change(periods=config['momentum_period'])
                data['momentum_ma'] = data['momentum'].rolling(window=3).mean()
                
                # 获取最新数据
                latest = data.iloc[-1]
                
                # 检查价格范围
                if not (min_price <= latest['close'] <= max_price):
                    continue
                
                # 检查RSI和动量条件
                rsi_oversold = latest['RSI'] < config['rsi_oversold']
                rsi_not_overbought = latest['RSI'] < config['rsi_overbought']
                momentum_positive = latest['momentum'] > 0
                momentum_increasing = latest['momentum'] > latest['momentum_ma']
                
                if (rsi_oversold and rsi_not_overbought and 
                    momentum_positive and momentum_increasing):
                    selected_stocks.append({
                        'code': stock_code,
                        'name': self._get_stock_name(stock_code),
                        'price': latest['close'],
                        'rsi': latest['RSI'],
                        'momentum': latest['momentum'],
                        'momentum_ma': latest['momentum_ma'],
                        'volume': latest['volume'],
                        'strategy': '短期RSI+动量',
                        'signal': 'RSI超卖+动量增强',
                        'data_points': len(data)
                    })
                
            except Exception as e:
                self.logger.warning(f"处理股票 {stock_code} 时出错: {e}")
                continue
        
        return selected_stocks
    
    def _calculate_kdj_k(self, data: pd.DataFrame, n: int, m: int) -> pd.Series:
        """计算KDJ的K值"""
        low_min = data['low'].rolling(window=n).min()
        high_max = data['high'].rolling(window=n).max()
        rsv = (data['close'] - low_min) / (high_max - low_min) * 100
        return rsv.ewm(span=m).mean()
    
    def _calculate_kdj_d(self, data: pd.DataFrame, m: int) -> pd.Series:
        """计算KDJ的D值"""
        return data['K'].ewm(span=m).mean()
    
    def _calculate_rsi(self, data: pd.DataFrame, period: int) -> pd.Series:
        """计算RSI指标"""
        delta = data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    
    def _get_stock_name(self, stock_code: str) -> str:
        """获取股票名称"""
        try:
            # 这里可以调用数据提供者获取股票名称
            # 暂时返回代码
            return stock_code
        except:
            return stock_code
