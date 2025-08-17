"""
股票筛选器
提供多种选股策略，根据技术指标、基本面等条件筛选股票
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple
import logging
from datetime import datetime, timedelta

class StockScreener:
    """股票筛选器类"""
    
    def __init__(self, data_provider):
        """
        初始化股票筛选器
        
        Args:
            data_provider: 数据提供者实例
        """
        self.data_provider = data_provider
        self.logger = logging.getLogger(__name__)
    
    def screen_by_ma_cross(self, 
                           stock_list: List[str], 
                           short_window: int = 5,
                           long_window: int = 20,
                           min_price: float = 5.0,
                           max_price: float = 100.0) -> List[Dict]:
        """
        根据均线交叉策略选股
        
        Args:
            stock_list: 股票代码列表
            short_window: 短期均线周期
            long_window: 长期均线周期
            min_price: 最低价格
            max_price: 最高价格
            
        Returns:
            List[Dict]: 符合条件的股票列表
        """
        selected_stocks = []
        
        for stock_code in stock_list[:50]:  # 限制数量避免超时
            try:
                # 获取股票数据（根据聚宽账号权限调整日期范围）
                end_date = '2025-05-14'  # 聚宽账号权限限制
                start_date = '2024-05-07'  # 聚宽账号权限限制
                
                data = self.data_provider.get_daily_data(stock_code, start_date, end_date)
                
                if data.empty or len(data) < long_window:
                    continue
                
                # 计算均线
                data['MA_short'] = data['close'].rolling(window=short_window).mean()
                data['MA_long'] = data['close'].rolling(window=long_window).mean()
                
                # 获取最新数据
                latest = data.iloc[-1]
                prev = data.iloc[-2]
                
                # 检查价格范围
                if not (min_price <= latest['close'] <= max_price):
                    continue
                
                # 检查均线金叉
                golden_cross = (latest['MA_short'] > latest['MA_long'] and 
                               prev['MA_short'] <= prev['MA_long'])
                
                if golden_cross:
                    selected_stocks.append({
                        'code': stock_code,
                        'name': self._get_stock_name(stock_code),
                        'price': latest['close'],
                        'ma_short': latest['MA_short'],
                        'ma_long': latest['MA_long'],
                        'volume': latest['volume'],
                        'strategy': 'MA交叉策略',
                        'signal': '金叉买入'
                    })
                
            except Exception as e:
                self.logger.warning(f"处理股票 {stock_code} 时出错: {e}")
                continue
        
        return selected_stocks
    
    def screen_by_kdj_macd(self, 
                           stock_list: List[str],
                           kdj_n: int = 9,
                           kdj_m1: int = 3,
                           kdj_m2: int = 3,
                           macd_fast: int = 12,
                           macd_slow: int = 26,
                           macd_signal: int = 9,
                           min_price: float = 5.0,
                           max_price: float = 100.0) -> List[Dict]:
        """
        根据KDJ+MACD双重金叉策略选股
        
        Args:
            stock_list: 股票代码列表
            kdj_n: KDJ计算周期
            kdj_m1: KDJ的M1参数
            kdj_m2: KDJ的M2参数
            macd_fast: MACD快线周期
            macd_slow: MACD慢线周期
            macd_signal: MACD信号线周期
            min_price: 最低价格
            max_price: 最高价格
            
        Returns:
            List[Dict]: 符合条件的股票列表
        """
        selected_stocks = []
        
        for stock_code in stock_list[:50]:  # 限制数量避免超时
            try:
                # 获取股票数据（根据聚宽账号权限调整日期范围）
                end_date = '2025-05-14'  # 聚宽账号权限限制
                start_date = '2024-05-07'  # 聚宽账号权限限制
                
                data = self.data_provider.get_daily_data(stock_code, start_date, end_date)
                
                if data.empty or len(data) < max(kdj_n + kdj_m2, macd_slow + macd_signal):
                    continue
                
                # 计算KDJ
                low_min = data['low'].rolling(window=kdj_n).min()
                high_max = data['high'].rolling(window=kdj_n).max()
                rsv = 100 * ((data['close'] - low_min) / (high_max - low_min))
                
                data['K'] = rsv.ewm(span=kdj_m1).mean()
                data['D'] = data['K'].ewm(span=kdj_m2).mean()
                data['J'] = 3 * data['K'] - 2 * data['D']
                
                # 计算MACD
                ema_fast = data['close'].ewm(span=macd_fast).mean()
                ema_slow = data['close'].ewm(span=macd_slow).mean()
                data['MACD'] = ema_fast - ema_slow
                data['MACD_Signal'] = data['MACD'].ewm(span=macd_signal).mean()
                
                # 获取最新数据
                latest = data.iloc[-1]
                prev = data.iloc[-2]
                
                # 检查价格范围
                if not (min_price <= latest['close'] <= max_price):
                    continue
                
                # 检查双重金叉
                kdj_golden = (latest['K'] > latest['D'] and prev['K'] <= prev['D'])
                macd_golden = (latest['MACD'] > latest['MACD_Signal'] and 
                              prev['MACD'] <= prev['MACD_Signal'])
                
                if kdj_golden and macd_golden:
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
                        'strategy': 'KDJ+MACD双重金叉',
                        'signal': '双重金叉买入'
                    })
                
            except Exception as e:
                self.logger.warning(f"处理股票 {stock_code} 时出错: {e}")
                continue
        
        return selected_stocks
    
    def screen_by_volume_breakout(self, 
                                  stock_list: List[str],
                                  volume_ratio: float = 2.0,
                                  price_change: float = 0.05,
                                  min_price: float = 5.0,
                                  max_price: float = 100.0) -> List[Dict]:
        """
        根据放量突破策略选股
        
        Args:
            stock_list: 股票代码列表
            volume_ratio: 成交量放大倍数
            price_change: 价格变化幅度
            min_price: 最低价格
            max_price: 最高价格
            
        Returns:
            List[Dict]: 符合条件的股票列表
        """
        selected_stocks = []
        
        for stock_code in stock_list[:50]:  # 限制数量避免超时
            try:
                # 获取股票数据（根据聚宽账号权限调整日期范围）
                end_date = '2025-05-14'  # 聚宽账号权限限制
                start_date = '2024-05-07'  # 聚宽账号权限限制
                
                data = self.data_provider.get_daily_data(stock_code, start_date, end_date)
                
                if data.empty or len(data) < 20:
                    continue
                
                # 计算成交量均线
                data['Volume_MA5'] = data['volume'].rolling(window=5).mean()
                data['Volume_MA10'] = data['volume'].rolling(window=10).mean()
                
                # 计算价格变化
                data['price_change'] = data['close'].pct_change()
                
                # 获取最新数据
                latest = data.iloc[-1]
                prev = data.iloc[-2]
                
                # 检查价格范围
                if not (min_price <= latest['close'] <= max_price):
                    continue
                
                # 检查放量突破
                volume_breakout = (latest['volume'] > volume_ratio * latest['Volume_MA5'] and
                                 latest['volume'] > volume_ratio * latest['Volume_MA10'])
                
                price_breakout = abs(latest['price_change']) > price_change
                
                if volume_breakout and price_breakout:
                    selected_stocks.append({
                        'code': stock_code,
                        'name': self._get_stock_name(stock_code),
                        'price': latest['close'],
                        'volume': latest['volume'],
                        'volume_ma5': latest['Volume_MA5'],
                        'volume_ma10': latest['Volume_MA10'],
                        'price_change': latest['price_change'],
                        'strategy': '放量突破策略',
                        'signal': '放量突破'
                    })
                
            except Exception as e:
                self.logger.warning(f"处理股票 {stock_code} 时出错: {e}")
                continue
        
        return selected_stocks
    
    def screen_by_rsi_oversold(self, 
                               stock_list: List[str],
                               rsi_period: int = 14,
                               rsi_threshold: float = 30.0,
                               min_price: float = 5.0,
                               max_price: float = 100.0) -> List[Dict]:
        """
        根据RSI超卖策略选股
        
        Args:
            stock_list: 股票代码列表
            rsi_period: RSI计算周期
            rsi_threshold: RSI阈值
            min_price: 最低价格
            max_price: 最高价格
            
        Returns:
            List[Dict]: 符合条件的股票列表
        """
        selected_stocks = []
        
        for stock_code in stock_list[:50]:  # 限制数量避免超时
            try:
                # 获取股票数据（根据聚宽账号权限调整日期范围）
                end_date = '2025-05-14'  # 聚宽账号权限限制
                start_date = '2024-05-07'  # 聚宽账号权限限制
                
                data = self.data_provider.get_daily_data(stock_code, start_date, end_date)
                
                if data.empty or len(data) < rsi_period:
                    continue
                
                # 计算RSI
                delta = data['close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=rsi_period).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_period).mean()
                rs = gain / loss
                data['RSI'] = 100 - (100 / (1 + rs))
                
                # 获取最新数据
                latest = data.iloc[-1]
                
                # 检查价格范围
                if not (min_price <= latest['close'] <= max_price):
                    continue
                
                # 检查RSI超卖
                if latest['RSI'] < rsi_threshold:
                    selected_stocks.append({
                        'code': stock_code,
                        'name': self._get_stock_name(stock_code),
                        'price': latest['close'],
                        'rsi': latest['RSI'],
                        'volume': latest['volume'],
                        'strategy': 'RSI超卖策略',
                        'signal': 'RSI超卖'
                    })
                
            except Exception as e:
                self.logger.warning(f"处理股票 {stock_code} 时出错: {e}")
                continue
        
        return selected_stocks
    
    def screen_by_bollinger_bands(self, 
                                  stock_list: List[str],
                                  bb_period: int = 20,
                                  bb_std: float = 2.0,
                                  min_price: float = 5.0,
                                  max_price: float = 100.0) -> List[Dict]:
        """
        根据布林带策略选股
        
        Args:
            stock_list: 股票代码列表
            bb_period: 布林带计算周期
            bb_std: 标准差倍数
            min_price: 最低价格
            max_price: 最高价格
            
        Returns:
            List[Dict]: 符合条件的股票列表
        """
        selected_stocks = []
        
        for stock_code in stock_list[:50]:  # 限制数量避免超时
            try:
                # 获取股票数据（根据聚宽账号权限调整日期范围）
                end_date = '2025-05-14'  # 聚宽账号权限限制
                start_date = '2024-05-07'  # 聚宽账号权限限制
                
                data = self.data_provider.get_daily_data(stock_code, start_date, end_date)
                
                if data.empty or len(data) < bb_period:
                    continue
                
                # 计算布林带
                data['BB_Middle'] = data['close'].rolling(window=bb_period).mean()
                data['BB_Std'] = data['close'].rolling(window=bb_period).std()
                data['BB_Upper'] = data['BB_Middle'] + (bb_std * data['BB_Std'])
                data['BB_Lower'] = data['BB_Middle'] - (bb_std * data['BB_Std'])
                
                # 获取最新数据
                latest = data.iloc[-1]
                prev = data.iloc[-2]
                
                # 检查价格范围
                if not (min_price <= latest['close'] <= max_price):
                    continue
                
                # 检查布林带突破
                price_near_lower = latest['close'] <= latest['BB_Lower'] * 1.02  # 价格接近下轨
                volume_increase = latest['volume'] > data['volume'].rolling(window=5).mean().iloc[-1] * 1.5  # 成交量放大
                
                if price_near_lower and volume_increase:
                    selected_stocks.append({
                        'code': stock_code,
                        'name': self._get_stock_name(stock_code),
                        'price': latest['close'],
                        'bb_middle': latest['BB_Middle'],
                        'bb_lower': latest['BB_Lower'],
                        'bb_position': (latest['close'] - latest['BB_Lower']) / (latest['BB_Upper'] - latest['BB_Lower']),
                        'volume': latest['volume'],
                        'strategy': '布林带策略',
                        'signal': '布林带下轨支撑'
                    })
                
            except Exception as e:
                self.logger.warning(f"处理股票 {stock_code} 时出错: {e}")
                continue
        
        return selected_stocks
    
    def screen_by_momentum(self, 
                           stock_list: List[str],
                           momentum_period: int = 10,
                           momentum_threshold: float = 0.05,
                           min_price: float = 5.0,
                           max_price: float = 100.0) -> List[Dict]:
        """
        根据动量策略选股
        
        Args:
            stock_list: 股票代码列表
            momentum_period: 动量计算周期
            momentum_threshold: 动量阈值
            min_price: 最低价格
            max_price: 最高价格
            
        Returns:
            List[Dict]: 符合条件的股票列表
        """
        selected_stocks = []
        
        for stock_code in stock_list[:50]:  # 限制数量避免超时
            try:
                # 获取股票数据（根据聚宽账号权限调整日期范围）
                end_date = '2025-05-14'  # 聚宽账号权限限制
                start_date = '2024-05-07'  # 聚宽账号权限限制
                
                data = self.data_provider.get_daily_data(stock_code, start_date, end_date)
                
                if data.empty or len(data) < momentum_period + 5:
                    continue
                
                # 计算动量指标
                data['momentum'] = data['close'].pct_change(periods=momentum_period)
                data['momentum_ma'] = data['momentum'].rolling(window=5).mean()
                data['volume_ratio'] = data['volume'] / data['volume'].rolling(window=10).mean()
                
                # 处理无穷大和NaN值
                data['momentum'] = data['momentum'].replace([np.inf, -np.inf], np.nan)
                data['volume_ratio'] = data['volume_ratio'].replace([np.inf, -np.inf], np.nan)
                data = data.dropna()
                
                # 获取最新数据
                latest = data.iloc[-1]
                
                # 检查价格范围
                if not (min_price <= latest['close'] <= max_price):
                    continue
                
                # 检查动量条件
                positive_momentum = latest['momentum'] > momentum_threshold
                momentum_increasing = latest['momentum'] > latest['momentum_ma']
                volume_support = latest['volume_ratio'] > 1.2
                
                if positive_momentum and momentum_increasing and volume_support:
                    selected_stocks.append({
                        'code': stock_code,
                        'name': self._get_stock_name(stock_code),
                        'price': latest['close'],
                        'momentum': latest['momentum'],
                        'momentum_ma': latest['momentum_ma'],
                        'volume_ratio': latest['volume_ratio'],
                        'strategy': '动量策略',
                        'signal': '动量增强'
                    })
                
            except Exception as e:
                self.logger.warning(f"处理股票 {stock_code} 时出错: {e}")
                continue
        
        return selected_stocks
    
    def screen_by_dual_strategy(self, 
                                stock_list: List[str],
                                strategy1: str = 'ma_cross',
                                strategy2: str = 'rsi_oversold',
                                min_price: float = 5.0,
                                max_price: float = 100.0) -> List[Dict]:
        """
        双重策略选股（两个策略同时满足）
        
        Args:
            stock_list: 股票代码列表
            strategy1: 第一个策略
            strategy2: 第二个策略
            min_price: 最低价格
            max_price: 最高价格
            
        Returns:
            List[Dict]: 符合条件的股票列表
        """
        selected_stocks = []
        
        for stock_code in stock_list[:30]:  # 限制数量避免超时
            try:
                # 获取股票数据（根据聚宽账号权限调整日期范围）
                end_date = '2025-05-14'  # 聚宽账号权限限制
                start_date = '2024-05-07'  # 聚宽账号权限限制
                
                data = self.data_provider.get_daily_data(stock_code, start_date, end_date)
                
                if data.empty or len(data) < 30:
                    continue
                
                # 检查价格范围
                latest_price = data['close'].iloc[-1]
                if not (min_price <= latest_price <= max_price):
                    continue
                
                # 执行第一个策略检查
                strategy1_result = False
                if strategy1 == 'ma_cross':
                    data['MA_short'] = data['close'].rolling(window=5).mean()
                    data['MA_long'] = data['close'].rolling(window=20).mean()
                    latest = data.iloc[-1]
                    prev = data.iloc[-2]
                    strategy1_result = (latest['MA_short'] > latest['MA_long'] and 
                                      prev['MA_short'] <= prev['MA_long'])
                
                elif strategy1 == 'rsi_oversold':
                    delta = data['close'].diff()
                    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                    rs = gain / loss
                    data['RSI'] = 100 - (100 / (1 + rs))
                    strategy1_result = data['RSI'].iloc[-1] < 30
                
                # 执行第二个策略检查
                strategy2_result = False
                if strategy2 == 'volume_breakout':
                    data['Volume_MA5'] = data['volume'].rolling(window=5).mean()
                    data['Volume_MA10'] = data['volume'].rolling(window=10).mean()
                    latest = data.iloc[-1]
                    strategy2_result = (latest['volume'] > 2.0 * latest['Volume_MA5'] and
                                      latest['volume'] > 2.0 * latest['Volume_MA10'])
                
                elif strategy2 == 'kdj_golden':
                    low_min = data['low'].rolling(window=9).min()
                    high_max = data['high'].rolling(window=9).max()
                    rsv = 100 * ((data['close'] - low_min) / (high_max - low_min))
                    data['K'] = rsv.ewm(span=3).mean()
                    data['D'] = data['K'].ewm(span=3).mean()
                    latest = data.iloc[-1]
                    prev = data.iloc[-2]
                    strategy2_result = (latest['K'] > latest['D'] and prev['K'] <= prev['D'])
                
                # 两个策略都满足
                if strategy1_result and strategy2_result:
                    selected_stocks.append({
                        'code': stock_code,
                        'name': self._get_stock_name(stock_code),
                        'price': latest_price,
                        'strategy1': strategy1,
                        'strategy2': strategy2,
                        'strategy': f'{strategy1}+{strategy2}双重策略',
                        'signal': '双重信号确认'
                    })
                
            except Exception as e:
                self.logger.warning(f"处理股票 {stock_code} 时出错: {e}")
                continue
        
        return selected_stocks
    
    def screen_by_industry_rotation(self, 
                                   industry_list: List[str] = None,
                                   min_price: float = 5.0,
                                   max_price: float = 100.0) -> List[Dict]:
        """
        行业轮动策略选股
        
        Args:
            industry_list: 行业列表，如果为None则使用默认行业
            min_price: 最低价格
            max_price: 最高价格
            
        Returns:
            List[Dict]: 符合条件的股票列表
        """
        if industry_list is None:
            # 默认关注的热门行业
            industry_list = ['计算机', '电子', '医药生物', '新能源', '消费']
        
        selected_stocks = []
        
        try:
            for industry in industry_list:
                # 获取行业成分股
                industry_stocks = self.data_provider.get_industry_stocks(industry)
                if not industry_stocks:
                    continue
                
                # 限制每个行业的股票数量
                sample_stocks = industry_stocks[:20]
                
                for stock_code in sample_stocks:
                    try:
                        # 获取股票数据
                        end_date = '2025-05-14'
                        start_date = '2024-05-07'
                        
                        data = self.data_provider.get_daily_data(stock_code, start_date, end_date)
                        
                        if data.empty or len(data) < 20:
                            continue
                        
                        # 计算行业相对强度
                        data['price_change'] = data['close'].pct_change()
                        data['relative_strength'] = data['price_change'].rolling(window=10).mean()
                        
                        # 获取最新数据
                        latest = data.iloc[-1]
                        
                        # 检查价格范围
                        if not (min_price <= latest['close'] <= max_price):
                            continue
                        
                        # 检查行业轮动条件
                        strong_relative_strength = latest['relative_strength'] > 0.02
                        volume_support = latest['volume'] > data['volume'].rolling(window=10).mean().iloc[-1] * 1.3
                        
                        if strong_relative_strength and volume_support:
                            selected_stocks.append({
                                'code': stock_code,
                                'name': self._get_stock_name(stock_code),
                                'industry': industry,
                                'price': latest['close'],
                                'relative_strength': latest['relative_strength'],
                                'volume_ratio': latest['volume'] / data['volume'].rolling(window=10).mean().iloc[-1],
                                'strategy': '行业轮动策略',
                                'signal': f'{industry}行业强势'
                            })
                    
                    except Exception as e:
                        self.logger.warning(f"处理股票 {stock_code} 时出错: {e}")
                        continue
                        
        except Exception as e:
            self.logger.error(f"行业轮动选股失败: {e}")
        
        return selected_stocks
    
    def _get_stock_name(self, stock_code: str) -> str:
        """获取股票名称（简化实现）"""
        # 这里可以扩展为从聚宽获取股票名称
        # 暂时返回代码作为名称
        return stock_code
    
    def get_all_strategies(self) -> List[Dict]:
        """获取所有可用的选股策略"""
        return [
            {
                'id': 'ma_cross',
                'name': '均线交叉策略',
                'description': '根据短期均线上穿长期均线选股',
                'parameters': ['short_window', 'long_window', 'min_price', 'max_price']
            },
            {
                'id': 'kdj_macd',
                'name': 'KDJ+MACD双重金叉',
                'description': '根据KDJ和MACD同时金叉选股',
                'parameters': ['kdj_n', 'kdj_m1', 'kdj_m2', 'macd_fast', 'macd_slow', 'macd_signal', 'min_price', 'max_price']
            },
            {
                'id': 'volume_breakout',
                'name': '放量突破策略',
                'description': '根据成交量和价格突破选股',
                'parameters': ['volume_ratio', 'price_change', 'min_price', 'max_price']
            },
            {
                'id': 'rsi_oversold',
                'name': 'RSI超卖策略',
                'description': '根据RSI超卖信号选股',
                'parameters': ['rsi_period', 'rsi_threshold', 'min_price', 'max_price']
            },
            {
                'id': 'bollinger_bands',
                'name': '布林带策略',
                'description': '根据布林带突破选股',
                'parameters': ['bb_period', 'bb_std', 'min_price', 'max_price']
            },
            {
                'id': 'momentum',
                'name': '动量策略',
                'description': '根据动量指标选股',
                'parameters': ['momentum_period', 'momentum_threshold', 'min_price', 'max_price']
            },
            {
                'id': 'dual_strategy',
                'name': '双重策略',
                'description': '两个策略同时满足',
                'parameters': ['strategy1', 'strategy2', 'min_price', 'max_price']
            },
            {
                'id': 'industry_rotation',
                'name': '行业轮动策略',
                'description': '根据行业相对强度和成交量选股',
                'parameters': ['industry_list', 'min_price', 'max_price']
            }
        ]

    def calculate_strategy_score(self, stock_data: pd.DataFrame, strategy_type: str) -> float:
        """
        计算策略评分
        
        Args:
            stock_data: 股票数据
            strategy_type: 策略类型
            
        Returns:
            float: 策略评分 (0-100)
        """
        try:
            if stock_data.empty or len(stock_data) < 20:
                return 0.0
            
            score = 0.0
            
            if strategy_type == 'ma_cross':
                # 均线交叉策略评分
                data = stock_data.copy()
                data['MA_short'] = data['close'].rolling(window=5).mean()
                data['MA_long'] = data['close'].rolling(window=20).mean()
                
                # 均线趋势
                ma_trend = (data['MA_short'].iloc[-1] - data['MA_short'].iloc[-5]) / data['MA_short'].iloc[-5]
                score += max(0, ma_trend * 50)  # 趋势得分
                
                # 价格位置
                price_position = (data['close'].iloc[-1] - data['low'].rolling(window=20).min().iloc[-1]) / \
                               (data['high'].rolling(window=20).max().iloc[-1] - data['low'].rolling(window=20).min().iloc[-1])
                score += price_position * 30  # 价格位置得分
                
                # 成交量支持
                volume_support = data['volume'].iloc[-1] / data['volume'].rolling(window=10).mean().iloc[-1]
                score += min(volume_support * 10, 20)  # 成交量得分
                
            elif strategy_type == 'rsi_oversold':
                # RSI超卖策略评分
                data = stock_data.copy()
                delta = data['close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss
                data['RSI'] = 100 - (100 / (1 + rs))
                
                rsi_value = data['RSI'].iloc[-1]
                if rsi_value < 30:
                    score += (30 - rsi_value) * 2  # RSI超卖程度得分
                
                # 价格反弹信号
                price_rebound = (data['close'].iloc[-1] - data['close'].iloc[-3]) / data['close'].iloc[-3]
                if price_rebound > 0:
                    score += price_rebound * 50  # 反弹力度得分
                
            elif strategy_type == 'momentum':
                # 动量策略评分
                data = stock_data.copy()
                data['momentum'] = data['close'].pct_change(periods=10)
                data['momentum_ma'] = data['momentum'].rolling(window=5).mean()
                
                momentum_strength = data['momentum'].iloc[-1]
                score += max(0, momentum_strength * 100)  # 动量强度得分
                
                # 动量持续性
                momentum_consistency = (data['momentum'] > 0).rolling(window=5).sum().iloc[-1] / 5
                score += momentum_consistency * 30  # 持续性得分
                
            # 通用评分因素
            # 波动率评分（适中的波动率更好）
            volatility = data['close'].pct_change().std()
            if 0.01 < volatility < 0.05:  # 适中的波动率
                score += 20
            elif volatility < 0.01:  # 低波动率
                score += 10
            
            # 价格趋势评分
            price_trend = (data['close'].iloc[-1] - data['close'].iloc[-20]) / data['close'].iloc[-20]
            score += max(0, price_trend * 25)  # 长期趋势得分
            
            return min(score, 100.0)  # 限制最高分为100
            
        except Exception as e:
            self.logger.warning(f"计算策略评分失败: {e}")
            return 0.0
    
    def rank_stocks_by_score(self, selected_stocks: List[Dict], strategy_type: str) -> List[Dict]:
        """
        根据策略评分对选股结果进行排序
        
        Args:
            selected_stocks: 选股结果列表
            strategy_type: 策略类型
            
        Returns:
            List[Dict]: 排序后的选股结果
        """
        if not selected_stocks:
            return []
        
        try:
            # 为每只股票计算评分
            for stock in selected_stocks:
                stock_code = stock['code']
                
                # 获取股票数据用于评分计算
                end_date = '2025-05-14'
                start_date = '2024-05-07'
                
                data = self.data_provider.get_daily_data(stock_code, start_date, end_date)
                
                if not data.empty:
                    score = self.calculate_strategy_score(data, strategy_type)
                    stock['strategy_score'] = round(score, 2)
                else:
                    stock['strategy_score'] = 0.0
            
            # 按评分降序排序
            ranked_stocks = sorted(selected_stocks, key=lambda x: x.get('strategy_score', 0), reverse=True)
            
            return ranked_stocks
            
        except Exception as e:
            self.logger.error(f"股票排序失败: {e}")
            return selected_stocks
    
    def get_strategy_recommendations(self, stock_list: List[str], top_n: int = 5) -> Dict:
        """
        获取策略推荐（综合多个策略的结果）
        
        Args:
            stock_list: 股票代码列表
            top_n: 推荐股票数量
            
        Returns:
            Dict: 策略推荐结果
        """
        recommendations = {}
        
        try:
            # 执行所有策略
            strategies = [
                ('ma_cross', '均线交叉策略'),
                ('rsi_oversold', 'RSI超卖策略'),
                ('momentum', '动量策略'),
                ('bollinger_bands', '布林带策略')
            ]
            
            for strategy_id, strategy_name in strategies:
                try:
                    if strategy_id == 'ma_cross':
                        results = self.screen_by_ma_cross(stock_list[:30], 5, 20, 5.0, 100.0)
                    elif strategy_id == 'rsi_oversold':
                        results = self.screen_by_rsi_oversold(stock_list[:30], 14, 30.0, 5.0, 100.0)
                    elif strategy_id == 'momentum':
                        results = self.screen_by_momentum(stock_list[:30], 10, 0.03, 5.0, 100.0)
                    elif strategy_id == 'bollinger_bands':
                        results = self.screen_by_bollinger_bands(stock_list[:30], 20, 2.0, 5.0, 100.0)
                    
                    if results:
                        # 计算评分并排序
                        ranked_results = self.rank_stocks_by_score(results, strategy_id)
                        recommendations[strategy_name] = ranked_results[:top_n]
                    else:
                        recommendations[strategy_name] = []
                        
                except Exception as e:
                    self.logger.warning(f"{strategy_name} 推荐生成失败: {e}")
                    recommendations[strategy_name] = []
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"策略推荐生成失败: {e}")
            return {}
