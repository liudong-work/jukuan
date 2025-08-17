"""
灵活选股策略
允许用户选择部分条件进行选股
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple
import logging
from datetime import datetime, timedelta

class FlexibleStockScreener:
    """灵活选股器类"""
    
    def __init__(self, data_provider):
        """
        初始化灵活选股器
        
        Args:
            data_provider: 数据提供者实例
        """
        self.data_provider = data_provider
        self.logger = logging.getLogger(__name__)
    
    def screen_by_selected_conditions(self, 
                                    stock_list: List[str],
                                    conditions: Dict[str, bool],
                                    min_price: float = 5.0,
                                    max_price: float = 100.0) -> List[Dict]:
        """
        根据选择的条件进行选股
        
        Args:
            stock_list: 股票代码列表
            conditions: 条件字典，key为条件名，value为是否启用
            min_price: 最低价格
            max_price: 最高价格
            
        Returns:
            List[Dict]: 符合条件的股票列表
        """
        selected_stocks = []
        
        for stock_code in stock_list[:80]:  # 限制数量避免超时
            try:
                # 获取股票数据
                end_date = '2025-05-14'  # 聚宽账号权限限制
                start_date = '2024-05-07'  # 聚宽账号权限限制
                
                daily_data = self.data_provider.get_daily_data(stock_code, start_date, end_date)
                
                if daily_data.empty or len(daily_data) < 30:
                    continue
                
                # 检查价格范围
                latest_price = daily_data['close'].iloc[-1]
                if not (min_price <= latest_price <= max_price):
                    continue
                
                # 根据启用的条件进行检查
                stock_info = {
                    'code': stock_code,
                    'name': self._get_stock_name(stock_code),
                    'price': latest_price,
                    'conditions_met': [],
                    'conditions_failed': [],
                    'strategy': '灵活选股策略',
                    'signal': '条件筛选'
                }
                
                all_conditions_met = True
                
                # 1. 排除科创板北交所
                if conditions.get('exclude_tech_board', False):
                    if self._is_excluded_exchange(stock_code):
                        all_conditions_met = False
                        stock_info['conditions_failed'].append('科创板北交所')
                    else:
                        stock_info['conditions_met'].append('非科创板北交所')
                
                # 2. 排除ST股票
                if conditions.get('exclude_st', False):
                    if self._is_st_stock(stock_code):
                        all_conditions_met = False
                        stock_info['conditions_failed'].append('非ST股票')
                    else:
                        stock_info['conditions_met'].append('非ST股票')
                
                # 3. 19天内有过涨停
                if conditions.get('has_limit_up', False):
                    if self._has_limit_up_in_days(daily_data, 19):
                        stock_info['conditions_met'].append('19天内有过涨停')
                    else:
                        all_conditions_met = False
                        stock_info['conditions_failed'].append('19天内有过涨停')
                
                # 4. 当日未涨停
                if conditions.get('not_limit_up_today', False):
                    if not self._is_limit_up_today(daily_data):
                        stock_info['conditions_met'].append('当日未涨停')
                    else:
                        all_conditions_met = False
                        stock_info['conditions_failed'].append('当日未涨停')
                
                # 5. 当日未跌停
                if conditions.get('not_limit_down_today', False):
                    if not self._is_limit_down_today(daily_data):
                        stock_info['conditions_met'].append('当日未跌停')
                    else:
                        all_conditions_met = False
                        stock_info['conditions_failed'].append('当日未跌停')
                
                # 6. 周线KDJ向上
                if conditions.get('weekly_kdj_up', False):
                    weekly_data = self._resample_to_weekly(daily_data)
                    if not weekly_data.empty and len(weekly_data) >= 20:
                        weekly_kdj = self._calculate_kdj(weekly_data, n=9, m1=3, m2=3)
                        if self._is_kdj_upward(weekly_kdj):
                            stock_info['conditions_met'].append('周线KDJ向上')
                            stock_info['weekly_kdj_k'] = weekly_kdj['K'].iloc[-1]
                            stock_info['weekly_kdj_d'] = weekly_kdj['D'].iloc[-1]
                            stock_info['weekly_kdj_j'] = weekly_kdj['J'].iloc[-1]
                        else:
                            all_conditions_met = False
                            stock_info['conditions_failed'].append('周线KDJ向上')
                    else:
                        all_conditions_met = False
                        stock_info['conditions_failed'].append('周线KDJ向上')
                
                # 7. 周线MACD往上
                if conditions.get('weekly_macd_up', False):
                    weekly_data = self._resample_to_weekly(daily_data)
                    if not weekly_data.empty and len(weekly_data) >= 30:
                        weekly_macd = self._calculate_macd(weekly_data, fast=12, slow=26, signal=9)
                        if self._is_macd_upward(weekly_macd):
                            stock_info['conditions_met'].append('周线MACD往上')
                            stock_info['weekly_macd'] = weekly_macd['MACD'].iloc[-1]
                            stock_info['weekly_macd_signal'] = weekly_macd['MACD_Signal'].iloc[-1]
                        else:
                            all_conditions_met = False
                            stock_info['conditions_failed'].append('周线MACD往上')
                    else:
                        all_conditions_met = False
                        stock_info['conditions_failed'].append('周线MACD往上')
                
                # 8. 日线MACD向上
                if conditions.get('daily_macd_up', False):
                    daily_macd = self._calculate_macd(daily_data, fast=12, slow=26, signal=9)
                    if self._is_macd_upward(daily_macd):
                        stock_info['conditions_met'].append('日线MACD向上')
                        stock_info['daily_macd'] = daily_macd['MACD'].iloc[-1]
                        stock_info['daily_macd_signal'] = daily_macd['MACD_Signal'].iloc[-1]
                    else:
                        all_conditions_met = False
                        stock_info['conditions_failed'].append('日线MACD向上')
                
                # 9. 成交量升序
                if conditions.get('volume_increasing', False):
                    if self._is_volume_increasing(daily_data, days=5):
                        stock_info['conditions_met'].append('成交量升序')
                        stock_info['volume_ratio'] = daily_data['volume'].iloc[-1] / daily_data['volume'].rolling(window=10).mean().iloc[-1]
                    else:
                        all_conditions_met = False
                        stock_info['conditions_failed'].append('成交量升序')
                
                # 10. 价格趋势向上
                if conditions.get('price_trend_up', False):
                    if self._is_price_trend_up(daily_data, days=20):
                        stock_info['conditions_met'].append('价格趋势向上')
                        stock_info['price_trend'] = (daily_data['close'].iloc[-1] - daily_data['close'].iloc[-20]) / daily_data['close'].iloc[-20]
                    else:
                        all_conditions_met = False
                        stock_info['conditions_failed'].append('价格趋势向上')
                
                # 如果所有启用的条件都满足，添加到结果中
                if all_conditions_met:
                    selected_stocks.append(stock_info)
                
            except Exception as e:
                self.logger.warning(f"处理股票 {stock_code} 时出错: {e}")
                continue
        
        # 按满足条件数量降序排列
        if selected_stocks:
            selected_stocks.sort(key=lambda x: len(x['conditions_met']), reverse=True)
        
        return selected_stocks
    
    def _is_excluded_exchange(self, stock_code: str) -> bool:
        """检查是否是需要排除的交易所股票"""
        code = stock_code.split('.')[0]
        return code.startswith('688') or code.startswith('8')
    
    def _is_st_stock(self, stock_code: str) -> bool:
        """检查是否为ST股票"""
        # 简化实现，实际需要获取股票名称
        return False
    
    def _has_limit_up_in_days(self, data: pd.DataFrame, days: int) -> bool:
        """检查指定天数内是否有涨停"""
        try:
            data['limit_up'] = data['close'].shift(1) * 1.1
            recent_data = data.tail(days)
            return (recent_data['close'] >= recent_data['limit_up'] * 0.99).any()
        except Exception as e:
            self.logger.warning(f"检查涨停失败: {e}")
            return False
    
    def _is_limit_up_today(self, data: pd.DataFrame) -> bool:
        """检查当日是否涨停"""
        try:
            if len(data) < 2:
                return False
            yesterday_close = data['close'].iloc[-2]
            today_close = data['close'].iloc[-1]
            limit_up_price = yesterday_close * 1.1
            return today_close >= limit_up_price * 0.99
        except Exception as e:
            self.logger.warning(f"检查当日涨停失败: {e}")
            return False
    
    def _is_limit_down_today(self, data: pd.DataFrame) -> bool:
        """检查当日是否跌停"""
        try:
            if len(data) < 2:
                return False
            yesterday_close = data['close'].iloc[-2]
            today_close = data['close'].iloc[-1]
            limit_down_price = yesterday_close * 0.9
            return today_close <= limit_down_price * 1.01
        except Exception as e:
            self.logger.warning(f"检查当日跌停失败: {e}")
            return False
    
    def _resample_to_weekly(self, daily_data: pd.DataFrame) -> pd.DataFrame:
        """将日线数据重采样为周线数据"""
        try:
            data = daily_data.copy()
            data['date'] = pd.to_datetime(data.index)
            data.set_index('date', inplace=True)
            
            weekly_data = data.resample('W').agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum'
            })
            
            return weekly_data.dropna()
        except Exception as e:
            self.logger.warning(f"周线重采样失败: {e}")
            return pd.DataFrame()
    
    def _calculate_kdj(self, data: pd.DataFrame, n: int = 9, m1: int = 3, m2: int = 3) -> pd.DataFrame:
        """计算KDJ指标"""
        try:
            low_min = data['low'].rolling(window=n).min()
            high_max = data['high'].rolling(window=n).max()
            rsv = 100 * ((data['close'] - low_min) / (high_max - low_min))
            
            k = rsv.ewm(span=m1).mean()
            d = k.ewm(span=m2).mean()
            j = 3 * k - 2 * d
            
            return pd.DataFrame({
                'K': k,
                'D': d,
                'J': j
            })
        except Exception as e:
            self.logger.warning(f"KDJ计算失败: {e}")
            return pd.DataFrame()
    
    def _calculate_macd(self, data: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
        """计算MACD指标"""
        try:
            ema_fast = data['close'].ewm(span=fast).mean()
            ema_slow = data['close'].ewm(span=slow).mean()
            
            macd = ema_fast - ema_slow
            macd_signal = macd.ewm(span=signal).mean()
            macd_histogram = macd - macd_signal
            
            return pd.DataFrame({
                'MACD': macd,
                'MACD_Signal': macd_signal,
                'MACD_Histogram': macd_histogram
            })
        except Exception as e:
            self.logger.warning(f"MACD计算失败: {e}")
            return pd.DataFrame()
    
    def _is_kdj_upward(self, kdj_data: pd.DataFrame) -> bool:
        """检查KDJ是否向上"""
        try:
            if kdj_data.empty or len(kdj_data) < 3:
                return False
            
            k_trend = kdj_data['K'].iloc[-1] > kdj_data['K'].iloc[-2]
            d_trend = kdj_data['D'].iloc[-1] > kdj_data['D'].iloc[-2]
            j_trend = kdj_data['J'].iloc[-1] > kdj_data['J'].iloc[-2]
            
            return sum([k_trend, d_trend, j_trend]) >= 2
        except Exception as e:
            self.logger.warning(f"KDJ趋势检查失败: {e}")
            return False
    
    def _is_macd_upward(self, macd_data: pd.DataFrame) -> bool:
        """检查MACD是否向上"""
        try:
            if macd_data.empty or len(macd_data) < 3:
                return False
            
            macd_trend = macd_data['MACD'].iloc[-1] > macd_data['MACD'].iloc[-2]
            signal_trend = macd_data['MACD_Signal'].iloc[-1] > macd_data['MACD_Signal'].iloc[-2]
            macd_above_signal = macd_data['MACD'].iloc[-1] > macd_data['MACD_Signal'].iloc[-1]
            
            return macd_trend and signal_trend and macd_above_signal
        except Exception as e:
            self.logger.warning(f"MACD趋势检查失败: {e}")
            return False
    
    def _is_volume_increasing(self, data: pd.DataFrame, days: int = 5) -> bool:
        """检查成交量是否升序"""
        try:
            if len(data) < days:
                return False
            
            recent_volumes = data['volume'].tail(days).values
            
            for i in range(1, len(recent_volumes)):
                if recent_volumes[i] <= recent_volumes[i-1]:
                    return False
            
            return True
        except Exception as e:
            self.logger.warning(f"成交量升序检查失败: {e}")
            return False
    
    def _is_price_trend_up(self, data: pd.DataFrame, days: int = 20) -> bool:
        """检查价格趋势是否向上"""
        try:
            if len(data) < days:
                return False
            
            start_price = data['close'].iloc[-days]
            end_price = data['close'].iloc[-1]
            
            return end_price > start_price
        except Exception as e:
            self.logger.warning(f"价格趋势检查失败: {e}")
            return False
    
    def _get_stock_name(self, stock_code: str) -> str:
        """获取股票名称"""
        return stock_code
    
    def get_available_conditions(self) -> List[Dict]:
        """获取可用的选股条件"""
        return [
            {'id': 'exclude_tech_board', 'name': '排除科创板北交所', 'description': '排除688开头和8开头的股票'},
            {'id': 'exclude_st', 'name': '排除ST股票', 'description': '排除ST、*ST等风险股票'},
            {'id': 'has_limit_up', 'name': '19天内有过涨停', 'description': '最近19个交易日内有过涨停'},
            {'id': 'not_limit_up_today', 'name': '当日未涨停', 'description': '当日收盘价未达到涨停价'},
            {'id': 'not_limit_down_today', 'name': '当日未跌停', 'description': '当日收盘价未达到跌停价'},
            {'id': 'weekly_kdj_up', 'name': '周线KDJ向上', 'description': '周线KDJ指标呈上升趋势'},
            {'id': 'weekly_macd_up', 'name': '周线MACD往上', 'description': '周线MACD指标呈上升趋势'},
            {'id': 'daily_macd_up', 'name': '日线MACD向上', 'description': '日线MACD指标呈上升趋势'},
            {'id': 'volume_increasing', 'name': '成交量升序', 'description': '最近5天成交量呈上升趋势'},
            {'id': 'price_trend_up', 'name': '价格趋势向上', 'description': '最近20天价格呈上升趋势'}
        ]
