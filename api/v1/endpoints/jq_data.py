"""
聚宽数据API端点 v1
"""

from fastapi import APIRouter, HTTPException, status, Query
from fastapi.responses import JSONResponse
from typing import List, Optional
import logging
from datetime import datetime, timedelta
import sys
import os
import json
import numpy as np
import pandas as pd

# Add project root to Python path for module discovery
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

try:
    from services.jq_service import jq_service, SafeJSONEncoder
except ImportError:
    logging.warning("无法导入聚宽服务，使用模拟服务")
    jq_service = None
    SafeJSONEncoder = None

logger = logging.getLogger(__name__)

class SafeJSONResponse(JSONResponse):
    """安全的JSON响应，使用自定义编码器"""
    
    def render(self, content) -> bytes:
        if SafeJSONEncoder:
            return json.dumps(
                content,
                ensure_ascii=False,
                separators=(',', ':'),
                cls=SafeJSONEncoder
            ).encode('utf-8')
        else:
            return super().render(content)

def clean_data_for_json(data):
    """清理数据，确保JSON兼容性"""
    if isinstance(data, dict):
        cleaned = {}
        for key, value in data.items():
            cleaned[key] = clean_data_for_json(value)
        return cleaned
    elif isinstance(data, list):
        return [clean_data_for_json(item) for item in data]
    elif isinstance(data, (np.integer, np.floating)):
        try:
            result = float(data)
            if np.isnan(result) or np.isinf(result):
                return 0.0
            return result
        except:
            return 0.0
    elif isinstance(data, (np.ndarray, pd.Series)):
        return data.tolist() if hasattr(data, 'tolist') else str(data)
    elif pd.isna(data):
        return None
    elif isinstance(data, (datetime, pd.Timestamp)):
        return data.isoformat()
    else:
        return data

router = APIRouter()

@router.get("/status")
async def get_jq_status():
    """获取聚宽连接状态"""
    try:
        if jq_service is None:
            return {
                "service": "聚宽数据服务",
                "status": {
                    "is_connected": False,
                    "status": "service_unavailable",
                    "username": None,
                    "last_check": datetime.now().isoformat(),
                    "error": "聚宽服务未初始化"
                }
            }
        
        status_info = await jq_service.get_connection_status()
        return {
            "service": "聚宽数据服务",
            "status": status_info
        }
    except Exception as e:
        logger.error(f"获取聚宽状态失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取聚宽状态失败"
        )

@router.post("/connect")
async def connect_jq():
    """连接聚宽服务器"""
    try:
        if jq_service is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="聚宽服务不可用"
            )
        
        success = await jq_service.connect()
        if success:
            return {
                "message": "聚宽服务器连接成功",
                "status": "connected"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="聚宽服务器连接失败"
            )
    except Exception as e:
        logger.error(f"连接聚宽服务器失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"连接聚宽服务器失败: {str(e)}"
        )

@router.post("/disconnect")
async def disconnect_jq():
    """断开聚宽连接"""
    try:
        if jq_service is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="聚宽服务不可用"
            )
        
        await jq_service.disconnect()
        return {
            "message": "聚宽连接已断开",
            "status": "disconnected"
        }
    except Exception as e:
        logger.error(f"断开聚宽连接失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="断开聚宽连接失败"
        )

@router.get("/stocks")
async def get_stocks(
    market: str = Query(default='CN', description="市场类型: CN=A股, HK=港股, US=美股"),
    limit: int = Query(default=50, description="返回数量限制，最大100")
):
    """获取股票列表（增强版，包含价格和涨幅）"""
    try:
        if jq_service is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="聚宽服务不可用"
            )
        
        # 限制数量
        if limit > 100:
            limit = 100
        elif limit < 1:
            limit = 50
        
        stocks = await jq_service.get_stock_list(market)
        
        # 应用数量限制
        if len(stocks) > limit:
            stocks = stocks[:limit]
        
        response_data = {
            "market": market,
            "count": len(stocks),
            "total_available": len(stocks),
            "limit": limit,
            "stocks": stocks,
            "timestamp": datetime.now().isoformat()
        }
        
        # 清理数据确保JSON兼容性
        cleaned_response = clean_data_for_json(response_data)
        
        return cleaned_response
        
    except Exception as e:
        logger.error(f"获取股票列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取股票列表失败"
        )

@router.get("/daily-data/{stock_code}")
async def get_daily_data(
    stock_code: str,
    start_date: str = Query(..., description="开始日期 (YYYY-MM-DD)"),
    end_date: str = Query(..., description="结束日期 (YYYY-MM-DD)"),
    fields: Optional[str] = Query(None, description="字段列表，用逗号分隔")
):
    """获取日线数据"""
    try:
        if jq_service is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="聚宽服务不可用"
            )
        
        # 解析字段列表
        field_list = None
        if fields:
            field_list = [f.strip() for f in fields.split(',')]
        
        data = await jq_service.get_daily_data(
            stock_code, start_date, end_date, field_list
        )
        
        if data.empty:
            return {
                "stock_code": stock_code,
                "start_date": start_date,
                "end_date": end_date,
                "data": [],
                "count": 0
            }
        
        # 转换数据为JSON格式
        data_json = data.to_dict('records')
        
        return {
            "stock_code": stock_code,
            "start_date": start_date,
            "end_date": end_date,
            "data": data_json,
            "count": len(data_json)
        }
    except Exception as e:
        logger.error(f"获取日线数据失败 {stock_code}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取日线数据失败: {str(e)}"
        )

