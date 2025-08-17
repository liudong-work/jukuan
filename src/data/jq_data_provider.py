"""
聚宽数据提供者
提供股票、期货等金融数据的获取功能
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from typing import List, Dict, Optional, Union
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 聚宽SDK导入
try:
    from jqdatasdk import *
    JQ_AVAILABLE = True
except ImportError:
    JQ_AVAILABLE = False
    logging.warning("聚宽SDK未安装，请运行: pip install jqdatasdk")

class JQDataProvider:
    """聚宽数据提供者类"""
    
    def __init__(self, username: str = None, password: str = None):
        """
        初始化聚宽数据提供者
        
        Args:
            username: 聚宽用户名
            password: 聚宽密码
        """
        if not JQ_AVAILABLE:
            raise ImportError("聚宽SDK未安装，无法使用数据提供者")
            
        self.username = username or os.getenv('JQ_USERNAME')
        self.password = password or os.getenv('JQ_PASSWORD')
        self.is_connected = False
        
        if self.username and self.password:
            self.connect()
    
    def connect(self) -> bool:
        """
        连接聚宽服务器
        
        Returns:
            bool: 连接是否成功
        """
        try:
            if self.username and self.password:
                auth(self.username, self.password)
                self.is_connected = True
                logging.info("聚宽服务器连接成功")
                return True
            else:
                logging.error("聚宽用户名或密码未配置")
                return False
        except Exception as e:
            logging.error(f"连接聚宽服务器失败: {e}")
            return False
    
    def get_stock_list(self, market: str = 'CN') -> List[str]:
        """
        获取股票列表
        
        Args:
            market: 市场类型 ('CN'=A股, 'HK'=港股, 'US'=美股)
            
        Returns:
            List[str]: 股票代码列表
        """
        if not self.is_connected:
            self.connect()
        
        try:
            if market == 'CN':
                stocks = get_all_securities(['stock'])
                return list(stocks.index)
            elif market == 'HK':
                stocks = get_all_securities(['hk_stock'])
                return list(stocks.index)
            elif market == 'US':
                stocks = get_all_securities(['us_stock'])
                return list(stocks.index)
            else:
                logging.error(f"不支持的市场类型: {market}")
                return []
        except Exception as e:
            logging.error(f"获取股票列表失败: {e}")
            return []
    
    def get_daily_data(self, 
                       security: str, 
                       start_date: str, 
                       end_date: str,
                       fields: List[str] = None) -> pd.DataFrame:
        """
        获取日线数据
        
        Args:
            security: 证券代码
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            fields: 字段列表，默认获取OHLCV
            
        Returns:
            pd.DataFrame: 日线数据
        """
        if not self.is_connected:
            self.connect()
        
        if fields is None:
            fields = ['open', 'high', 'low', 'close', 'volume']
        
        try:
            df = get_price(security, 
                          start_date=start_date, 
                          end_date=end_date,
                          frequency='daily',
                          fields=fields)
            return df
        except Exception as e:
            logging.error(f"获取日线数据失败: {e}")
            return pd.DataFrame()
    
    def get_minute_data(self, 
                        security: str, 
                        start_date: str, 
                        end_date: str,
                        frequency: str = '1m',
                        fields: List[str] = None) -> pd.DataFrame:
        """
        获取分钟级数据
        
        Args:
            security: 证券代码
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            frequency: 频率 ('1m', '5m', '15m', '30m', '60m')
            fields: 字段列表
            
        Returns:
            pd.DataFrame: 分钟级数据
        """
        if not self.is_connected:
            self.connect()
        
        if fields is None:
            fields = ['open', 'high', 'low', 'close', 'volume']
        
        try:
            df = get_price(security, 
                          start_date=start_date, 
                          end_date=end_date,
                          frequency=frequency,
                          fields=fields)
            return df
        except Exception as e:
            logging.error(f"获取分钟级数据失败: {e}")
            return pd.DataFrame()
    
    def get_financial_data(self, 
                           security: str, 
                           statement: str,
                           start_date: str = None,
                           end_date: str = None) -> pd.DataFrame:
        """
        获取财务数据
        
        Args:
            security: 证券代码
            statement: 报表类型 ('income', 'balance', 'cash_flow')
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            pd.DataFrame: 财务数据
        """
        if not self.is_connected:
            self.connect()
        
        try:
            if statement == 'income':
                df = get_fundamentals(query(income).filter(income.code == security))
            elif statement == 'balance':
                df = get_fundamentals(query(balance).filter(balance.code == security))
            elif statement == 'cash_flow':
                df = get_fundamentals(query(cash_flow).filter(cash_flow.code == security))
            else:
                logging.error(f"不支持的报表类型: {statement}")
                return pd.DataFrame()
            
            return df
        except Exception as e:
            logging.error(f"获取财务数据失败: {e}")
            return pd.DataFrame()
    
    def get_index_stocks(self, index_code: str) -> List[str]:
        """
        获取指数成分股
        
        Args:
            index_code: 指数代码
            
        Returns:
            List[str]: 成分股代码列表
        """
        if not self.is_connected:
            self.connect()
        
        try:
            stocks = get_index_stocks(index_code)
            return stocks
        except Exception as e:
            logging.error(f"获取指数成分股失败: {e}")
            return []
    
    def get_industry_stocks(self, industry: str) -> List[str]:
        """
        获取行业股票
        
        Args:
            industry: 行业名称
            
        Returns:
            List[str]: 股票代码列表
        """
        if not self.is_connected:
            self.connect()
        
        try:
            stocks = get_industry_stocks(industry)
            return stocks
        except Exception as e:
            logging.error(f"获取行业股票失败: {e}")
            return []
    
    def get_realtime_price(self, securities: List[str]) -> Dict[str, float]:
        """
        获取实时价格
        
        Args:
            securities: 证券代码列表
            
        Returns:
            Dict[str, float]: 证券代码到价格的映射
        """
        if not self.is_connected:
            self.connect()
        
        try:
            prices = get_current_tick(securities)
            result = {}
            for security in securities:
                if security in prices:
                    result[security] = prices[security]['last_price']
                else:
                    result[security] = 0.0
            return result
        except Exception as e:
            logging.error(f"获取实时价格失败: {e}")
            return {sec: 0.0 for sec in securities}
    
    def disconnect(self):
        """断开聚宽连接"""
        try:
            logout()
            self.is_connected = False
            logging.info("已断开聚宽连接")
        except Exception as e:
            logging.error(f"断开连接失败: {e}")
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def get_sector_performance(self, date: str = None) -> pd.DataFrame:
        """
        获取板块涨幅数据
        
        Args:
            date: 日期，默认为最新交易日
            
        Returns:
            pd.DataFrame: 板块涨幅数据，包含板块名称、涨跌幅、成交额等
        """
        if not self.is_connected:
            self.connect()
        
        try:
            if date is None:
                # 获取最新交易日
                date = get_trade_days(end_date=datetime.now(), count=1)[0].strftime('%Y-%m-%d')
            
            # 获取申万一级行业指数
            sw_indices = ['801010', '801020', '801030', '801040', '801050', '801060', 
                         '801070', '801080', '801090', '801100', '801110', '801120', 
                         '801130', '801140', '801150', '801160', '801170', '801180', 
                         '801190', '801200', '801210', '801220', '801230', '801240', 
                         '801250', '801260', '801270', '801280', '801290', '801300']
            
            sector_data = []
            for index_code in sw_indices:
                try:
                    # 获取指数数据
                    index_data = get_price(index_code, start_date=date, end_date=date, 
                                         frequency='daily', fields=['close', 'open', 'high', 'low', 'volume'])
                    
                    if not index_data.empty:
                        close_price = index_data['close'].iloc[0]
                        open_price = index_data['open'].iloc[0]
                        change_pct = ((close_price - open_price) / open_price) * 100
                        
                        # 获取指数名称
                        index_name = get_security_info(index_code)['display_name']
                        
                        sector_data.append({
                            'code': index_code,
                            'name': index_name,
                            'open': open_price,
                            'close': close_price,
                            'change_pct': round(change_pct, 2),
                            'volume': index_data['volume'].iloc[0] if 'volume' in index_data else 0
                        })
                except Exception as e:
                    logging.warning(f"获取板块 {index_code} 数据失败: {e}")
                    continue
            
            # 按涨跌幅排序
            df = pd.DataFrame(sector_data)
            if not df.empty:
                df = df.sort_values('change_pct', ascending=False)
            
            return df
            
        except Exception as e:
            logging.error(f"获取板块涨幅数据失败: {e}")
            return pd.DataFrame()
    
    def get_concept_performance(self, date: str = None) -> pd.DataFrame:
        """
        获取概念板块涨幅数据
        
        Args:
            date: 日期，默认为最新交易日
            
        Returns:
            pd.DataFrame: 概念板块涨幅数据
        """
        if not self.is_connected:
            self.connect()
        
        try:
            if date is None:
                date = get_trade_days(end_date=datetime.now(), count=1)[0].strftime('%Y-%m-%d')
            
            # 获取概念板块列表
            concepts = get_concepts()
            
            concept_data = []
            for concept in concepts[:50]:  # 限制数量避免超时
                try:
                    concept_stocks = get_concept_stocks(concept)
                    if concept_stocks:
                        # 计算概念板块平均涨跌幅
                        stock_codes = [stock for stock in concept_stocks if stock.startswith('00') or stock.startswith('60')]
                        if stock_codes:
                            prices = get_price(stock_codes, start_date=date, end_date=date, 
                                             frequency='daily', fields=['close', 'open'])
                            
                            if not prices.empty:
                                changes = []
                                for stock in stock_codes:
                                    if stock in prices.index:
                                        stock_data = prices.loc[stock]
                                        if not stock_data.empty:
                                            open_price = stock_data['open'].iloc[0]
                                            close_price = stock_data['close'].iloc[0]
                                            if open_price > 0:
                                                change_pct = ((close_price - open_price) / open_price) * 100
                                                changes.append(change_pct)
                                
                                if changes:
                                    avg_change = sum(changes) / len(changes)
                                    concept_data.append({
                                        'name': concept,
                                        'change_pct': round(avg_change, 2),
                                        'stock_count': len(changes)
                                    })
                except Exception as e:
                    logging.warning(f"获取概念板块 {concept} 数据失败: {e}")
                    continue
            
            # 按涨跌幅排序
            df = pd.DataFrame(concept_data)
            if not df.empty:
                df = df.sort_values('change_pct', ascending=False)
            
            return df
            
        except Exception as e:
            logging.error(f"获取概念板块涨幅数据失败: {e}")
            return pd.DataFrame()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.disconnect()
