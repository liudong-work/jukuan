"""
实时行情服务
提供WebSocket实时数据推送、行情数据管理等功能
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Set
from datetime import datetime, timedelta
import json
import os
from dataclasses import dataclass, asdict
import websockets
from websockets.server import WebSocketServerProtocol

# 导入相关服务
try:
    from .jq_service import jq_service
    from .enhanced_trading_service import enhanced_trading_service
except ImportError:
    jq_service = None
    enhanced_trading_service = None

logger = logging.getLogger(__name__)

@dataclass
class RealTimeQuote:
    """实时行情数据结构"""
    stock_code: str
    stock_name: str
    current_price: float
    change: float
    change_pct: float
    volume: int
    amount: float
    high: float
    low: float
    open: float
    prev_close: float
    bid_price: float
    ask_price: float
    bid_volume: int
    ask_volume: int
    timestamp: datetime

@dataclass
class MarketIndex:
    """市场指数数据结构"""
    index_code: str
    index_name: str
    current_value: float
    change: float
    change_pct: float
    volume: int
    amount: float
    timestamp: datetime

class MarketDataService:
    """实时行情服务类"""
    
    def __init__(self):
        self.websocket_connections: Set[WebSocketServerProtocol] = set()
        self.subscribed_stocks: Dict[str, Set[WebSocketServerProtocol]] = {}
        self.market_data_cache = {}
        self.index_data_cache = {}
        self.update_interval = 5  # 5秒更新一次
        
        # 启动数据更新任务
        asyncio.create_task(self._start_market_data_update())
        logger.info("实时行情服务已启动")
    
    async def _start_market_data_update(self):
        """启动市场数据更新"""
        while True:
            try:
                await self._update_market_data()
                await asyncio.sleep(self.update_interval)
            except Exception as e:
                logger.error(f"更新市场数据失败: {e}")
                await asyncio.sleep(10)
    
    async def _update_market_data(self):
        """更新市场数据"""
        try:
            if not jq_service:
                return
            
            # 获取所有订阅的股票
            all_subscribed_stocks = set()
            for stock_code in self.subscribed_stocks.keys():
                all_subscribed_stocks.add(stock_code)
            
            # 批量更新行情数据
            for stock_code in all_subscribed_stocks:
                try:
                    quote = await self._get_real_time_quote(stock_code)
                    if quote:
                        self.market_data_cache[stock_code] = quote
                        # 推送给订阅者
                        await self._broadcast_quote(quote)
                except Exception as e:
                    logger.error(f"更新股票{stock_code}行情失败: {e}")
            
            # 更新主要指数
            await self._update_market_indices()
            
        except Exception as e:
            logger.error(f"更新市场数据失败: {e}")
    
    async def _get_real_time_quote(self, stock_code: str) -> Optional[RealTimeQuote]:
        """获取实时行情"""
        try:
            if not jq_service:
                return None
            
            # 获取实时价格
            price_data = await jq_service._get_current_price(stock_code)
            if not price_data:
                return None
            
            # 获取日线数据
            end_date = datetime.now().strftime('%Y-%m-%d')
            daily_data = await jq_service.get_daily_data(stock_code, end_date, end_date)
            
            if daily_data and len(daily_data) > 0:
                today = daily_data[0]
                prev_close = today.get('close', 0)
                current_price = price_data.get('price', prev_close)
                change = current_price - prev_close
                change_pct = (change / prev_close * 100) if prev_close > 0 else 0
                
                # 获取股票名称
                stock_name = await self._get_stock_name(stock_code)
                
                quote = RealTimeQuote(
                    stock_code=stock_code,
                    stock_name=stock_name,
                    current_price=current_price,
                    change=change,
                    change_pct=change_pct,
                    volume=today.get('volume', 0),
                    amount=today.get('amount', 0),
                    high=today.get('high', 0),
                    low=today.get('low', 0),
                    open=today.get('open', 0),
                    prev_close=prev_close,
                    bid_price=current_price * 0.999,  # 模拟买一价
                    ask_price=current_price * 1.001,  # 模拟卖一价
                    bid_volume=1000,  # 模拟买一量
                    ask_volume=1000,  # 模拟卖一量
                    timestamp=datetime.now()
                )
                
                return quote
            
            return None
            
        except Exception as e:
            logger.error(f"获取股票{stock_code}实时行情失败: {e}")
            return None
    
    async def _get_stock_name(self, stock_code: str) -> str:
        """获取股票名称"""
        try:
            if jq_service:
                stock_info = await jq_service.get_stock_info(stock_code)
                if stock_info:
                    return stock_info.get("name", stock_code)
            return stock_code
        except Exception as e:
            logger.error(f"获取股票名称失败: {e}")
            return stock_code
    
    async def _update_market_indices(self):
        """更新市场指数"""
        try:
            # 主要指数列表
            indices = [
                {"code": "000001.XSHG", "name": "上证指数"},
                {"code": "399001.XSHE", "name": "深证成指"},
                {"code": "399006.XSHE", "name": "创业板指"},
                {"code": "000300.XSHG", "name": "沪深300"},
                {"code": "000905.XSHG", "name": "中证500"}
            ]
            
            for index_info in indices:
                try:
                    index_data = await self._get_index_data(index_info["code"], index_info["name"])
                    if index_data:
                        self.index_data_cache[index_info["code"]] = index_data
                        # 推送给所有连接
                        await self._broadcast_index(index_data)
                except Exception as e:
                    logger.error(f"更新指数{index_info['code']}失败: {e}")
                    
        except Exception as e:
            logger.error(f"更新市场指数失败: {e}")
    
    async def _get_index_data(self, index_code: str, index_name: str) -> Optional[MarketIndex]:
        """获取指数数据"""
        try:
            if not jq_service:
                return None
            
            # 获取指数数据
            end_date = datetime.now().strftime('%Y-%m-%d')
            daily_data = await jq_service.get_daily_data(index_code, end_date, end_date)
            
            if daily_data and len(daily_data) > 0:
                today = daily_data[0]
                prev_close = today.get('close', 0)
                current_value = today.get('close', prev_close)
                change = current_value - prev_close
                change_pct = (change / prev_close * 100) if prev_close > 0 else 0
                
                index_data = MarketIndex(
                    index_code=index_code,
                    index_name=index_name,
                    current_value=current_value,
                    change=change,
                    change_pct=change_pct,
                    volume=today.get('volume', 0),
                    amount=today.get('amount', 0),
                    timestamp=datetime.now()
                )
                
                return index_data
            
            return None
            
        except Exception as e:
            logger.error(f"获取指数{index_code}数据失败: {e}")
            return None
    
    async def _broadcast_quote(self, quote: RealTimeQuote):
        """广播行情数据"""
        try:
            if quote.stock_code not in self.subscribed_stocks:
                return
            
            subscribers = self.subscribed_stocks[quote.stock_code]
            if not subscribers:
                return
            
            message = {
                "type": "quote",
                "data": asdict(quote)
            }
            
            # 推送给所有订阅者
            disconnected = set()
            for websocket in subscribers:
                try:
                    await websocket.send(json.dumps(message, default=str))
                except websockets.exceptions.ConnectionClosed:
                    disconnected.add(websocket)
                except Exception as e:
                    logger.error(f"推送行情数据失败: {e}")
                    disconnected.add(websocket)
            
            # 清理断开的连接
            for websocket in disconnected:
                await self._remove_websocket_connection(websocket)
                
        except Exception as e:
            logger.error(f"广播行情数据失败: {e}")
    
    async def _broadcast_index(self, index_data: MarketIndex):
        """广播指数数据"""
        try:
            message = {
                "type": "index",
                "data": asdict(index_data)
            }
            
            # 推送给所有连接
            disconnected = set()
            for websocket in self.websocket_connections:
                try:
                    await websocket.send(json.dumps(message, default=str))
                except websockets.exceptions.ConnectionClosed:
                    disconnected.add(websocket)
                except Exception as e:
                    logger.error(f"推送指数数据失败: {e}")
                    disconnected.add(websocket)
            
            # 清理断开的连接
            for websocket in disconnected:
                await self._remove_websocket_connection(websocket)
                
        except Exception as e:
            logger.error(f"广播指数数据失败: {e}")
    
    async def add_websocket_connection(self, websocket: WebSocketServerProtocol):
        """添加WebSocket连接"""
        try:
            self.websocket_connections.add(websocket)
            logger.info(f"WebSocket连接已添加，当前连接数: {len(self.websocket_connections)}")
        except Exception as e:
            logger.error(f"添加WebSocket连接失败: {e}")
    
    async def remove_websocket_connection(self, websocket: WebSocketServerProtocol):
        """移除WebSocket连接"""
        try:
            await self._remove_websocket_connection(websocket)
        except Exception as e:
            logger.error(f"移除WebSocket连接失败: {e}")
    
    async def _remove_websocket_connection(self, websocket: WebSocketServerProtocol):
        """内部移除WebSocket连接"""
        try:
            # 从全局连接集合中移除
            self.websocket_connections.discard(websocket)
            
            # 从所有订阅中移除
            for stock_code, subscribers in self.subscribed_stocks.items():
                subscribers.discard(websocket)
            
            logger.info(f"WebSocket连接已移除，当前连接数: {len(self.websocket_connections)}")
            
        except Exception as e:
            logger.error(f"移除WebSocket连接失败: {e}")
    
    async def subscribe_stock(self, websocket: WebSocketServerProtocol, stock_code: str):
        """订阅股票行情"""
        try:
            if stock_code not in self.subscribed_stocks:
                self.subscribed_stocks[stock_code] = set()
            
            self.subscribed_stocks[stock_code].add(websocket)
            logger.info(f"订阅股票{stock_code}，当前订阅数: {len(self.subscribed_stocks[stock_code])}")
            
            # 发送当前行情数据
            if stock_code in self.market_data_cache:
                quote = self.market_data_cache[stock_code]
                message = {
                    "type": "quote",
                    "data": asdict(quote)
                }
                await websocket.send(json.dumps(message, default=str))
            
        except Exception as e:
            logger.error(f"订阅股票{stock_code}失败: {e}")
    
    async def unsubscribe_stock(self, websocket: WebSocketServerProtocol, stock_code: str):
        """取消订阅股票行情"""
        try:
            if stock_code in self.subscribed_stocks:
                self.subscribed_stocks[stock_code].discard(websocket)
                logger.info(f"取消订阅股票{stock_code}，当前订阅数: {len(self.subscribed_stocks[stock_code])}")
                
                # 如果没有订阅者，清理该股票的缓存
                if not self.subscribed_stocks[stock_code]:
                    del self.subscribed_stocks[stock_code]
                    if stock_code in self.market_data_cache:
                        del self.market_data_cache[stock_code]
            
        except Exception as e:
            logger.error(f"取消订阅股票{stock_code}失败: {e}")
    
    async def get_market_overview(self) -> Dict[str, Any]:
        """获取市场概览"""
        try:
            overview = {
                "timestamp": datetime.now().isoformat(),
                "indices": {},
                "market_status": "open" if self._is_market_open() else "closed",
                "total_stocks": len(self.market_data_cache),
                "active_subscriptions": len(self.subscribed_stocks)
            }
            
            # 添加指数数据
            for index_code, index_data in self.index_data_cache.items():
                overview["indices"][index_code] = asdict(index_data)
            
            return overview
            
        except Exception as e:
            logger.error(f"获取市场概览失败: {e}")
            return {"error": f"获取市场概览失败: {e}"}
    
    def _is_market_open(self) -> bool:
        """判断市场是否开放"""
        now = datetime.now()
        # 简单判断：9:30-11:30, 13:00-15:00
        if now.weekday() >= 5:  # 周末
            return False
        
        current_time = now.time()
        morning_start = datetime.strptime("09:30:00", "%H:%M:%S").time()
        morning_end = datetime.strptime("11:30:00", "%H:%M:%S").time()
        afternoon_start = datetime.strptime("13:00:00", "%H:%M:%S").time()
        afternoon_end = datetime.strptime("15:00:00", "%H:%M:%S").time()
        
        return (morning_start <= current_time <= morning_end or 
                afternoon_start <= current_time <= afternoon_end)
    
    async def get_stock_quote(self, stock_code: str) -> Optional[RealTimeQuote]:
        """获取股票行情"""
        try:
            if stock_code in self.market_data_cache:
                return self.market_data_cache[stock_code]
            
            # 如果缓存中没有，实时获取
            quote = await self._get_real_time_quote(stock_code)
            if quote:
                self.market_data_cache[stock_code] = quote
            
            return quote
            
        except Exception as e:
            logger.error(f"获取股票{stock_code}行情失败: {e}")
            return None
    
    async def get_multiple_quotes(self, stock_codes: List[str]) -> Dict[str, RealTimeQuote]:
        """批量获取股票行情"""
        try:
            quotes = {}
            for stock_code in stock_codes:
                quote = await self.get_stock_quote(stock_code)
                if quote:
                    quotes[stock_code] = quote
            
            return quotes
            
        except Exception as e:
            logger.error(f"批量获取股票行情失败: {e}")
            return {}
    
    async def search_stocks(self, keyword: str) -> List[Dict[str, Any]]:
        """搜索股票"""
        try:
            if not jq_service:
                return []
            
            # 从聚宽搜索股票
            search_results = await jq_service.search_stocks(keyword)
            return search_results or []
            
        except Exception as e:
            logger.error(f"搜索股票失败: {e}")
            return []
    
    async def get_sector_performance(self) -> List[Dict[str, Any]]:
        """获取行业表现"""
        try:
            if not jq_service:
                return []
            
            # 从聚宽获取行业表现
            sector_data = await jq_service.get_sector_performance()
            return sector_data or []
            
        except Exception as e:
            logger.error(f"获取行业表现失败: {e}")
            return []

# 创建全局市场数据服务实例
market_data_service = MarketDataService()
