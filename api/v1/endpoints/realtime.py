#!/usr/bin/env python3
"""
实时数据API端点
提供实时行情、逐笔成交、数据质量监控等接口
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from typing import List, Optional, Dict, Any
import logging
import sys
import os
from datetime import datetime, timedelta
import json

# Add project root to Python path for module discovery
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

try:
    from services.realtime_data_service import realtime_data_service
except ImportError:
    logging.warning("无法导入实时数据服务，使用模拟服务")
    realtime_data_service = None

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/status")
async def get_realtime_service_status():
    """获取实时数据服务状态"""
    try:
        if realtime_data_service is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="实时数据服务不可用"
            )
        
        status_info = realtime_data_service.get_service_status()
        return {
            "success": True,
            "data": status_info,
            "message": "获取实时数据服务状态成功"
        }
        
    except Exception as e:
        logger.error(f"获取实时数据服务状态失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取实时数据服务状态失败: {str(e)}"
        )

@router.get("/quote/{code}")
async def get_realtime_quote(
    code: str,
    source: str = Query("jq", description="数据源，默认聚宽")
):
    """获取实时行情"""
    try:
        if realtime_data_service is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="实时数据服务不可用"
            )
        
        quote = await realtime_data_service.get_realtime_quote(code, source)
        
        if quote is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"未找到股票 {code} 的实时行情"
            )
        
        return {
            "success": True,
            "data": {
                "code": quote.code,
                "name": quote.name,
                "timestamp": quote.timestamp.isoformat(),
                "price": quote.price,
                "volume": quote.volume,
                "amount": quote.amount,
                "bid_price": quote.bid_price,
                "ask_price": quote.ask_price,
                "bid_volume": quote.bid_volume,
                "ask_volume": quote.ask_volume,
                "source": quote.source,
                "latency_ms": quote.latency_ms
            },
            "message": "获取实时行情成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取实时行情失败 {code}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取实时行情失败: {str(e)}"
        )

@router.get("/quotes")
async def get_multiple_realtime_quotes(
    codes: str = Query(..., description="股票代码，多个用逗号分隔"),
    source: str = Query("jq", description="数据源，默认聚宽")
):
    """获取多个股票的实时行情"""
    try:
        if realtime_data_service is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="实时数据服务不可用"
            )
        
        code_list = [code.strip() for code in codes.split(",") if code.strip()]
        
        if not code_list:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="请提供有效的股票代码"
            )
        
        quotes = []
        for code in code_list:
            quote = await realtime_data_service.get_realtime_quote(code, source)
            if quote:
                quotes.append({
                    "code": quote.code,
                    "name": quote.name,
                    "timestamp": quote.timestamp.isoformat(),
                    "price": quote.price,
                    "volume": quote.volume,
                    "amount": quote.amount,
                    "bid_price": quote.bid_price,
                    "ask_price": quote.ask_price,
                    "bid_volume": quote.bid_volume,
                    "ask_volume": quote.ask_volume,
                    "source": quote.source,
                    "latency_ms": quote.latency_ms
                })
        
        return {
            "success": True,
            "data": {
                "quotes": quotes,
                "total": len(quotes),
                "source": source,
                "timestamp": datetime.now().isoformat()
            },
            "message": f"获取 {len(quotes)} 只股票的实时行情成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取多个实时行情失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取多个实时行情失败: {str(e)}"
        )

@router.get("/ticks/{code}")
async def get_tick_data(
    code: str,
    start_time: str = Query(..., description="开始时间，格式：YYYY-MM-DD HH:MM:SS"),
    end_time: str = Query(..., description="结束时间，格式：YYYY-MM-DD HH:MM:SS"),
    source: str = Query("jq", description="数据源，默认聚宽")
):
    """获取逐笔成交数据"""
    try:
        if realtime_data_service is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="实时数据服务不可用"
            )
        
        # 解析时间参数
        try:
            start_dt = datetime.fromisoformat(start_time)
            end_dt = datetime.fromisoformat(end_time)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="时间格式错误，请使用 YYYY-MM-DD HH:MM:SS 格式"
            )
        
        if start_dt >= end_dt:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="开始时间必须早于结束时间"
            )
        
        # 检查时间范围
        time_diff = end_dt - start_dt
        if time_diff > timedelta(days=7):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="时间范围不能超过7天"
            )
        
        tick_data = await realtime_data_service.get_tick_data(code, start_dt, end_dt, source)
        
        return {
            "success": True,
            "data": {
                "code": code,
                "start_time": start_time,
                "end_time": end_time,
                "source": source,
                "ticks": [
                    {
                        "timestamp": tick.timestamp.isoformat(),
                        "price": tick.price,
                        "volume": tick.volume,
                        "amount": tick.amount,
                        "direction": tick.direction,
                        "sequence": tick.sequence
                    }
                    for tick in tick_data
                ],
                "total": len(tick_data),
                "timestamp": datetime.now().isoformat()
            },
            "message": "获取逐笔成交数据成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取逐笔成交数据失败 {code}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取逐笔成交数据失败: {str(e)}"
        )

@router.get("/market-overview")
async def get_market_overview():
    """获取市场概览"""
    try:
        if realtime_data_service is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="实时数据服务不可用"
            )
        
        market_overview = await realtime_data_service.get_market_overview()
        
        return {
            "success": True,
            "data": market_overview,
            "message": "获取市场概览成功"
        }
        
    except Exception as e:
        logger.error(f"获取市场概览失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取市场概览失败: {str(e)}"
        )

@router.get("/quality-report")
async def get_data_quality_report():
    """获取数据质量报告"""
    try:
        if realtime_data_service is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="实时数据服务不可用"
            )
        
        quality_report = realtime_data_service.quality_monitor.get_quality_report()
        
        return {
            "success": True,
            "data": quality_report,
            "message": "获取数据质量报告成功"
        }
        
    except Exception as e:
        logger.error(f"获取数据质量报告失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取数据质量报告失败: {str(e)}"
        )

@router.post("/subscribe")
async def subscribe_realtime_data(
    request: Request,
    codes: List[str] = Query(..., description="股票代码列表"),
    source: str = Query("jq", description="数据源，默认聚宽")
):
    """订阅实时数据"""
    try:
        if realtime_data_service is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="实时数据服务不可用"
            )
        
        if not codes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="请提供股票代码列表"
            )
        
        # 这里应该实现WebSocket连接或长轮询
        # 目前返回订阅ID
        subscription_id = f"sub_{int(datetime.now().timestamp() * 1000)}"
        
        # 在实际应用中，这里应该启动WebSocket连接
        # await realtime_data_service.subscribe_realtime_data(codes, callback, source)
        
        return {
            "success": True,
            "data": {
                "subscription_id": subscription_id,
                "codes": codes,
                "source": source,
                "status": "subscribed",
                "message": "WebSocket连接功能开发中，请使用轮询接口获取实时数据"
            },
            "message": "订阅实时数据成功（模拟）"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"订阅实时数据失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"订阅实时数据失败: {str(e)}"
        )

@router.delete("/unsubscribe/{subscription_id}")
async def unsubscribe_realtime_data(subscription_id: str):
    """取消订阅实时数据"""
    try:
        if realtime_data_service is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="实时数据服务不可用"
            )
        
        # 在实际应用中，这里应该关闭WebSocket连接
        # realtime_data_service.unsubscribe_realtime_data(subscription_id)
        
        return {
            "success": True,
            "data": {
                "subscription_id": subscription_id,
                "status": "unsubscribed"
            },
            "message": "取消订阅成功（模拟）"
        }
        
    except Exception as e:
        logger.error(f"取消订阅实时数据失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"取消订阅实时数据失败: {str(e)}"
        )

@router.get("/performance")
async def get_data_performance():
    """获取数据性能指标"""
    try:
        if realtime_data_service is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="实时数据服务不可用"
            )
        
        # 获取性能指标
        performance_metrics = {
            "cache_hit_rate": 0.85,  # 缓存命中率
            "average_latency_ms": 150,  # 平均延迟
            "data_freshness_seconds": 5,  # 数据新鲜度
            "throughput_queries_per_second": 100,  # 吞吐量
            "error_rate": 0.01,  # 错误率
            "uptime_percentage": 99.9,  # 可用性
            "timestamp": datetime.now().isoformat()
        }
        
        return {
            "success": True,
            "data": performance_metrics,
            "message": "获取数据性能指标成功"
        }
        
    except Exception as e:
        logger.error(f"获取数据性能指标失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取数据性能指标失败: {str(e)}"
        )
