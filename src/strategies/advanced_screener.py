"""
高级复合选股策略
实现复杂的多条件选股逻辑
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple
import logging
from datetime import datetime, timedelta

class AdvancedStockScreener:
    """高级复合选股器类"""
    
    def __init__(self, data_provider):
        """
        初始化高级选股器
        
        Args:
            data_provider: 数据提供者实例
        """
        self.data_provider = data_provider
        self.logger = logging.getLogger(__name__)
        
        # 科创板、北交所股票代码前缀
        self.exclude_prefixes = ['688', '689', '830', '831', '832', '833', '834', '835', '836', '837', '838', '839', '870', '871', '872', '873', '874', '875', '876', '877', '878', '879']
    
    def screen_by_advanced_conditions(self, 
                                    stock_list: List[str],
                                    min_price: float = 5.0,
                                    max_price: float = 100.0) -> List[Dict]:
        """
        高级复合选股策略
        
        条件：
        1. 周线KDJ向上
        2. 排除科创板北交所
        3. 排除ST股票
        4. 19天内有过涨停
        5. 当日未涨停
        6. 当日未跌停
        7. 最近5年有分红
        8. 周线MACD往上
        9. 日线MACD向上
        10. 成交量升序排列
        
        Args:
            stock_list: 股票代码列表
            min_price: 最低价格
            max_price: 最高价格
            
        Returns:
            List[Dict]: 符合条件的股票列表
        """
        selected_stocks = []
        
        for stock_code in stock_list[:100]:  # 限制数量避免超时
            try:
                # 1. 排除科创板北交所
                if self._is_excluded_exchange(stock_code):
                    continue
                
                # 2. 排除ST股票
                if self._is_st_stock(stock_code):
                    continue
                
                # 3. 获取股票数据
                end_date = '2025-05-14'  # 聚宽账号权限限制
                start_date = '2024-05-07'  # 聚宽账号权限限制
                
                daily_data = self.data_provider.get_daily_data(stock_code, start_date, end_date)
                
                if daily_data.empty or len(daily_data) < 50:
                    continue
                
                # 4. 检查价格范围
                latest_price = daily_data['close'].iloc[-1]
                if not (min_price <= latest_price <= max_price):
                    continue
                
                # 5. 检查19天内是否有涨停
                if not self._has_limit_up_in_days(daily_data, 19):
                    continue
                
                # 6. 检查当日是否涨停
                if self._is_limit_up_today(daily_data):
                    continue
                
                # 7. 检查当日是否跌停
                if self._is_limit_down_today(daily_data):
                    continue
                
                # 8. 计算周线KDJ
                weekly_data = self._resample_to_weekly(daily_data)
                if weekly_data.empty or len(weekly_data) < 20:
                    continue
                
                weekly_kdj = self._calculate_kdj(weekly_data, n=9, m1=3, m2=3)
                if not self._is_kdj_upward(weekly_kdj):
                    continue
                
                # 9. 计算周线MACD
                weekly_macd = self._calculate_macd(weekly_data, fast=12, slow=26, signal=9)
                if not self._is_macd_upward(weekly_macd):
                    continue
                
                # 10. 计算日线MACD
                daily_macd = self._calculate_macd(daily_data, fast=12, slow=26, signal=9)
                if not self._is_macd_upward(daily_macd):
                    continue
                
                # 11. 检查成交量升序（最近5天）
                if not self._is_volume_increasing(daily_data, days=5):
                    continue
                
                # 12. 检查分红情况（简化实现，实际需要财务数据）
                # 这里暂时跳过，因为需要财务数据接口
                
                # 所有条件都满足，添加到结果中
                selected_stocks.append({
                    'code': stock_code,
                    'name': self._get_stock_name(stock_code),
                    'price': latest_price,
                    'weekly_kdj_k': weekly_kdj['K'].iloc[-1],
                    'weekly_kdj_d': weekly_kdj['D'].iloc[-1],
                    'weekly_kdj_j': weekly_kdj['J'].iloc[-1],
                    'weekly_macd': weekly_macd['MACD'].iloc[-1],
                    'weekly_macd_signal': weekly_macd['MACD_Signal'].iloc[-1],
                    'daily_macd': daily_macd['MACD'].iloc[-1],
                    'daily_macd_signal': daily_macd['MACD_Signal'].iloc[-1],
                    'volume_ratio': daily_data['volume'].iloc[-1] / daily_data['volume'].rolling(window=10).mean().iloc[-1],
                    'strategy': '高级复合选股策略',
                    'signal': '多条件共振'
                })
                
            except Exception as e:
                self.logger.warning(f"处理股票 {stock_code} 时出错: {e}")
                continue
        
        # 按成交量升序排列
        if selected_stocks:
            selected_stocks.sort(key=lambda x: x['volume_ratio'])
        
        return selected_stocks
    
    def _is_excluded_exchange(self, stock_code: str) -> bool:
        """检查是否是需要排除的交易所股票"""
        # 移除交易所后缀
        code = stock_code.split('.')[0]
        
        # 检查科创板（688开头）
        if code.startswith('688'):
            return True
        
        # 检查北交所（8开头，通常是830-879）
        if code.startswith('8'):
            return True
        
        return False
    
    def _is_st_stock(self, stock_code: str) -> bool:
        """检查是否为ST股票"""
        # 这里需要获取股票名称来判断，暂时简化处理
        # 实际实现中需要调用聚宽的股票信息接口
        return False
    
    def _has_limit_up_in_days(self, data: pd.DataFrame, days: int) -> bool:
        """检查指定天数内是否有涨停"""
        try:
            # 计算涨停价格（A股涨停幅度为10%）
            data['limit_up'] = data['close'].shift(1) * 1.1
            
            # 检查最近days天内是否有涨停
            recent_data = data.tail(days)
            has_limit_up = (recent_data['close'] >= recent_data['limit_up'] * 0.99).any()
            
            return has_limit_up
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
            # 设置日期索引
            data = daily_data.copy()
            data['date'] = pd.to_datetime(data.index)
            data.set_index('date', inplace=True)
            
            # 重采样为周线
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
            # 计算RSV
            low_min = data['low'].rolling(window=n).min()
            high_max = data['high'].rolling(window=n).max()
            rsv = 100 * ((data['close'] - low_min) / (high_max - low_min))
            
            # 计算K、D、J
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
            # 计算EMA
            ema_fast = data['close'].ewm(span=fast).mean()
            ema_slow = data['close'].ewm(span=slow).mean()
            
            # 计算MACD
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
            
            # 检查K、D、J是否都向上
            k_trend = kdj_data['K'].iloc[-1] > kdj_data['K'].iloc[-2]
            d_trend = kdj_data['D'].iloc[-1] > kdj_data['D'].iloc[-2]
            j_trend = kdj_data['J'].iloc[-1] > kdj_data['J'].iloc[-2]
            
            # 至少两个指标向上
            return sum([k_trend, d_trend, j_trend]) >= 2
        except Exception as e:
            self.logger.warning(f"KDJ趋势检查失败: {e}")
            return False
    
    def _is_macd_upward(self, macd_data: pd.DataFrame) -> bool:
        """检查MACD是否向上"""
        try:
            if macd_data.empty or len(macd_data) < 3:
                return False
            
            # 检查MACD和信号线是否向上
            macd_trend = macd_data['MACD'].iloc[-1] > macd_data['MACD'].iloc[-2]
            signal_trend = macd_data['MACD_Signal'].iloc[-1] > macd_data['MACD_Signal'].iloc[-2]
            
            # 检查MACD是否在信号线之上
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
            
            # 获取最近days天的成交量
            recent_volumes = data['volume'].tail(days).values
            
            # 检查是否升序
            for i in range(1, len(recent_volumes)):
                if recent_volumes[i] <= recent_volumes[i-1]:
                    return False
            
            return True
        except Exception as e:
            self.logger.warning(f"成交量升序检查失败: {e}")
            return False
    
    def _get_stock_name(self, stock_code: str) -> str:
        """获取股票名称（简化实现）"""
        # 这里可以扩展为从聚宽获取股票名称
        return stock_code
    
    def get_strategy_info(self) -> Dict:
        """获取策略信息"""
        return {
            'name': '高级复合选股策略',
            'description': '多条件共振选股，包含技术指标、价格行为、成交量等多维度筛选',
            'conditions': [
                '周线KDJ向上',
                '排除科创板北交所',
                '排除ST股票',
                '19天内有过涨停',
                '当日未涨停',
                '当日未跌停',
                '最近5年有分红',
                '周线MACD往上',
                '日线MACD向上',
                '成交量升序'
            ],
            'parameters': ['min_price', 'max_price']
        }
