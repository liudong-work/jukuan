"""
聚宽模拟服务
当聚宽SDK不可用或未配置时，提供模拟数据
"""

import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple
import random

logger = logging.getLogger(__name__)

class MockJQDataProvider:
    """聚宽模拟数据提供者"""
    
    def __init__(self, username: str = None, password: str = None):
        """初始化模拟数据提供者"""
        self.username = username or "mock_user"
        self.password = password or "mock_pass"
        self.is_connected = False
        
        # 模拟股票数据
        self.mock_stocks = {
            "CN": [
                {"code": "000001.XSHE", "name": "平安银行", "market": "CN"},
                {"code": "000002.XSHE", "name": "万科A", "market": "CN"},
                {"code": "000858.XSHE", "name": "五粮液", "market": "CN"},
                {"code": "000876.XSHE", "name": "新希望", "market": "CN"},
                {"code": "002415.XSHE", "name": "海康威视", "market": "CN"},
                {"code": "002594.XSHE", "name": "比亚迪", "market": "CN"},
                {"code": "300059.XSHE", "name": "东方财富", "market": "CN"},
                {"code": "300750.XSHE", "name": "宁德时代", "market": "CN"},
                {"code": "600036.XSHG", "name": "招商银行", "market": "CN"},
                {"code": "600519.XSHG", "name": "贵州茅台", "market": "CN"},
                {"code": "600887.XSHG", "name": "伊利股份", "market": "CN"},
                {"code": "601318.XSHG", "name": "中国平安", "market": "CN"},
                {"code": "601398.XSHG", "name": "工商银行", "market": "CN"},
                {"code": "601939.XSHG", "name": "建设银行", "market": "CN"},
                {"code": "603259.XSHG", "name": "药明康德", "market": "CN"}
            ],
            "HK": [
                {"code": "00700.HK", "name": "腾讯控股", "market": "HK"},
                {"code": "00941.HK", "name": "中国移动", "market": "HK"},
                {"code": "01299.HK", "name": "友邦保险", "market": "HK"},
                {"code": "02318.HK", "name": "中国平安", "market": "HK"},
                {"code": "03988.HK", "name": "中国银行", "market": "HK"}
            ],
            "US": [
                {"code": "AAPL", "name": "苹果", "market": "US"},
                {"code": "MSFT", "name": "微软", "market": "US"},
                {"code": "GOOGL", "name": "谷歌", "market": "US"},
                {"code": "AMZN", "name": "亚马逊", "market": "US"},
                {"code": "TSLA", "name": "特斯拉", "market": "US"}
            ]
        }
    
    def connect(self) -> bool:
        """模拟连接"""
        self.is_connected = True
        logger.info("聚宽模拟服务连接成功")
        return True
    
    def disconnect(self):
        """模拟断开连接"""
        self.is_connected = False
        logger.info("聚宽模拟服务连接已断开")
    
    def get_stock_list(self, market: str = "CN") -> List[Dict]:
        """获取模拟股票列表"""
        if not self.is_connected:
            logger.warning("聚宽模拟服务未连接")
            return []
        
        stocks = self.mock_stocks.get(market, [])
        logger.info(f"获取模拟股票列表: {len(stocks)} 只股票")
        return stocks
    
    def get_daily_data(self, code: str, start_date: str, end_date: str, fields: List[str] = None) -> pd.DataFrame:
        """获取模拟日线数据"""
        if not self.is_connected:
            logger.warning("聚宽模拟服务未连接")
            return pd.DataFrame()
        
        try:
            # 生成日期范围
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            dates = pd.date_range(start=start_dt, end=end_dt, freq='D')
            
            # 过滤掉周末
            trading_dates = [date for date in dates if date.weekday() < 5]
            
            if not trading_dates:
                return pd.DataFrame()
            
            # 生成模拟数据
            data_list = []
            base_price = random.uniform(10, 100)  # 基础价格
            
            for date in trading_dates:
                # 模拟价格波动
                price_change = random.uniform(-0.05, 0.05)  # ±5%波动
                close_price = base_price * (1 + price_change)
                open_price = close_price * random.uniform(0.98, 1.02)
                high_price = max(open_price, close_price) * random.uniform(1.0, 1.03)
                low_price = min(open_price, close_price) * random.uniform(0.97, 1.0)
                volume = random.randint(1000000, 10000000)
                money = volume * close_price
                
                data_list.append({
                    'date': date,
                    'open': round(open_price, 2),
                    'close': round(close_price, 2),
                    'high': round(high_price, 2),
                    'low': round(low_price, 2),
                    'volume': volume,
                    'money': round(money, 2)
                })
                
                base_price = close_price  # 更新基础价格
            
            df = pd.DataFrame(data_list)
            df.set_index('date', inplace=True)
            
            logger.info(f"生成模拟日线数据: {code}, {len(df)} 条记录")
            return df
            
        except Exception as e:
            logger.error(f"生成模拟日线数据失败: {e}")
            return pd.DataFrame()
    
    def get_price_data(self, codes: List[str], start_date: str, end_date: str, 
                      fields: List[str] = None) -> pd.DataFrame:
        """生成模拟价格数据"""
        if not self.is_connected:
            logger.warning("聚宽模拟服务未连接")
            return pd.DataFrame()
        
        if fields is None:
            fields = ['open', 'close', 'high', 'low', 'volume', 'money']
        
        try:
            # 生成日期范围
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            dates = pd.date_range(start=start_dt, end=end_dt, freq='D')
            
            # 生成模拟数据
            data_list = []
            for code in codes:
                base_price = random.uniform(10, 100)  # 基础价格
                for date in dates:
                    # 模拟价格波动
                    price_change = random.uniform(-0.05, 0.05)  # ±5%波动
                    close_price = base_price * (1 + price_change)
                    open_price = close_price * random.uniform(0.98, 1.02)
                    high_price = max(open_price, close_price) * random.uniform(1.0, 1.03)
                    low_price = min(open_price, close_price) * random.uniform(0.97, 1.0)
                    volume = random.randint(1000000, 10000000)
                    money = volume * close_price
                    
                    data_list.append({
                        'code': code,
                        'date': date,
                        'open': round(open_price, 2),
                        'close': round(close_price, 2),
                        'high': round(high_price, 2),
                        'low': round(low_price, 2),
                        'volume': volume,
                        'money': round(money, 2)
                    })
                    
                    base_price = close_price  # 更新基础价格
            
            df = pd.DataFrame(data_list)
            df.set_index(['code', 'date'], inplace=True)
            
            logger.info(f"生成模拟价格数据: {len(df)} 条记录")
            return df
            
        except Exception as e:
            logger.error(f"生成模拟价格数据失败: {e}")
            return pd.DataFrame()
    
    def get_financial_data(self, codes: List[str], start_date: str, end_date: str,
                          fields: List[str] = None) -> pd.DataFrame:
        """生成模拟财务数据"""
        if not self.is_connected:
            logger.warning("聚宽模拟服务未连接")
            return pd.DataFrame()
        
        try:
            data_list = []
            for code in codes:
                data_list.append({
                    'code': code,
                    'pe_ratio': round(random.uniform(5, 50), 2),
                    'pb_ratio': round(random.uniform(0.5, 5), 2),
                    'market_cap': random.randint(1000000000, 1000000000000)
                })
            
            df = pd.DataFrame(data_list)
            logger.info(f"生成模拟财务数据: {len(df)} 条记录")
            return df
            
        except Exception as e:
            logger.error(f"生成模拟财务数据失败: {e}")
            return pd.DataFrame()
    
    def get_trading_calendar(self, start_date: str, end_date: str) -> List[str]:
        """生成模拟交易日历"""
        if not self.is_connected:
            logger.warning("聚宽模拟服务未连接")
            return []
        
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            dates = pd.date_range(start=start_dt, end=end_dt, freq='D')
            
            # 过滤掉周末
            trading_days = [date.strftime('%Y-%m-%d') for date in dates if date.weekday() < 5]
            
            logger.info(f"生成模拟交易日历: {len(trading_days)} 个交易日")
            return trading_days
            
        except Exception as e:
            logger.error(f"生成模拟交易日历失败: {e}")
            return []
    
    def get_index_data(self, index_code: str, start_date: str, end_date: str) -> pd.DataFrame:
        """生成模拟指数数据"""
        if not self.is_connected:
            logger.warning("聚宽模拟服务未连接")
            return pd.DataFrame()
        
        try:
            # 生成日期范围
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            dates = pd.date_range(start=start_dt, end=end_dt, freq='D')
            
            # 生成模拟指数数据
            data_list = []
            base_index = 3000  # 基础指数
            for date in dates:
                if date.weekday() < 5:  # 只包含工作日
                    price_change = random.uniform(-0.03, 0.03)  # ±3%波动
                    close_price = base_index * (1 + price_change)
                    open_price = close_price * random.uniform(0.99, 1.01)
                    high_price = max(open_price, close_price) * random.uniform(1.0, 1.02)
                    low_price = min(open_price, close_price) * random.uniform(0.98, 1.0)
                    volume = random.randint(100000000, 1000000000)
                    
                    data_list.append({
                        'date': date,
                        'open': round(open_price, 2),
                        'close': round(close_price, 2),
                        'high': round(high_price, 2),
                        'low': round(low_price, 2),
                        'volume': volume
                    })
                    
                    base_index = close_price  # 更新基础指数
            
            df = pd.DataFrame(data_list)
            df.set_index('date', inplace=True)
            
            logger.info(f"生成模拟指数数据: {len(df)} 条记录")
            return df
            
        except Exception as e:
            logger.error(f"生成模拟指数数据失败: {e}")
            return pd.DataFrame()
    
    def get_realtime_data(self, codes: List[str]) -> Dict[str, Dict]:
        """生成模拟实时数据"""
        if not self.is_connected:
            logger.warning("聚宽模拟服务未连接")
            return {}
        
        try:
            result = {}
            for code in codes:
                base_price = random.uniform(10, 100)
                result[code] = {
                    'last_price': round(base_price, 2),
                    'high_limit': round(base_price * 1.1, 2),
                    'low_limit': round(base_price * 0.9, 2),
                    'volume': random.randint(1000000, 10000000),
                    'money': round(random.randint(10000000, 100000000), 2),
                    'high': round(base_price * random.uniform(1.0, 1.05), 2),
                    'low': round(base_price * random.uniform(0.95, 1.0), 2),
                    'avg': round(base_price * random.uniform(0.98, 1.02), 2),
                    'pre_close': round(base_price * random.uniform(0.95, 1.05), 2),
                    'paused': False
                }
            
            logger.info(f"生成模拟实时数据: {len(result)} 只股票")
            return result
            
        except Exception as e:
            logger.error(f"生成模拟实时数据失败: {e}")
            return {}
    
    def get_connection_status(self) -> Dict[str, Any]:
        """获取连接状态"""
        return {
            'is_connected': self.is_connected,
            'username': self.username,
            'sdk_available': True,
            'status': 'connected' if self.is_connected else 'disconnected',
            'mode': 'mock'
        }
    
    def __del__(self):
        """析构函数"""
        self.disconnect()