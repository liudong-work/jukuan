"""
智能交易助手API端点 v1
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Form
from typing import List, Optional, Dict, Any
import logging
import sys
import os

# Add project root to Python path for module discovery
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

try:
    from services.smart_trading_assistant import smart_trading_assistant
except ImportError:
    logging.warning("无法导入智能交易助手，使用模拟服务")
    smart_trading_assistant = None

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/market-sentiment")
async def get_market_sentiment():
    """获取市场情绪分析"""
    try:
        if smart_trading_assistant is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="智能交易助手不可用"
            )
        
        analysis = await smart_trading_assistant.analyze_market_sentiment()
        return asdict(analysis)
        
    except Exception as e:
        logger.error(f"获取市场情绪分析失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取市场情绪分析失败"
        )

@router.get("/stock-analysis/{stock_code}")
async def get_stock_analysis(stock_code: str):
    """获取个股分析"""
    try:
        if smart_trading_assistant is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="智能交易助手不可用"
            )
        
        analysis = await smart_trading_assistant.analyze_stock(stock_code)
        return asdict(analysis)
        
    except Exception as e:
        logger.error(f"获取个股分析失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取个股分析失败"
        )

@router.get("/portfolio-insight")
async def get_portfolio_insight():
    """获取投资组合洞察"""
    try:
        if smart_trading_assistant is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="智能交易助手不可用"
            )
        
        insight = await smart_trading_assistant.analyze_portfolio()
        return asdict(insight)
        
    except Exception as e:
        logger.error(f"获取投资组合洞察失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取投资组合洞察失败"
        )

@router.get("/trading-advice")
async def get_trading_advice(stock_code: Optional[str] = Query(None, description="股票代码")):
    """获取交易建议"""
    try:
        if smart_trading_assistant is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="智能交易助手不可用"
            )
        
        advice = await smart_trading_assistant.get_trading_advice(stock_code)
        return advice
        
    except Exception as e:
        logger.error(f"获取交易建议失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取交易建议失败"
        )

@router.get("/analysis-history")
async def get_analysis_history():
    """获取分析历史"""
    try:
        if smart_trading_assistant is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="智能交易助手不可用"
            )
        
        # 加载分析历史
        analysis_data = smart_trading_assistant._load_data(smart_trading_assistant.analysis_file)
        insights_data = smart_trading_assistant._load_data(smart_trading_assistant.insights_file)
        
        return {
            "market_analyses": analysis_data.get("analyses", [])[-10:],  # 最近10次
            "portfolio_insights": insights_data.get("insights", [])[-10:]  # 最近10次
        }
        
    except Exception as e:
        logger.error(f"获取分析历史失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取分析历史失败"
        )
