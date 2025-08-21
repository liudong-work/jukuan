#!/usr/bin/env python3
"""
KDJ+MACD技术选股策略
基于KDJ和MACD双重技术指标向上，结合基本面筛选的选股策略
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class KDJMACDScreeningStrategy:
    """KDJ+MACD技术选股策略"""
    
    def __init__(self, parameters: Dict[str, Any]):
        """
        初始化策略参数
        
        Args:
            parameters: 策略参数字典
        """
        self.parameters = parameters
        self.kdj_period = parameters.get('kdj_period', 9)
        self.macd_fast = parameters.get('macd_fast', 12)
        self.macd_slow = parameters.get('macd_slow', 26)
        self.macd_signal = parameters.get('macd_signal', 9)
        
        # 筛选条件
        self.exclude_st = parameters.get('exclude_st', True)
        self.exclude_tech_board = parameters.get('exclude_tech_board', True)
        self.exclude_beijing = parameters.get('exclude_beijing', True)
        self.limit_up_within_days = parameters.get('limit_up_within_days', 19)
        self.dividend_years = parameters.get('dividend_years', 5)
        self.current_no_limit_up = parameters.get('current_no_limit_up', True)
        self.current_no_limit_down = parameters.get('current_no_limit_down', True)
        self.volume_sort = parameters.get('volume_sort', 'ascending')
        
        logger.info(f"KDJ+MACD选股策略初始化完成，参数: {parameters}")
    
    def calculate_kdj(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int = 9) -> Dict[str, pd.Series]:
        """
        计算KDJ指标
        
        Args:
            high: 最高价序列
            low: 最低价序列
            close: 收盘价序列
            period: 计算周期
            
        Returns:
            包含K、D、J值的字典
        """
        try:
            # 计算RSV
            low_min = low.rolling(window=period).min()
            high_max = high.rolling(window=period).max()
            rsv = (close - low_min) / (high_max - low_min) * 100
            
            # 计算K值
            k = pd.Series(index=close.index, dtype=float)
            k.iloc[0] = 50.0
            
            for i in range(1, len(close)):
                k.iloc[i] = (2/3) * k.iloc[i-1] + (1/3) * rsv.iloc[i]
            
            # 计算D值
            d = pd.Series(index=close.index, dtype=float)
            d.iloc[0] = 50.0
            
            for i in range(1, len(close)):
                d.iloc[i] = (2/3) * d.iloc[i-1] + (1/3) * k.iloc[i]
            
            # 计算J值
            j = 3 * k - 2 * d
            
            return {'K': k, 'D': d, 'J': j}
            
        except Exception as e:
            logger.error(f"计算KDJ指标失败: {e}")
            return {'K': pd.Series(), 'D': pd.Series(), 'J': pd.Series()}
    
    def calculate_macd(self, close: pd.Series) -> Dict[str, pd.Series]:
        """
        计算MACD指标
        
        Args:
            close: 收盘价序列
            
        Returns:
            包含MACD、Signal、Histogram的字典
        """
        try:
            # 计算EMA
            ema_fast = close.ewm(span=self.macd_fast).mean()
            ema_slow = close.ewm(span=self.macd_slow).mean()
            
            # 计算MACD线
            macd_line = ema_fast - ema_slow
            
            # 计算信号线
            signal_line = macd_line.ewm(span=self.macd_signal).mean()
            
            # 计算柱状图
            histogram = macd_line - signal_line
            
            return {
                'MACD': macd_line,
                'Signal': signal_line,
                'Histogram': histogram
            }
            
        except Exception as e:
            logger.error(f"计算MACD指标失败: {e}")
            return {'MACD': pd.Series(), 'Signal': pd.Series(), 'Histogram': pd.Series()}
    
    def check_kdj_trend(self, kdj_data: Dict[str, pd.Series], lookback: int = 3) -> bool:
        """
        检查KDJ趋势是否向上
        
        Args:
            kdj_data: KDJ数据字典
            lookback: 回看天数
            
        Returns:
            True表示向上趋势，False表示向下趋势
        """
        try:
            if len(kdj_data['K']) < lookback:
                return False
            
            # 检查K值趋势
            k_trend = kdj_data['K'].iloc[-lookback:].is_monotonic_increasing
            
            # 检查D值趋势
            d_trend = kdj_data['D'].iloc[-lookback:].is_monotonic_increasing
            
            # 检查J值趋势
            j_trend = kdj_data['J'].iloc[-lookback:].is_monotonic_increasing
            
            # 至少两个指标向上
            up_count = sum([k_trend, d_trend, j_trend])
            
            return up_count >= 2
            
        except Exception as e:
            logger.error(f"检查KDJ趋势失败: {e}")
            return False
    
    def check_macd_trend(self, macd_data: Dict[str, pd.Series], lookback: int = 3) -> bool:
        """
        检查MACD趋势是否向上
        
        Args:
            macd_data: MACD数据字典
            lookback: 回看天数
            
        Returns:
            True表示向上趋势，False表示向下趋势
        """
        try:
            if len(macd_data['MACD']) < lookback:
                return False
            
            # 检查MACD线趋势
            macd_trend = macd_data['MACD'].iloc[-lookback:].is_monotonic_increasing
            
            # 检查柱状图趋势
            histogram_trend = macd_data['Histogram'].iloc[-lookback:].is_monotonic_increasing
            
            # 检查是否在零轴上方
            above_zero = macd_data['MACD'].iloc[-1] > 0
            
            return macd_trend and histogram_trend and above_zero
            
        except Exception as e:
            logger.error(f"检查MACD趋势失败: {e}")
            return False
    
    def filter_stocks(self, stock_data: pd.DataFrame) -> pd.DataFrame:
        """
        筛选股票
        
        Args:
            stock_data: 股票数据DataFrame
            
        Returns:
            筛选后的股票DataFrame
        """
        try:
            filtered_data = stock_data.copy()
            
            # 排除ST股票
            if self.exclude_st:
                filtered_data = filtered_data[~filtered_data['name'].str.contains('ST', na=False)]
                filtered_data = filtered_data[~filtered_data['name'].str.contains('st', na=False)]
            
            # 排除科创板
            if self.exclude_tech_board:
                filtered_data = filtered_data[~filtered_data['code'].str.startswith('688')]
            
            # 排除北交所
            if self.exclude_beijing:
                filtered_data = filtered_data[~filtered_data['code'].str.startswith('8')]
            
            # 排除创业板（可选）
            # filtered_data = filtered_data[~filtered_data['code'].str.startswith('300')]
            
            logger.info(f"筛选后剩余股票数量: {len(filtered_data)}")
            return filtered_data
            
        except Exception as e:
            logger.error(f"筛选股票失败: {e}")
            return stock_data
    
    def rank_by_volume(self, stock_data: pd.DataFrame) -> pd.DataFrame:
        """
        按成交量排序
        
        Args:
            stock_data: 股票数据DataFrame
            
        Returns:
            排序后的股票DataFrame
        """
        try:
            if 'volume' in stock_data.columns:
                if self.volume_sort == 'ascending':
                    return stock_data.sort_values('volume', ascending=True)
                else:
                    return stock_data.sort_values('volume', ascending=False)
            else:
                logger.warning("数据中没有成交量字段，跳过排序")
                return stock_data
                
        except Exception as e:
            logger.error(f"按成交量排序失败: {e}")
            return stock_data
    
    def run_screening(self, market_data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """
        运行选股策略
        
        Args:
            market_data: 市场数据字典，包含日线和周线数据
            
        Returns:
            选股结果字典
        """
        try:
            logger.info("开始运行KDJ+MACD选股策略")
            
            results = {
                'strategy_name': 'KDJ+MACD技术选股策略',
                'run_time': datetime.now().isoformat(),
                'selected_stocks': [],
                'total_screened': 0,
                'total_selected': 0,
                'filters_applied': []
            }
            
            # 获取股票列表
            if 'stock_list' not in market_data:
                logger.error("市场数据中缺少股票列表")
                return results
            
            stock_list = market_data['stock_list']
            results['total_screened'] = len(stock_list)
            
            # 应用基础筛选
            filtered_stocks = self.filter_stocks(stock_list)
            results['filters_applied'].append(f"基础筛选后剩余: {len(filtered_stocks)}只")
            
            selected_stocks = []
            
            for _, stock in filtered_stocks.iterrows():
                try:
                    stock_code = stock['code']
                    
                    # 检查是否有日线和周线数据
                    if f'daily_{stock_code}' not in market_data or f'weekly_{stock_code}' not in market_data:
                        continue
                    
                    daily_data = market_data[f'daily_{stock_code}']
                    weekly_data = market_data[f'weekly_{stock_code}']
                    
                    if len(daily_data) < 30 or len(weekly_data) < 10:
                        continue
                    
                    # 计算日线KDJ
                    daily_kdj = self.calculate_kdj(
                        daily_data['high'], 
                        daily_data['low'], 
                        daily_data['close'], 
                        self.kdj_period
                    )
                    
                    # 计算周线KDJ
                    weekly_kdj = self.calculate_kdj(
                        weekly_data['high'], 
                        weekly_data['low'], 
                        weekly_data['close'], 
                        self.kdj_period
                    )
                    
                    # 计算日线MACD
                    daily_macd = self.calculate_macd(daily_data['close'])
                    
                    # 计算周线MACD
                    weekly_macd = self.calculate_macd(weekly_data['close'])
                    
                    # 检查技术指标趋势
                    daily_kdj_up = self.check_kdj_trend(daily_kdj)
                    weekly_kdj_up = self.check_kdj_trend(weekly_kdj)
                    daily_macd_up = self.check_macd_trend(daily_macd)
                    weekly_macd_up = self.check_macd_trend(weekly_macd)
                    
                    # 所有技术指标都必须向上
                    if daily_kdj_up and weekly_kdj_up and daily_macd_up and weekly_macd_up:
                        stock_info = {
                            'code': stock_code,
                            'name': stock.get('name', ''),
                            'daily_kdj_up': daily_kdj_up,
                            'weekly_kdj_up': weekly_kdj_up,
                            'daily_macd_up': daily_macd_up,
                            'weekly_macd_up': weekly_macd_up,
                            'volume': daily_data['volume'].iloc[-1] if 'volume' in daily_data.columns else 0,
                            'close': daily_data['close'].iloc[-1],
                            'change_pct': ((daily_data['close'].iloc[-1] - daily_data['close'].iloc[-2]) / daily_data['close'].iloc[-2] * 100) if len(daily_data) > 1 else 0
                        }
                        selected_stocks.append(stock_info)
                        
                except Exception as e:
                    logger.warning(f"处理股票 {stock_code} 时出错: {e}")
                    continue
            
            # 按成交量排序
            if selected_stocks:
                selected_df = pd.DataFrame(selected_stocks)
                selected_df = self.rank_by_volume(selected_df)
                results['selected_stocks'] = selected_df.to_dict('records')
            
            results['total_selected'] = len(results['selected_stocks'])
            results['filters_applied'].append(f"技术指标筛选后剩余: {results['total_selected']}只")
            
            logger.info(f"KDJ+MACD选股策略完成，共筛选出 {results['total_selected']} 只股票")
            
            return results
            
        except Exception as e:
            logger.error(f"运行选股策略失败: {e}")
            return {
                'strategy_name': 'KDJ+MACD技术选股策略',
                'run_time': datetime.now().isoformat(),
                'error': str(e),
                'selected_stocks': [],
                'total_screened': 0,
                'total_selected': 0,
                'filters_applied': []
            }
    
    def get_strategy_summary(self) -> Dict[str, Any]:
        """
        获取策略摘要
        
        Returns:
            策略摘要字典
        """
        return {
            'name': 'KDJ+MACD技术选股策略',
            'description': '基于KDJ和MACD双重技术指标向上，结合基本面筛选的选股策略',
            'type': 'technical_screening',
            'parameters': self.parameters,
            'filters': {
                'weekly_kdj_up': True,
                'daily_kdj_up': True,
                'weekly_macd_up': True,
                'daily_macd_up': True,
                'exclude_st': self.exclude_st,
                'exclude_tech_board': self.exclude_tech_board,
                'exclude_beijing': self.exclude_beijing,
                'volume_sort': self.volume_sort
            },
            'created_at': datetime.now().isoformat()
        }
