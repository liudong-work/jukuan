"""
聚宽服务模块
提供统一的聚宽数据接口和交易接口
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import pandas as pd
import json
import os
import numpy as np

from src.data.jq_data_provider import JQDataProvider
from core.config import settings

logger = logging.getLogger(__name__)

class SafeJSONEncoder(json.JSONEncoder):
    """安全的JSON编码器，处理numpy类型和特殊数值"""
    
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return self._safe_float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif pd.isna(obj):
            return None
        elif isinstance(obj, (datetime, pd.Timestamp)):
            return obj.isoformat()
        return super().default(obj)
    
    def _safe_float(self, value):
        """安全转换浮点数"""
        try:
            if pd.isna(value) or value == np.inf or value == -np.inf:
                return 0.0
            result = float(value)
            if np.isnan(result) or np.isinf(result):
                return 0.0
            return result
        except:
            return 0.0

class JQService:
    """聚宽服务类"""
    
    def __init__(self):
        """初始化聚宽服务"""
        self.data_provider = None
        self.is_connected = False
        self.connection_status = "disconnected"
        self.cache_dir = "cache/jq_data"
        self.cache_ttl = 3600  # 缓存1小时
        
        # 创建缓存目录
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # 初始化数据提供者
        self._init_data_provider()
    
    def _init_data_provider(self):
        """初始化数据提供者"""
        try:
            if settings.JQ_USERNAME and settings.JQ_PASSWORD:
                print(f"🔍 初始化聚宽服务: 用户名={settings.JQ_USERNAME}")
                self.data_provider = JQDataProvider(
                    username=settings.JQ_USERNAME,
                    password=settings.JQ_PASSWORD
                )
                self.is_connected = self.data_provider.is_connected
                self.connection_status = "connected" if self.is_connected else "failed"
                logger.info(f"聚宽数据提供者初始化: {self.connection_status}")
            else:
                logger.warning("聚宽用户名或密码未配置")
                self.connection_status = "not_configured"
        except Exception as e:
            logger.error(f"初始化聚宽数据提供者失败: {e}")
            self.connection_status = "error"
    
    def _get_available_date_range(self) -> tuple:
        """获取可用的日期范围"""
        # 根据账号权限，返回可用的日期范围
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)  # 默认1年数据
        
        # 如果当前日期超出权限范围，调整到权限范围内
        if end_date > datetime(2025, 5, 16):
            end_date = datetime(2025, 5, 16)
            start_date = datetime(2024, 5, 9)
        
        return start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')
    
    def _get_cache_key(self, key: str) -> str:
        """生成缓存键"""
        return os.path.join(self.cache_dir, f"{key}.json")
    
    def _is_cache_valid(self, cache_file: str) -> bool:
        """检查缓存是否有效"""
        if not os.path.exists(cache_file):
            return False
        
        # 检查文件修改时间
        mtime = os.path.getmtime(cache_file)
        if datetime.now().timestamp() - mtime > self.cache_ttl:
            return False
        
        return True
    
    def _save_to_cache(self, key: str, data: Any):
        """保存数据到缓存"""
        try:
            cache_file = self._get_cache_key(key)
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2, cls=SafeJSONEncoder)
        except Exception as e:
            logger.warning(f"保存缓存失败: {e}")
    
    def _load_from_cache(self, key: str) -> Optional[Any]:
        """从缓存加载数据"""
        try:
            cache_file = self._get_cache_key(key)
            if self._is_cache_valid(cache_file):
                with open(cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"加载缓存失败: {e}")
        return None
    
    async def connect(self) -> bool:
        """连接聚宽服务器"""
        try:
            if self.data_provider:
                success = self.data_provider.connect()
                self.is_connected = success
                self.connection_status = "connected" if success else "failed"
                logger.info(f"聚宽连接状态: {self.connection_status}")
                return success
            return False
        except Exception as e:
            logger.error(f"连接聚宽服务器失败: {e}")
            self.connection_status = "error"
            return False
    
    async def disconnect(self):
        """断开聚宽连接"""
        try:
            if self.data_provider:
                # 聚宽SDK没有显式的断开连接方法
                self.is_connected = False
                self.connection_status = "disconnected"
                logger.info("聚宽连接已断开")
        except Exception as e:
            logger.error(f"断开聚宽连接失败: {e}")
    
    async def get_connection_status(self) -> Dict[str, Any]:
        """获取连接状态"""
        return {
            "is_connected": self.is_connected,
            "status": self.connection_status,
            "username": settings.JQ_USERNAME if self.is_connected else None,
            "last_check": datetime.now().isoformat(),
            "available_date_range": self._get_available_date_range()
        }
    
    async def get_stock_list(self, market: str = 'CN') -> List[Dict]:
        """获取股票列表（增强版，包含价格和涨幅）"""
        try:
            if not self.is_connected:
                await self.connect()
            
            # 尝试从缓存加载
            cache_key = f"stock_list_{market}"
            cached_data = self._load_from_cache(cache_key)
            if cached_data:
                logger.info(f"从缓存加载{market}市场股票列表: {len(cached_data)}只")
                return cached_data
            
            if self.data_provider and self.is_connected:
                # 获取基础股票列表
                stocks = self.data_provider.get_stock_list(market)
                
                # 限制数量，避免API调用过多
                if len(stocks) > 50:  # 减少到50只，避免连接数超限
                    stocks = stocks[:50]
                    logger.info(f"限制股票数量为50只，避免连接数超限")
                
                # 获取股票详细信息（价格、涨幅等）
                stock_details = []
                
                # 批量获取数据，减少连接数
                try:
                    # 使用可用的日期范围
                    start_date, end_date = self._get_available_date_range()
                    
                    # 批量获取多只股票的数据
                    for i in range(0, len(stocks), 5):  # 每次处理5只股票
                        batch_stocks = stocks[i:i+5]
                        
                        for stock_code in batch_stocks:
                            try:
                                data = self.data_provider.get_daily_data(stock_code, start_date, end_date)
                                
                                if not data.empty:
                                    latest = data.iloc[-1]
                                    prev_close = data.iloc[-2]['close'] if len(data) > 1 else latest['open']
                                    
                                    stock_info = {
                                        'code': stock_code,
                                        'name': self._get_stock_name(stock_code),
                                        'current_price': self._safe_float(latest['close']),
                                        'open_price': self._safe_float(latest['open']),
                                        'high_price': self._safe_float(latest['high']),
                                        'low_price': self._safe_float(latest['low']),
                                        'prev_close': self._safe_float(prev_close),
                                        'change': self._safe_float(latest['close'] - prev_close),
                                        'change_pct': self._safe_float(((latest['close'] - prev_close) / prev_close) * 100 if prev_close > 0 else 0),
                                        'volume': self._safe_float(latest['volume']),
                                        'amount': self._safe_float(latest.get('amount', 0)),
                                        'market': self._get_market_type(stock_code),
                                        'industry': self._get_industry(stock_code),
                                        'update_time': datetime.now().isoformat(),
                                        'data_date': latest.name.strftime('%Y-%m-%d') if hasattr(latest.name, 'strftime') else str(latest.name)
                                    }
                                    stock_details.append(stock_info)
                                else:
                                    # 添加基础信息
                                    stock_details.append({
                                        'code': stock_code,
                                        'name': stock_code,
                                        'current_price': 0.0,
                                        'open_price': 0.0,
                                        'high_price': 0.0,
                                        'low_price': 0.0,
                                        'prev_close': 0.0,
                                        'change': 0.0,
                                        'change_pct': 0.0,
                                        'volume': 0,
                                        'amount': 0,
                                        'market': self._get_market_type(stock_code),
                                        'industry': '未知',
                                        'update_time': datetime.now().isoformat(),
                                        'data_date': '未知'
                                    })
                                    
                            except Exception as e:
                                logger.warning(f"获取{stock_code}详细信息失败: {e}")
                                # 添加基础信息
                                stock_details.append({
                                    'code': stock_code,
                                    'name': stock_code,
                                    'current_price': 0.0,
                                    'open_price': 0.0,
                                    'high_price': 0.0,
                                    'low_price': 0.0,
                                    'prev_close': 0.0,
                                    'change': 0.0,
                                    'change_pct': 0.0,
                                    'volume': 0,
                                    'amount': 0,
                                    'market': self._get_market_type(stock_code),
                                    'industry': '未知',
                                    'update_time': datetime.now().isoformat(),
                                    'data_date': '未知'
                                })
                        
                        # 批次间暂停，避免连接数超限
                        if i + 5 < len(stocks):
                            await asyncio.sleep(0.5)
                            
                except Exception as e:
                    logger.error(f"批量获取股票数据失败: {e}")
                    # 如果批量获取失败，返回基础股票列表
                    stock_details = [
                        {
                            'code': stock_code,
                            'name': stock_code,
                            'current_price': 0.0,
                            'open_price': 0.0,
                            'high_price': 0.0,
                            'low_price': 0.0,
                            'prev_close': 0.0,
                            'change': 0.0,
                            'change_pct': 0.0,
                            'volume': 0,
                            'amount': 0,
                            'market': self._get_market_type(stock_code),
                            'industry': '未知',
                            'update_time': datetime.now().isoformat(),
                            'data_date': '未知'
                        }
                        for stock_code in stocks[:20]  # 只返回前20只
                    ]
                
                # 按涨跌幅排序
                if stock_details:
                    stock_details.sort(key=lambda x: x['change_pct'], reverse=True)
                
                # 清理数据，确保JSON兼容性
                cleaned_stocks = []
                for stock in stock_details:
                    cleaned_stock = {}
                    for key, value in stock.items():
                        if isinstance(value, (np.integer, np.floating)):
                            cleaned_stock[key] = self._safe_float(value)
                        elif isinstance(value, (np.ndarray, pd.Series)):
                            cleaned_stock[key] = value.tolist() if hasattr(value, 'tolist') else str(value)
                        elif pd.isna(value):
                            cleaned_stock[key] = None
                        else:
                            cleaned_stock[key] = value
                    cleaned_stocks.append(cleaned_stock)
                
                # 保存到缓存
                self._save_to_cache(cache_key, cleaned_stocks)
                
                logger.info(f"获取{market}市场股票列表: {len(cleaned_stocks)}只")
                return cleaned_stocks
            else:
                logger.warning("聚宽未连接，无法获取股票列表")
                return []
        except Exception as e:
            logger.error(f"获取股票列表失败: {e}")
            return []
    
    async def get_daily_data(self, 
                            stock_code: str, 
                            start_date: str = None, 
                            end_date: str = None,
                            fields: Optional[List[str]] = None) -> pd.DataFrame:
        """获取日线数据"""
        try:
            if not self.is_connected:
                await self.connect()
            
            # 如果没有指定日期，使用可用范围
            if not start_date or not end_date:
                start_date, end_date = self._get_available_date_range()
                logger.info(f"使用默认日期范围: {start_date} 至 {end_date}")
            
            # 尝试从缓存加载
            cache_key = f"daily_data_{stock_code}_{start_date}_{end_date}"
            cached_data = self._load_from_cache(cache_key)
            if cached_data:
                logger.info(f"从缓存加载{stock_code}日线数据: {len(cached_data)}条")
                return pd.DataFrame(cached_data)
            
            if self.data_provider and self.is_connected:
                data = self.data_provider.get_daily_data(
                    stock_code, start_date, end_date, fields
                )
                
                if not data.empty:
                    # 保存到缓存
                    self._save_to_cache(cache_key, data.to_dict('records'))
                
                logger.info(f"获取{stock_code}日线数据: {len(data)}条")
                return data
            else:
                logger.warning("聚宽未连接，无法获取日线数据")
                return pd.DataFrame()
        except Exception as e:
            logger.error(f"获取日线数据失败 {stock_code}: {e}")
            return pd.DataFrame()
    
    async def get_realtime_quotes(self, stock_codes: List[str]) -> Dict[str, Dict]:
        """获取实时行情"""
        try:
            if not self.is_connected:
                await self.connect()
            
            if self.data_provider and self.is_connected:
                quotes = {}
                for stock_code in stock_codes:
                    try:
                        # 获取最新数据作为实时行情
                        end_date = datetime.now().strftime('%Y-%m-%d')
                        start_date = (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d')
                        
                        data = self.data_provider.get_daily_data(
                            stock_code, start_date, end_date
                        )
                        
                        if not data.empty:
                            latest = data.iloc[-1]
                            quotes[stock_code] = {
                                'code': stock_code,
                                'name': self._get_stock_name(stock_code),
                                'price': latest['close'],
                                'change': latest['close'] - latest['open'],
                                'change_pct': ((latest['close'] - latest['open']) / latest['open']) * 100,
                                'volume': latest['volume'],
                                'amount': latest.get('amount', 0),
                                'high': latest['high'],
                                'low': latest['low'],
                                'open': latest['open'],
                                'prev_close': data.iloc[-2]['close'] if len(data) > 1 else latest['open'],
                                'timestamp': datetime.now().isoformat()
                            }
                    except Exception as e:
                        logger.warning(f"获取{stock_code}实时行情失败: {e}")
                        continue
                
                logger.info(f"获取实时行情: {len(quotes)}只股票")
                return quotes
            else:
                logger.warning("聚宽未连接，无法获取实时行情")
                return {}
        except Exception as e:
            logger.error(f"获取实时行情失败: {e}")
            return {}
    
    async def get_stock_info(self, stock_codes: List[str]) -> Dict[str, Dict]:
        """获取股票基本信息"""
        try:
            if not self.is_connected:
                await self.connect()
            
            if self.data_provider and self.is_connected:
                stock_info = {}
                for stock_code in stock_codes:
                    try:
                        name = self._get_stock_name(stock_code)
                        stock_info[stock_code] = {
                            'code': stock_code,
                            'name': name,
                            'market': self._get_market_type(stock_code),
                            'industry': self._get_industry(stock_code),
                            'list_date': self._get_list_date(stock_code),
                            'current_price': await self._get_current_price(stock_code)
                        }
                    except Exception as e:
                        logger.warning(f"获取{stock_code}基本信息失败: {e}")
                        continue
                
                logger.info(f"获取股票信息: {len(stock_info)}只股票")
                return stock_info
            else:
                logger.warning("聚宽未连接，无法获取股票信息")
                return {}
        except Exception as e:
            logger.error(f"获取股票信息失败: {e}")
            return {}
    
    async def get_market_overview(self) -> Dict[str, Any]:
        """获取市场概览"""
        try:
            if not self.is_connected:
                await self.connect()
            
            # 获取主要指数
            indices = ['000001.XSHG', '399001.XSHE', '399006.XSHE']  # 上证、深证、创业板
            overview = {
                'timestamp': datetime.now().isoformat(),
                'indices': {},
                'market_stats': {},
                'top_gainers': [],
                'top_losers': []
            }
            
            # 获取指数数据
            for index_code in indices:
                try:
                    end_date = datetime.now().strftime('%Y-%m-%d')
                    start_date = (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d')
                    
                    data = self.data_provider.get_daily_data(index_code, start_date, end_date)
                    if not data.empty:
                        latest = data.iloc[-1]
                        overview['indices'][index_code] = {
                            'name': self._get_index_name(index_code),
                            'price': latest['close'],
                            'change': latest['close'] - latest['open'],
                            'change_pct': ((latest['close'] - latest['open']) / latest['open']) * 100
                        }
                except Exception as e:
                    logger.warning(f"获取指数{index_code}数据失败: {e}")
                    continue
            
            logger.info("获取市场概览成功")
            return overview
            
        except Exception as e:
            logger.error(f"获取市场概览失败: {e}")
            return {}
    
    async def get_sector_performance(self) -> Dict[str, Any]:
        """获取行业板块表现"""
        try:
            if not self.is_connected:
                await self.connect()
            
            # 这里应该调用聚宽的行业分类接口
            # 暂时返回模拟数据
            sectors = {
                'technology': {'name': '科技', 'change_pct': 2.5, 'volume': 1000000},
                'finance': {'name': '金融', 'change_pct': -0.8, 'volume': 800000},
                'consumer': {'name': '消费', 'change_pct': 1.2, 'volume': 600000},
                'healthcare': {'name': '医疗', 'change_pct': 3.1, 'volume': 400000}
            }
            
            return {
                'timestamp': datetime.now().isoformat(),
                'sectors': sectors
            }
            
        except Exception as e:
            logger.error(f"获取行业板块表现失败: {e}")
            return {}
    
    async def _get_current_price(self, stock_code: str) -> float:
        """获取当前价格"""
        try:
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            
            data = self.data_provider.get_daily_data(stock_code, start_date, end_date)
            if not data.empty:
                return data.iloc[-1]['close']
            return 0.0
        except Exception:
            return 0.0
    
    def _get_stock_name(self, stock_code: str) -> str:
        """获取股票名称"""
        try:
            if self.data_provider and self.is_connected:
                # 这里应该调用聚宽的股票名称接口
                # 暂时返回代码
                return stock_code
            return stock_code
        except Exception as e:
            logger.warning(f"获取股票名称失败 {stock_code}: {e}")
            return stock_code
    
    def _get_index_name(self, index_code: str) -> str:
        """获取指数名称"""
        index_names = {
            '000001.XSHG': '上证指数',
            '399001.XSHE': '深证成指',
            '399006.XSHE': '创业板指'
        }
        return index_names.get(index_code, index_code)
    
    def _get_market_type(self, stock_code: str) -> str:
        """获取市场类型"""
        if stock_code.startswith('000') or stock_code.startswith('002'):
            return '深市主板'
        elif stock_code.startswith('300'):
            return '创业板'
        elif stock_code.startswith('688'):
            return '科创板'
        elif stock_code.startswith('60'):
            return '沪市主板'
        else:
            return '其他'
    
    def _get_industry(self, stock_code: str) -> str:
        """获取行业分类"""
        # 这里应该调用聚宽的行业分类接口
        # 暂时返回默认值
        return '未知'
    
    def _get_list_date(self, stock_code: str) -> str:
        """获取上市日期"""
        # 这里应该调用聚宽的上市日期接口
        # 暂时返回默认值
        return '未知'
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        return {
            "service": "jq_service",
            "status": "healthy" if self.is_connected else "unhealthy",
            "connection_status": self.connection_status,
            "is_connected": self.is_connected,
            "last_check": datetime.now().isoformat(),
            "cache_info": {
                "cache_dir": self.cache_dir,
                "cache_ttl": self.cache_ttl
            }
        }

    def _safe_float(self, value: Any) -> float:
        """安全地将值转换为浮点数，处理无穷大和NaN"""
        try:
            if value is None or pd.isna(value):
                return 0.0
            
            # 处理numpy类型
            if hasattr(value, 'item'):
                value = value.item()
            
            # 转换为浮点数
            result = float(value)
            
            # 检查是否为无穷大或NaN
            if np.isnan(result) or np.isinf(result):
                return 0.0
                
            return result
        except (ValueError, TypeError, OverflowError):
            return 0.0

    def clear_cache(self, pattern: str = "*") -> Dict[str, Any]:
        """清理缓存文件
        
        Args:
            pattern: 缓存文件匹配模式，默认为"*"清理所有缓存
            
        Returns:
            清理结果信息
        """
        try:
            import glob
            cache_files = glob.glob(os.path.join(self.cache_dir, f"{pattern}.json"))
            
            cleared_count = 0
            cleared_files = []
            
            for cache_file in cache_files:
                try:
                    os.remove(cache_file)
                    cleared_count += 1
                    cleared_files.append(os.path.basename(cache_file))
                except Exception as e:
                    logger.warning(f"删除缓存文件失败 {cache_file}: {e}")
            
            result = {
                "success": True,
                "cleared_count": cleared_count,
                "cleared_files": cleared_files,
                "message": f"成功清理 {cleared_count} 个缓存文件"
            }
            
            logger.info(f"缓存清理完成: {result['message']}")
            return result
            
        except Exception as e:
            error_msg = f"清理缓存失败: {e}"
            logger.error(error_msg)
            return {
                "success": False,
                "cleared_count": 0,
                "cleared_files": [],
                "message": error_msg
            }

# 创建全局聚宽服务实例
jq_service = JQService()

def reinitialize_jq_service():
    """重新初始化聚宽服务实例"""
    global jq_service
    jq_service = JQService()
    return jq_service
