"""
智能投顾API端点 v1
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Form
from typing import List, Optional, Dict, Any
import logging
import sys
import os

# Add project root to Python path for module discovery
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

try:
    from services.robo_advisor import robo_advisor
except ImportError:
    logging.warning("无法导入智能投顾服务，使用模拟服务")
    robo_advisor = None

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/create-profile")
async def create_user_profile(
    user_id: int = Form(..., description="用户ID"),
    age: int = Form(..., description="年龄"),
    income_level: str = Form(..., description="收入水平"),
    investment_experience: str = Form(..., description="投资经验"),
    risk_tolerance: str = Form(..., description="风险偏好"),
    investment_goal: str = Form(..., description="投资目标"),
    investment_horizon: int = Form(..., description="投资期限"),
    liquidity_needs: str = Form(..., description="流动性需求"),
    tax_situation: str = Form(..., description="税务情况")
):
    """创建用户画像"""
    try:
        if robo_advisor is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="智能投顾服务不可用"
            )
        
        result = await robo_advisor.create_user_profile(
            user_id=user_id,
            age=age,
            income_level=income_level,
            investment_experience=investment_experience,
            risk_tolerance=risk_tolerance,
            investment_goal=investment_goal,
            investment_horizon=investment_horizon,
            liquidity_needs=liquidity_needs,
            tax_situation=tax_situation
        )
        
        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )
        
        return result
        
    except Exception as e:
        logger.error(f"创建用户画像失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建用户画像失败"
        )

@router.get("/profile/{user_id}")
async def get_user_profile(user_id: int):
    """获取用户画像"""
    try:
        if robo_advisor is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="智能投顾服务不可用"
            )
        
        profile = await robo_advisor.get_user_profile(user_id)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户画像不存在"
            )
        
        return profile
        
    except Exception as e:
        logger.error(f"获取用户画像失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取用户画像失败"
        )

@router.get("/allocation/{user_id}")
async def get_asset_allocation(user_id: int):
    """获取资产配置"""
    try:
        if robo_advisor is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="智能投顾服务不可用"
            )
        
        allocation = await robo_advisor.get_asset_allocation(user_id)
        if not allocation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="资产配置不存在"
            )
        
        return allocation
        
    except Exception as e:
        logger.error(f"获取资产配置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取资产配置失败"
        )

@router.post("/generate-recommendations")
async def generate_strategy_recommendations(user_id: int = Form(..., description="用户ID")):
    """生成策略推荐"""
    try:
        if robo_advisor is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="智能投顾服务不可用"
            )
        
        recommendations = await robo_advisor.generate_strategy_recommendations(user_id)
        return {"recommendations": recommendations}
        
    except Exception as e:
        logger.error(f"生成策略推荐失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="生成策略推荐失败"
        )

@router.post("/optimize-portfolio")
async def optimize_portfolio(user_id: int = Form(..., description="用户ID")):
    """优化投资组合"""
    try:
        if robo_advisor is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="智能投顾服务不可用"
            )
        
        optimization = await robo_advisor.optimize_portfolio(user_id)
        if not optimization:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="投资组合优化失败"
            )
        
        return optimization
        
    except Exception as e:
        logger.error(f"优化投资组合失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="优化投资组合失败"
        )

@router.get("/recommendations/{user_id}")
async def get_user_recommendations(user_id: int):
    """获取用户推荐"""
    try:
        if robo_advisor is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="智能投顾服务不可用"
            )
        
        recommendations = await robo_advisor.get_user_recommendations(user_id)
        return {"recommendations": recommendations}
        
    except Exception as e:
        logger.error(f"获取用户推荐失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取用户推荐失败"
        )

@router.get("/optimizations/{user_id}")
async def get_portfolio_optimizations(user_id: int):
    """获取投资组合优化记录"""
    try:
        if robo_advisor is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="智能投顾服务不可用"
            )
        
        optimizations = await robo_advisor.get_portfolio_optimizations(user_id)
        return {"optimizations": optimizations}
        
    except Exception as e:
        logger.error(f"获取投资组合优化记录失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取投资组合优化记录失败"
        )
