#!/usr/bin/env python3
"""
实时数据服务
实现聚宽数据实时化、多数据源融合和数据质量提升
"""

import asyncio
import logging
import json
import os
import time
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from dataclasses import dataclass, asdict
import redis
from concurrent.futures import ThreadPoolExecutor
import threading
from queue import Queue, Empty

# 导入现有服务
from services.jq_service import JQService
from core.config import settings

logger = logging.getLogger(__name__)

@dataclass
class MarketData:
    """市场数据结构"""
    code: str
    name: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    amount: float
    source: str
    quality_score: float = 1.0

@dataclass
class RealTimeQuote:
    """实时行情数据结构"""
    code: str
    name: str
    timestamp: datetime
    price: float
    volume: int
    amount: float
    bid_price: float
    ask_price: float
    bid_volume: int
    ask_volume: int
    source: str
    latency_ms: float = 0.0

@dataclass
class TickData:
    """逐笔成交数据结构"""
    code: str
    timestamp: datetime
    price: float
    volume: int
    amount: float
    direction: str  # 'buy' or 'sell'
    source: str
    sequence: int

class DataQualityMonitor:
    """数据质量监控器"""
    
    def __init__(self):
        self.quality_metrics = {}
        self.alert_thresholds = {
            'latency_ms': 1000,  # 延迟超过1秒告警
            'missing_rate': 0.05,  # 缺失率超过5%告警
            'error_rate': 0.01,    # 错误率超过1%告警
        }
    
    def calculate_quality_score(self, data: pd.DataFrame, source: str) -> float:
        """计算数据质量分数"""
        if data.empty:
            return 0.0
        
        scores = []
        
        # 完整性检查
        completeness = 1 - (data.isnull().sum().sum() / (len(data) * len(data.columns)))
        scores.append(completeness * 0.3)
        
        # 一致性检查
        consistency = self._check_data_consistency(data)
        scores.append(consistency * 0.3)
        
        # 时效性检查
        timeliness = self._check_data_timeliness(data)
        scores.append(timeliness * 0.4)
        
        quality_score = sum(scores)
        
        # 记录质量指标
        self.quality_metrics[source] = {
            'completeness': completeness,
            'consistency': consistency,
            'timeliness': timeliness,
            'overall_score': quality_score,
            'timestamp': datetime.now()
        }
        
        return quality_score
    
    def _check_data_consistency(self, data: pd.DataFrame) -> float:
        """检查数据一致性"""
        if data.empty:
            return 0.0
        
        # 检查价格合理性
        price_consistency = 1.0
        if 'close' in data.columns:
            # 检查价格是否为正数
            valid_prices = (data['close'] > 0).sum()
            price_consistency = valid_prices / len(data)
        
        # 检查成交量合理性
        volume_consistency = 1.0
        if 'volume' in data.columns:
            valid_volumes = (data['volume'] >= 0).sum()
            volume_consistency = valid_volumes / len(data)
        
        return (price_consistency + volume_consistency) / 2
    
    def _check_data_timeliness(self, data: pd.DataFrame) -> float:
        """检查数据时效性"""
        if data.empty or 'timestamp' not in data.columns:
            return 0.0
        
        try:
            # 检查最新数据的时间
            latest_time = pd.to_datetime(data['timestamp'].max())
            current_time = pd.Timestamp.now()
            time_diff = (current_time - latest_time).total_seconds()
            
            # 根据数据类型设置时效性标准
            if time_diff <= 60:  # 1分钟内
                return 1.0
            elif time_diff <= 300:  # 5分钟内
                return 0.8
            elif time_diff <= 3600:  # 1小时内
                return 0.6
            else:
                return 0.3
        except:
            return 0.5
    
    def get_quality_report(self) -> Dict[str, Any]:
        """获取数据质量报告"""
        scores = [m['overall_score'] for m in self.quality_metrics.values()]
        overall_quality = np.mean(scores) if scores else 0.0
        
        # 确保没有 NaN 值
        if np.isnan(overall_quality):
            overall_quality = 0.0
        
        return {
            'overall_quality': float(overall_quality),
            'source_quality': self.quality_metrics,
            'alerts': self._generate_alerts(),
            'timestamp': datetime.now().isoformat()
        }
    
    def _generate_alerts(self) -> List[Dict[str, Any]]:
        """生成告警信息"""
        alerts = []
        
        for source, metrics in self.quality_metrics.items():
            if metrics['overall_score'] < 0.8:
                alerts.append({
                    'source': source,
                    'level': 'warning',
                    'message': f'{source}数据质量较低: {metrics["overall_score"]:.2f}',
                    'timestamp': datetime.now().isoformat()
                })
        
        return alerts