@router.get("/realtime-quotes")
async def get_realtime_quotes(
    stock_codes: str = Query(..., description="股票代码列表，用逗号分隔")
):
    """获取实时行情"""
    try:
        if jq_service is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="聚宽服务不可用"
            )
        
        # 解析股票代码列表
        codes = [code.strip() for code in stock_codes.split(',')]
        
        # 限制请求数量
        if len(codes) > 50:
            codes = codes[:50]
            logger.warning(f"请求股票数量过多，限制为50只")
        
        quotes = await jq_service.get_realtime_quotes(codes)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "count": len(quotes),
            "quotes": quotes
        }
    except Exception as e:
        logger.error(f"获取实时行情失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取实时行情失败"
        )

@router.get("/stock-info")
async def get_stock_info(
    stock_codes: str = Query(..., description="股票代码列表，用逗号分隔")
):
    """获取股票基本信息"""
    try:
        if jq_service is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="聚宽服务不可用"
            )
        
        # 解析股票代码列表
        codes = [code.strip() for code in stock_codes.split(',')]
        
        # 限制请求数量
        if len(codes) > 100:
            codes = codes[:100]
            logger.warning(f"请求股票数量过多，限制为100只")
        
        stock_info = await jq_service.get_stock_info(codes)
        
        return {
            "count": len(stock_info),
            "stocks": stock_info
        }
    except Exception as e:
        logger.error(f"获取股票信息失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取股票信息失败"
        )

@router.get("/financial-data/{stock_code}")
async def get_financial_data(
    stock_code: str,
    report_type: str = Query(default='annual', description="报告类型: annual=年报, quarterly=季报"),
    fields: Optional[str] = Query(None, description="字段列表，用逗号分隔")
):
    """获取财务数据"""
    try:
        if jq_service is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="聚宽服务不可用"
            )
        
        # 解析字段列表
        field_list = None
        if fields:
            field_list = [f.strip() for f in fields.split(',')]
        
        data = await jq_service.get_financial_data(
            stock_code, report_type, field_list
        )
        
        if data.empty:
            return {
                "stock_code": stock_code,
                "report_type": report_type,
                "data": [],
                "count": 0
            }
        
        # 转换数据为JSON格式
        data_json = data.to_dict('records')
        
        return {
            "stock_code": stock_code,
            "report_type": report_type,
            "data": data_json,
            "count": len(data_json)
        }
    except Exception as e:
        logger.error(f"获取财务数据失败 {stock_code}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取财务数据失败"
        )

@router.get("/health")
async def jq_health_check():
    """聚宽服务健康检查"""
    try:
        if jq_service is None:
            return {
                "service": "jq_service",
                "status": "unhealthy",
                "error": "聚宽服务未初始化",
                "last_check": datetime.now().isoformat()
            }
        
        health_info = await jq_service.health_check()
        return health_info
    except Exception as e:
        logger.error(f"聚宽健康检查失败: {e}")
        return {
            "service": "jq_service",
            "status": "unhealthy",
            "error": str(e),
            "last_check": datetime.now().isoformat()
        }

@router.get("/market-overview")
async def get_market_overview():
    """获取市场概览"""
    try:
        if jq_service is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="聚宽服务不可用"
            )
        
        overview = await jq_service.get_market_overview()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "overview": overview
        }
    except Exception as e:
        logger.error(f"获取市场概览失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取市场概览失败"
        )

@router.get("/sector-performance")
async def get_sector_performance():
    """获取行业板块表现"""
    try:
        if jq_service is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="聚宽服务不可用"
            )
        
        performance = await jq_service.get_sector_performance()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "performance": performance
        }
    except Exception as e:
        logger.error(f"获取行业板块表现失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取行业板块表现失败"
        )

@router.get("/available-date-range")
async def get_available_date_range():
    """获取可用的日期范围"""
    try:
        if jq_service is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="聚宽服务不可用"
            )
        
        # 从服务状态中获取日期范围
        status_info = await jq_service.get_connection_status()
        date_range = status_info.get('available_date_range', [])
        
        return {
            "available_date_range": date_range,
            "note": "根据账号权限自动调整的可用日期范围"
        }
    except Exception as e:
        logger.error(f"获取可用日期范围失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取可用日期范围失败"
        )

@router.delete("/cache")
async def clear_cache(
    pattern: str = Query(default="*", description="缓存文件匹配模式，*表示清理所有缓存")
):
    """清理聚宽数据缓存"""
    try:
        if jq_service is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="聚宽服务不可用"
            )
        
        result = jq_service.clear_cache(pattern)
        
        if result["success"]:
            return {
                "message": "缓存清理成功",
                "details": result
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["message"]
            )
            
    except Exception as e:
        logger.error(f"清理缓存失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="清理缓存失败"
        )
