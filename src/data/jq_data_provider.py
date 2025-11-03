"""
聚宽数据提供者
封装聚宽SDK，提供统一的数据接口
"""

import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple
import warnings

# 忽略聚宽SDK的警告
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

class JQDataProvider:
    """聚宽数据提供者"""
    
    def __init__(self, username: str = None, password: str = None):
        """初始化聚宽数据提供者"""
        self.username = username
        self.password = password
        self.is_connected = False
        self.jq = None
        
        # 尝试导入聚宽SDK
        try:
            import jqdatasdk as jq
            self.jq = jq
            logger.info("聚宽SDK导入成功")
        except ImportError as e:
            logger.error(f"聚宽SDK导入失败: {e}")
            self.jq = None
    
    def connect(self) -> bool:
        """连接聚宽服务器"""
        if not self.jq:
            logger.error("聚宽SDK未安装")
            return False
        
        if not self.username or not self.password:
            logger.warning("聚宽用户名或密码未配置")
            return False
        
        try:
            # 连接聚宽
            self.jq.auth(self.username, self.password)
            self.is_connected = True
            logger.info("聚宽连接成功")
            return True
        except Exception as e:
            logger.error(f"聚宽连接失败: {e}")
            self.is_connected = False
            return False
    
    def disconnect(self):
        """断开聚宽连接"""
        if self.jq and self.is_connected:
            try:
                self.jq.logout()
                self.is_connected = False
                logger.info("聚宽连接已断开")
            except Exception as e:
                logger.error(f"断开聚宽连接失败: {e}")
    
    def get_stock_list(self, market: str = "CN") -> List[Dict]:
        """获取股票列表"""
        if not self.is_connected or not self.jq:
            logger.warning("聚宽未连接")
            return []
        
        try:
            # 根据市场获取股票列表
            if market == "CN":
                stocks = self.jq.get_all_securities(['stock'])
            elif market == "HK":
                stocks = self.jq.get_all_securities(['stock'], market='hk')
            elif market == "US":
                stocks = self.jq.get_all_securities(['stock'], market='us')
            else:
                stocks = self.jq.get_all_securities(['stock'])
            
            # 转换为字典列表
            stock_list = []
            for code, info in stocks.iterrows():
                stock_list.append({
                    'code': code,
                    'name': info['display_name'],
                    'market': market,
                    'start_date': info['start_date'].strftime('%Y-%m-%d') if pd.notna(info['start_date']) else None,
                    'end_date': info['end_date'].strftime('%Y-%m-%d') if pd.notna(info['end_date']) else None
                })
            
            logger.info(f"获取到 {len(stock_list)} 只股票")
            return stock_list
            
        except Exception as e:
            logger.error(f"获取股票列表失败: {e}")
            return []
    
    def get_price_data(self, codes: List[str], start_date: str, end_date: str, 
                      fields: List[str] = None) -> pd.DataFrame:
        """获取价格数据"""
        if not self.is_connected or not self.jq:
            logger.warning("聚宽未连接")
            return pd.DataFrame()
        
        if fields is None:
            fields = ['open', 'close', 'high', 'low', 'volume', 'money']
        
        try:
            # 获取价格数据
            data = self.jq.get_price(
                codes,
                start_date=start_date,
                end_date=end_date,
                frequency='daily',
                fields=fields,
                skip_paused=True,
                fq='pre'
            )
            
            logger.info(f"获取价格数据成功: {len(data)} 条记录")
            return data
            
        except Exception as e:
            logger.error(f"获取价格数据失败: {e}")
            return pd.DataFrame()
    
    def get_financial_data(self, codes: List[str], start_date: str, end_date: str,
                          fields: List[str] = None) -> pd.DataFrame:
        """获取财务数据"""
        if not self.is_connected or not self.jq:
            logger.warning("聚宽未连接")
            return pd.DataFrame()
        
        if fields is None:
            fields = ['total_revenue', 'net_profit', 'total_assets', 'total_liabilities']
        
        try:
            # 获取财务数据
            data = self.jq.get_fundamentals(
                self.jq.query(
                    self.jq.valuation.code,
                    self.jq.valuation.pe_ratio,
                    self.jq.valuation.pb_ratio,
                    self.jq.valuation.market_cap
                ).filter(
                    self.jq.valuation.code.in_(codes)
                ),
                date=end_date
            )
            
            logger.info(f"获取财务数据成功: {len(data)} 条记录")
            return data
            
        except Exception as e:
            logger.error(f"获取财务数据失败: {e}")
            return pd.DataFrame()
    
    def get_trading_calendar(self, start_date: str, end_date: str) -> List[str]:
        """获取交易日历"""
        if not self.is_connected or not self.jq:
            logger.warning("聚宽未连接")
            return []
        
        try:
            calendar = self.jq.get_trading_days(start_date=start_date, end_date=end_date)
            return [date.strftime('%Y-%m-%d') for date in calendar]
        except Exception as e:
            logger.error(f"获取交易日历失败: {e}")
            return []
    
    def get_index_data(self, index_code: str, start_date: str, end_date: str) -> pd.DataFrame:
        """获取指数数据"""
        if not self.is_connected or not self.jq:
            logger.warning("聚宽未连接")
            return pd.DataFrame()
        
        try:
            data = self.jq.get_price(
                index_code,
                start_date=start_date,
                end_date=end_date,
                frequency='daily',
                fields=['open', 'close', 'high', 'low', 'volume']
            )
            
            logger.info(f"获取指数数据成功: {len(data)} 条记录")
            return data
            
        except Exception as e:
            logger.error(f"获取指数数据失败: {e}")
            return pd.DataFrame()
    
    def get_realtime_data(self, codes: List[str]) -> Dict[str, Dict]:
        """获取实时数据"""
        if not self.is_connected or not self.jq:
            logger.warning("聚宽未连接")
            return {}
        
        try:
            # 获取实时数据
            data = self.jq.get_current_data(codes)
            
            result = {}
            for code in codes:
                if code in data:
                    current_data = data[code]
                    result[code] = {
                        'last_price': current_data.last_price,
                        'high_limit': current_data.high_limit,
                        'low_limit': current_data.low_limit,
                        'volume': current_data.volume,
                        'money': current_data.money,
                        'high': current_data.high,
                        'low': current_data.low,
                        'avg': current_data.avg,
                        'pre_close': current_data.pre_close,
                        'paused': current_data.paused
                    }
            
            logger.info(f"获取实时数据成功: {len(result)} 只股票")
            return result
            
        except Exception as e:
            logger.error(f"获取实时数据失败: {e}")
            return {}
    
    def get_connection_status(self) -> Dict[str, Any]:
        """获取连接状态"""
        return {
            'is_connected': self.is_connected,
            'username': self.username,
            'sdk_available': self.jq is not None,
            'status': 'connected' if self.is_connected else 'disconnected'
        }
    
    def __del__(self):
        """析构函数，自动断开连接"""
        self.disconnect()