class RealTimeDataService:
    """实时数据服务"""
    
    def __init__(self):
        """初始化实时数据服务"""
        self.jq_service = JQService()
        self.quality_monitor = DataQualityMonitor()
        
        # 数据源配置
        self.data_sources = {
            'jq': self.jq_service,
            # 后续可以添加其他数据源
            # 'tushare': TushareService(),
            # 'akshare': AKShareService(),
        }
        
        # 实时数据缓存
        self.realtime_cache = {}
        self.cache_lock = threading.Lock()
        
        # 订阅管理
        self.subscriptions = {}
        self.subscription_lock = threading.Lock()
        
        # 数据质量监控
        self.quality_thread = None
        self.stop_quality_monitor = False
        
        # 启动质量监控
        self._start_quality_monitor()
        
        logger.info("实时数据服务初始化完成")
    
    def _start_quality_monitor(self):
        """启动数据质量监控"""
        def quality_monitor_loop():
            while not self.stop_quality_monitor:
                try:
                    # 每5分钟检查一次数据质量
                    time.sleep(300)
                    self._check_data_quality()
                except Exception as e:
                    logger.error(f"数据质量监控异常: {e}")
        
        self.quality_thread = threading.Thread(target=quality_monitor_loop, daemon=True)
        self.quality_thread.start()
    
    def _check_data_quality(self):
        """检查数据质量"""
        try:
            # 检查各数据源的数据质量
            for source_name, source_service in self.data_sources.items():
                if hasattr(source_service, 'get_data_quality'):
                    quality_data = source_service.get_data_quality()
                    if quality_data is not None:
                        self.quality_monitor.calculate_quality_score(quality_data, source_name)
            
            # 生成质量报告
            quality_report = self.quality_monitor.get_quality_report()
            
            # 记录质量报告
            logger.info(f"数据质量报告: {quality_report}")
            
            # 如果有告警，记录告警信息
            if quality_report['alerts']:
                for alert in quality_report['alerts']:
                    logger.warning(f"数据质量告警: {alert}")
                    
        except Exception as e:
            logger.error(f"检查数据质量失败: {e}")
    
    async def get_realtime_quote(self, code: str, source: str = 'jq') -> Optional[RealTimeQuote]:
        """获取实时行情"""
        try:
            if source not in self.data_sources:
                raise ValueError(f"不支持的数据源: {source}")
            
            source_service = self.data_sources[source]
            
            # 检查缓存
            cache_key = f"{source}_{code}_quote"
            cached_data = self._get_cache(cache_key)
            
            if cached_data and self._is_cache_valid(cached_data, ttl=5):  # 5秒缓存
                return cached_data
            
            # 从数据源获取实时数据
            start_time = time.time()
            
            if source == 'jq':
                quote_data = await self._get_jq_realtime_quote(code)
            else:
                quote_data = None
            
            if quote_data:
                # 计算延迟
                latency_ms = (time.time() - start_time) * 1000
                quote_data.latency_ms = latency_ms
                
                # 缓存数据
                self._set_cache(cache_key, quote_data, ttl=5)
                
                return quote_data
            
        except Exception as e:
            logger.error(f"获取实时行情失败 {code} from {source}: {e}")
        
        return None
    
    async def _get_jq_realtime_quote(self, code: str) -> Optional[RealTimeQuote]:
        """从聚宽获取实时行情"""
        try:
            if not self.jq_service.is_connected:
                logger.warning("聚宽服务未连接")
                return None
            
            # 获取实时行情数据
            # 这里需要根据聚宽API的具体实现来获取数据
            # 目前返回模拟数据
            current_time = datetime.now()
            
            quote = RealTimeQuote(
                code=code,
                name=f"股票{code}",
                timestamp=current_time,
                price=100.0 + np.random.randn() * 2,  # 模拟价格
                volume=1000000 + int(np.random.randn() * 100000),
                amount=100000000 + np.random.randn() * 10000000,
                bid_price=99.5 + np.random.randn(),
                ask_price=100.5 + np.random.randn(),
                bid_volume=500000 + int(np.random.randn() * 50000),
                ask_volume=500000 + int(np.random.randn() * 50000),
                source='jq'
            )
            
            return quote
            
        except Exception as e:
            logger.error(f"从聚宽获取实时行情失败 {code}: {e}")
            return None
    
    async def get_tick_data(self, code: str, start_time: datetime, end_time: datetime, 
                           source: str = 'jq') -> List[TickData]:
        """获取逐笔成交数据"""
        try:
            if source not in self.data_sources:
                raise ValueError(f"不支持的数据源: {source}")
            
            source_service = self.data_sources[source]
            
            # 检查缓存
            cache_key = f"{source}_{code}_ticks_{start_time.date()}_{end_time.date()}"
            cached_data = self._get_cache(cache_key)
            
            if cached_data and self._is_cache_valid(cached_data, ttl=3600):  # 1小时缓存
                return cached_data
            
            # 从数据源获取数据
            if source == 'jq':
                tick_data = await self._get_jq_tick_data(code, start_time, end_time)
            else:
                tick_data = []
            
            if tick_data:
                # 缓存数据
                self._set_cache(cache_key, tick_data, ttl=3600)
                
                return tick_data
            
        except Exception as e:
            logger.error(f"获取逐笔成交数据失败 {code} from {source}: {e}")
        
        return []
    
    async def _get_jq_tick_data(self, code: str, start_time: datetime, end_time: datetime) -> List[TickData]:
        """从聚宽获取逐笔成交数据"""
        try:
            if not self.jq_service.is_connected:
                logger.warning("聚宽服务未连接")
                return []
            
            # 这里需要根据聚宽API的具体实现来获取数据
            # 目前返回模拟数据
            tick_data = []
            current_time = start_time
            
            while current_time <= end_time:
                tick = TickData(
                    code=code,
                    timestamp=current_time,
                    price=100.0 + np.random.randn() * 2,
                    volume=1000 + int(np.random.randn() * 100),
                    amount=100000 + np.random.randn() * 10000,
                    direction='buy' if np.random.random() > 0.5 else 'sell',
                    source='jq',
                    sequence=len(tick_data) + 1
                )
                tick_data.append(tick)
                current_time += timedelta(seconds=np.random.randint(1, 10))
            
            return tick_data
            
        except Exception as e:
            logger.error(f"从聚宽获取逐笔成交数据失败 {code}: {e}")
            return []
    
    async def subscribe_realtime_data(self, codes: List[str], callback: Callable, 
                                    source: str = 'jq') -> str:
        """订阅实时数据"""
        try:
            subscription_id = f"sub_{int(time.time() * 1000)}"
            
            with self.subscription_lock:
                self.subscriptions[subscription_id] = {
                    'codes': codes,
                    'callback': callback,
                    'source': source,
                    'active': True,
                    'created_at': datetime.now()
                }
            
            # 启动订阅任务
            asyncio.create_task(self._subscription_task(subscription_id))
            
            logger.info(f"订阅实时数据成功: {subscription_id}, 股票: {codes}")
            return subscription_id
            
        except Exception as e:
            logger.error(f"订阅实时数据失败: {e}")
            raise
    
    async def _subscription_task(self, subscription_id: str):
        """订阅任务"""
        try:
            while self.subscriptions.get(subscription_id, {}).get('active', False):
                subscription = self.subscriptions.get(subscription_id)
                if not subscription:
                    break
                
                # 获取订阅的股票数据
                for code in subscription['codes']:
                    try:
                        quote = await self.get_realtime_quote(code, subscription['source'])
                        if quote:
                            # 调用回调函数
                            await subscription['callback'](quote)
                    except Exception as e:
                        logger.error(f"处理订阅数据失败 {code}: {e}")
                
                # 等待下一次更新
                await asyncio.sleep(1)  # 1秒更新一次
                
        except Exception as e:
            logger.error(f"订阅任务异常 {subscription_id}: {e}")
        finally:
            # 清理订阅
            with self.subscription_lock:
                if subscription_id in self.subscriptions:
                    del self.subscriptions[subscription_id]
    
    def unsubscribe_realtime_data(self, subscription_id: str):
        """取消订阅"""
        with self.subscription_lock:
            if subscription_id in self.subscriptions:
                self.subscriptions[subscription_id]['active'] = False
                logger.info(f"取消订阅: {subscription_id}")
    
    def _get_cache(self, key: str):
        """获取缓存数据"""
        with self.cache_lock:
            return self.realtime_cache.get(key)
    
    def _set_cache(self, key: str, value: Any, ttl: int = 3600):
        """设置缓存数据"""
        with self.cache_lock:
            self.realtime_cache[key] = {
                'data': value,
                'timestamp': time.time(),
                'ttl': ttl
            }
    
    def _is_cache_valid(self, cached_item: Dict, ttl: int) -> bool:
        """检查缓存是否有效"""
        if not cached_item:
            return False
        
        current_time = time.time()
        cache_time = cached_item.get('timestamp', 0)
        cache_ttl = cached_item.get('ttl', ttl)
        
        return (current_time - cache_time) < cache_ttl
    
    async def get_market_overview(self) -> Dict[str, Any]:
        """获取市场概览"""
        try:
            market_data = {}
            
            # 获取主要指数数据
            indices = ['000001.XSHG', '399001.XSHE', '399006.XSHE']  # 上证、深证、创业板
            
            for index_code in indices:
                quote = await self.get_realtime_quote(index_code, 'jq')
                if quote:
                    market_data[index_code] = asdict(quote)
            
            # 获取数据质量报告
            quality_report = self.quality_monitor.get_quality_report()
            
            return {
                'market_data': market_data,
                'quality_report': quality_report,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"获取市场概览失败: {e}")
            return {}
    
    def get_service_status(self) -> Dict[str, Any]:
        """获取服务状态"""
        return {
            'service_name': 'RealTimeDataService',
            'status': 'running',
            'data_sources': list(self.data_sources.keys()),
            'active_subscriptions': len([s for s in self.subscriptions.values() if s['active']]),
            'cache_size': len(self.realtime_cache),
            'quality_monitor': self.quality_monitor.get_quality_report(),
            'timestamp': datetime.now().isoformat()
        }
    
    def cleanup(self):
        """清理资源"""
        self.stop_quality_monitor = True
        if self.quality_thread:
            self.quality_thread.join(timeout=5)
        
        # 清理订阅
        with self.subscription_lock:
            for subscription_id in list(self.subscriptions.keys()):
                self.unsubscribe_realtime_data(subscription_id)
        
        logger.info("实时数据服务清理完成")

# 全局实例
realtime_data_service = RealTimeDataService()

# 清理函数
def cleanup_realtime_data_service():
    """清理实时数据服务"""
    realtime_data_service.cleanup()

# 在应用退出时注册清理函数
import atexit
atexit.register(cleanup_realtime_data_service)
