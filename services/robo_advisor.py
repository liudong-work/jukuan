"""
智能投顾系统
提供个性化策略推荐、资产配置优化、风险偏好匹配等功能
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import json
import os
import numpy as np
import pandas as pd
from dataclasses import dataclass, asdict
from enum import Enum

# 导入相关服务
try:
    from .enhanced_trading_service import enhanced_trading_service
    from .strategy_service import strategy_service
    from .ml_strategy_service import ml_strategy_service
    from .market_data_service import market_data_service
except ImportError:
    enhanced_trading_service = None
    strategy_service = None
    ml_strategy_service = None
    market_data_service = None

logger = logging.getLogger(__name__)

class RiskLevel(Enum):
    """风险等级枚举"""
    CONSERVATIVE = "保守型"      # 低风险
    MODERATE = "稳健型"         # 中风险
    AGGRESSIVE = "激进型"       # 高风险

class InvestmentGoal(Enum):
    """投资目标枚举"""
    CAPITAL_PRESERVATION = "资本保值"      # 保值
    INCOME_GENERATION = "收益获取"        # 收益
    GROWTH = "资本增值"                   # 增值
    SPECULATION = "投机获利"              # 投机

@dataclass
class UserProfile:
    """用户画像数据结构"""
    user_id: int
    age: int
    income_level: str  # low, medium, high
    investment_experience: str  # beginner, intermediate, advanced
    risk_tolerance: RiskLevel
    investment_goal: InvestmentGoal
    investment_horizon: int  # 投资期限（年）
    liquidity_needs: str  # low, medium, high
    tax_situation: str  # low, medium, high
    created_at: datetime
    updated_at: datetime

@dataclass
class AssetAllocation:
    """资产配置数据结构"""
    allocation_id: str
    user_id: int
    risk_level: RiskLevel
    stock_ratio: float      # 股票比例
    bond_ratio: float       # 债券比例
    cash_ratio: float       # 现金比例
    alternative_ratio: float # 另类投资比例
    rebalance_frequency: str # 再平衡频率
    created_at: datetime

@dataclass
class StrategyRecommendation:
    """策略推荐数据结构"""
    recommendation_id: str
    user_id: int
    strategy_id: str
    strategy_name: str
    strategy_type: str
    confidence_score: float
    expected_return: float
    risk_level: RiskLevel
    investment_horizon: int
    reasoning: str
    created_at: datetime

@dataclass
class PortfolioOptimization:
    """投资组合优化数据结构"""
    optimization_id: str
    user_id: int
    current_allocation: Dict[str, float]
    optimized_allocation: Dict[str, float]
    expected_return: float
    expected_risk: float
    sharpe_ratio: float
    max_drawdown: float
    rebalance_recommendations: List[Dict[str, Any]]
    created_at: datetime

class RoboAdvisor:
    """智能投顾系统"""
    
    def __init__(self):
        self.profiles_file = "data/user_profiles.json"
        self.allocations_file = "data/asset_allocations.json"
        self.recommendations_file = "data/strategy_recommendations.json"
        self.optimizations_file = "data/portfolio_optimizations.json"
        
        # 确保目录存在
        os.makedirs("data", exist_ok=True)
        
        # 初始化数据文件
        self._init_data_files()
        
        # 风险等级配置
        self.risk_configs = {
            RiskLevel.CONSERVATIVE: {
                "stock_ratio": 0.2,
                "bond_ratio": 0.6,
                "cash_ratio": 0.15,
                "alternative_ratio": 0.05,
                "expected_return": 0.06,
                "expected_risk": 0.08
            },
            RiskLevel.MODERATE: {
                "stock_ratio": 0.5,
                "bond_ratio": 0.35,
                "cash_ratio": 0.1,
                "alternative_ratio": 0.05,
                "expected_return": 0.09,
                "expected_risk": 0.12
            },
            RiskLevel.AGGRESSIVE: {
                "stock_ratio": 0.8,
                "bond_ratio": 0.1,
                "cash_ratio": 0.05,
                "alternative_ratio": 0.05,
                "expected_return": 0.12,
                "expected_risk": 0.18
            }
        }
        
        # 投资目标权重
        self.goal_weights = {
            InvestmentGoal.CAPITAL_PRESERVATION: {"conservative": 0.8, "moderate": 0.2, "aggressive": 0.0},
            InvestmentGoal.INCOME_GENERATION: {"conservative": 0.6, "moderate": 0.3, "aggressive": 0.1},
            InvestmentGoal.GROWTH: {"conservative": 0.2, "moderate": 0.6, "aggressive": 0.2},
            InvestmentGoal.SPECULATION: {"conservative": 0.0, "moderate": 0.3, "aggressive": 0.7}
        }
        
        logger.info("智能投顾系统已启动")
    
    def _init_data_files(self):
        """初始化数据文件"""
        if not os.path.exists(self.profiles_file):
            self._save_data(self.profiles_file, {"profiles": []})
        if not os.path.exists(self.allocations_file):
            self._save_data(self.allocations_file, {"allocations": []})
        if not os.path.exists(self.recommendations_file):
            self._save_data(self.recommendations_file, {"recommendations": []})
        if not os.path.exists(self.optimizations_file):
            self._save_data(self.optimizations_file, {"optimizations": []})
    
    def _save_data(self, file_path: str, data: Any):
        """保存数据到文件"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        except Exception as e:
            logger.error(f"保存数据失败 {file_path}: {e}")
    
    def _load_data(self, file_path: str) -> Any:
        """从文件加载数据"""
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return None
        except Exception as e:
            logger.error(f"加载数据失败 {file_path}: {e}")
            return None
    
    async def create_user_profile(self, user_id: int, age: int, income_level: str,
                                 investment_experience: str, risk_tolerance: str,
                                 investment_goal: str, investment_horizon: int,
                                 liquidity_needs: str, tax_situation: str) -> Dict[str, Any]:
        """创建用户画像"""
        try:
            # 验证输入参数
            if age < 18 or age > 100:
                return {"error": "年龄必须在18-100之间"}
            
            if investment_horizon < 1 or investment_horizon > 50:
                return {"error": "投资期限必须在1-50年之间"}
            
            # 创建用户画像
            profile = UserProfile(
                user_id=user_id,
                age=age,
                income_level=income_level,
                investment_experience=investment_experience,
                risk_tolerance=RiskLevel(risk_tolerance),
                investment_goal=InvestmentGoal(investment_goal),
                investment_horizon=investment_horizon,
                liquidity_needs=liquidity_needs,
                tax_situation=tax_situation,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            # 保存用户画像
            profiles_data = self._load_data(self.profiles_file)
            profiles_data["profiles"].append(asdict(profile))
            self._save_data(self.profiles_file, profiles_data)
            
            # 自动创建资产配置
            await self._create_asset_allocation(user_id, profile)
            
            logger.info(f"用户画像创建成功: {user_id}")
            return {"message": "用户画像创建成功", "profile": asdict(profile)}
            
        except Exception as e:
            logger.error(f"创建用户画像失败: {e}")
            return {"error": f"创建用户画像失败: {e}"}
    
    async def _create_asset_allocation(self, user_id: int, profile: UserProfile):
        """自动创建资产配置"""
        try:
            # 根据用户画像确定风险等级
            risk_level = self._determine_risk_level(profile)
            
            # 获取风险配置
            risk_config = self.risk_configs[risk_level]
            
            # 创建资产配置
            allocation = AssetAllocation(
                allocation_id=f"allocation_{user_id}",
                user_id=user_id,
                risk_level=risk_level,
                stock_ratio=risk_config["stock_ratio"],
                bond_ratio=risk_config["bond_ratio"],
                cash_ratio=risk_config["cash_ratio"],
                alternative_ratio=risk_config["alternative_ratio"],
                rebalance_frequency="monthly",
                created_at=datetime.now()
            )
            
            # 保存资产配置
            allocations_data = self._load_data(self.allocations_file)
            allocations_data["allocations"].append(asdict(allocation))
            self._save_data(self.allocations_file, allocations_data)
            
        except Exception as e:
            logger.error(f"创建资产配置失败: {e}")
    
    def _determine_risk_level(self, profile: UserProfile) -> RiskLevel:
        """根据用户画像确定风险等级"""
        try:
            # 基础风险分数
            risk_score = 0
            
            # 年龄因素
            if profile.age < 30:
                risk_score += 3
            elif profile.age < 50:
                risk_score += 2
            elif profile.age < 65:
                risk_score += 1
            else:
                risk_score += 0
            
            # 收入水平
            if profile.income_level == "high":
                risk_score += 2
            elif profile.income_level == "medium":
                risk_score += 1
            else:
                risk_score += 0
            
            # 投资经验
            if profile.investment_experience == "advanced":
                risk_score += 2
            elif profile.investment_experience == "intermediate":
                risk_score += 1
            else:
                risk_score += 0
            
            # 投资期限
            if profile.investment_horizon >= 10:
                risk_score += 2
            elif profile.investment_horizon >= 5:
                risk_score += 1
            else:
                risk_score += 0
            
            # 流动性需求
            if profile.liquidity_needs == "low":
                risk_score += 1
            elif profile.liquidity_needs == "medium":
                risk_score += 0
            else:
                risk_score += -1
            
            # 根据分数确定风险等级
            if risk_score >= 6:
                return RiskLevel.AGGRESSIVE
            elif risk_score >= 3:
                return RiskLevel.MODERATE
            else:
                return RiskLevel.CONSERVATIVE
                
        except Exception as e:
            logger.error(f"确定风险等级失败: {e}")
            return RiskLevel.MODERATE
    
    async def get_user_profile(self, user_id: int) -> Optional[UserProfile]:
        """获取用户画像"""
        try:
            profiles_data = self._load_data(self.profiles_file)
            profile_data = next((p for p in profiles_data["profiles"] if p["user_id"] == user_id), None)
            
            if profile_data:
                return UserProfile(
                    user_id=profile_data["user_id"],
                    age=profile_data["age"],
                    income_level=profile_data["income_level"],
                    investment_experience=profile_data["investment_experience"],
                    risk_tolerance=RiskLevel(profile_data["risk_tolerance"]),
                    investment_goal=InvestmentGoal(profile_data["investment_goal"]),
                    investment_horizon=profile_data["investment_horizon"],
                    liquidity_needs=profile_data["liquidity_needs"],
                    tax_situation=profile_data["tax_situation"],
                    created_at=datetime.fromisoformat(profile_data["created_at"]),
                    updated_at=datetime.fromisoformat(profile_data["updated_at"])
                )
            
            return None
            
        except Exception as e:
            logger.error(f"获取用户画像失败: {e}")
            return None
    
    async def get_asset_allocation(self, user_id: int) -> Optional[AssetAllocation]:
        """获取资产配置"""
        try:
            allocations_data = self._load_data(self.allocations_file)
            allocation_data = next((a for a in allocations_data["allocations"] if a["user_id"] == user_id), None)
            
            if allocation_data:
                return AssetAllocation(
                    allocation_id=allocation_data["allocation_id"],
                    user_id=allocation_data["user_id"],
                    risk_level=RiskLevel(allocation_data["risk_level"]),
                    stock_ratio=allocation_data["stock_ratio"],
                    bond_ratio=allocation_data["bond_ratio"],
                    cash_ratio=allocation_data["cash_ratio"],
                    alternative_ratio=allocation_data["alternative_ratio"],
                    rebalance_frequency=allocation_data["rebalance_frequency"],
                    created_at=datetime.fromisoformat(allocation_data["created_at"])
                )
            
            return None
            
        except Exception as e:
            logger.error(f"获取资产配置失败: {e}")
            return None
    
    async def generate_strategy_recommendations(self, user_id: int) -> List[Dict[str, Any]]:
        """生成策略推荐"""
        try:
            # 获取用户画像和资产配置
            profile = await self.get_user_profile(user_id)
            allocation = await self.get_asset_allocation(user_id)
            
            if not profile or not allocation:
                return []
            
            recommendations = []
            
            # 获取可用策略
            strategies = []
            if strategy_service:
                strategies.extend(await strategy_service.get_strategies())
            if ml_strategy_service:
                strategies.extend(await ml_strategy_service.get_strategies())
            
            # 为每个策略计算推荐分数
            for strategy in strategies:
                recommendation_score = self._calculate_recommendation_score(strategy, profile, allocation)
                
                if recommendation_score > 0.5:  # 只推荐分数大于0.5的策略
                    recommendation = StrategyRecommendation(
                        recommendation_id=f"rec_{user_id}_{strategy.get('strategy_id', 'unknown')}",
                        user_id=user_id,
                        strategy_id=strategy.get('strategy_id', ''),
                        strategy_name=strategy.get('name', ''),
                        strategy_type=strategy.get('strategy_type', ''),
                        confidence_score=recommendation_score,
                        expected_return=self._estimate_expected_return(strategy, allocation),
                        risk_level=allocation.risk_level,
                        investment_horizon=profile.investment_horizon,
                        reasoning=self._generate_recommendation_reasoning(strategy, profile, allocation),
                        created_at=datetime.now()
                    )
                    
                    recommendations.append(asdict(recommendation))
            
            # 按推荐分数排序
            recommendations.sort(key=lambda x: x['confidence_score'], reverse=True)
            
            # 保存推荐记录
            recommendations_data = self._load_data(self.recommendations_file)
            recommendations_data["recommendations"].extend(recommendations)
            self._save_data(self.recommendations_file, recommendations_data)
            
            return recommendations[:10]  # 返回前10个推荐
            
        except Exception as e:
            logger.error(f"生成策略推荐失败: {e}")
            return []
    
    def _calculate_recommendation_score(self, strategy: Dict[str, Any], 
                                      profile: UserProfile, allocation: AssetAllocation) -> float:
        """计算策略推荐分数"""
        try:
            score = 0.0
            
            # 风险匹配度
            strategy_risk = self._estimate_strategy_risk(strategy)
            risk_match = 1.0 - abs(strategy_risk - allocation.risk_level.value)
            score += risk_match * 0.4
            
            # 投资期限匹配度
            if profile.investment_horizon >= 5:
                score += 0.3
            elif profile.investment_horizon >= 2:
                score += 0.2
            else:
                score += 0.1
            
            # 投资目标匹配度
            goal_match = self._calculate_goal_match(strategy, profile.investment_goal)
            score += goal_match * 0.3
            
            return min(score, 1.0)
            
        except Exception as e:
            logger.error(f"计算推荐分数失败: {e}")
            return 0.0
    
    def _estimate_strategy_risk(self, strategy: Dict[str, Any]) -> float:
        """估算策略风险"""
        try:
            # 根据策略类型估算风险
            strategy_type = strategy.get('strategy_type', 'unknown')
            
            risk_mapping = {
                'ma_cross': 0.3,      # 均线交叉 - 低风险
                'kdj_macd': 0.5,      # KDJ+MACD - 中风险
                'random_forest': 0.6,  # 随机森林 - 中高风险
                'gradient_boosting': 0.7,  # 梯度提升 - 高风险
                'logistic_regression': 0.4  # 逻辑回归 - 中风险
            }
            
            return risk_mapping.get(strategy_type, 0.5)
            
        except Exception as e:
            logger.error(f"估算策略风险失败: {e}")
            return 0.5
    
    def _calculate_goal_match(self, strategy: Dict[str, Any], goal: InvestmentGoal) -> float:
        """计算投资目标匹配度"""
        try:
            strategy_type = strategy.get('strategy_type', 'unknown')
            
            # 根据策略类型和投资目标计算匹配度
            if goal == InvestmentGoal.CAPITAL_PRESERVATION:
                if strategy_type in ['ma_cross', 'logistic_regression']:
                    return 0.9
                else:
                    return 0.5
            elif goal == InvestmentGoal.INCOME_GENERATION:
                if strategy_type in ['ma_cross', 'kdj_macd']:
                    return 0.8
                else:
                    return 0.6
            elif goal == InvestmentGoal.GROWTH:
                if strategy_type in ['random_forest', 'gradient_boosting']:
                    return 0.9
                else:
                    return 0.7
            elif goal == InvestmentGoal.SPECULATION:
                if strategy_type in ['gradient_boosting']:
                    return 0.9
                else:
                    return 0.5
            
            return 0.5
            
        except Exception as e:
            logger.error(f"计算目标匹配度失败: {e}")
            return 0.5
    
    def _estimate_expected_return(self, strategy: Dict[str, Any], allocation: AssetAllocation) -> float:
        """估算预期收益"""
        try:
            # 根据风险等级和策略类型估算收益
            base_return = self.risk_configs[allocation.risk_level]["expected_return"]
            strategy_type = strategy.get('strategy_type', 'unknown')
            
            # 策略类型调整因子
            strategy_adjustments = {
                'ma_cross': 0.8,      # 均线交叉 - 相对保守
                'kdj_macd': 1.0,      # KDJ+MACD - 标准
                'random_forest': 1.1,  # 随机森林 - 略高
                'gradient_boosting': 1.2,  # 梯度提升 - 较高
                'logistic_regression': 0.9  # 逻辑回归 - 略低
            }
            
            adjustment = strategy_adjustments.get(strategy_type, 1.0)
            return base_return * adjustment
            
        except Exception as e:
            logger.error(f"估算预期收益失败: {e}")
            return 0.08
    
    def _generate_recommendation_reasoning(self, strategy: Dict[str, Any], 
                                         profile: UserProfile, allocation: AssetAllocation) -> str:
        """生成推荐理由"""
        try:
            strategy_type = strategy.get('strategy_type', '')
            risk_level = allocation.risk_level.value
            
            reasoning = f"基于您的{risk_level}风险偏好和{profile.investment_goal.value}投资目标，"
            
            if strategy_type == 'ma_cross':
                reasoning += "推荐均线交叉策略，该策略相对稳健，适合风险承受能力较低的投资者。"
            elif strategy_type == 'kdj_macd':
                reasoning += "推荐KDJ+MACD策略，该策略平衡了收益和风险，适合中等风险偏好的投资者。"
            elif strategy_type == 'random_forest':
                reasoning += "推荐随机森林策略，该策略利用机器学习技术，能够捕捉复杂的市场模式。"
            elif strategy_type == 'gradient_boosting':
                reasoning += "推荐梯度提升策略，该策略具有较高的预测准确性，适合追求高收益的投资者。"
            elif strategy_type == 'logistic_regression':
                reasoning += "推荐逻辑回归策略，该策略简单有效，适合初学者投资者。"
            else:
                reasoning += "该策略与您的投资需求匹配度较高。"
            
            reasoning += f"建议投资期限{profile.investment_horizon}年以上。"
            
            return reasoning
            
        except Exception as e:
            logger.error(f"生成推荐理由失败: {e}")
            return "该策略与您的投资需求匹配。"
    
    async def optimize_portfolio(self, user_id: int) -> Optional[Dict[str, Any]]:
        """优化投资组合"""
        try:
            # 获取当前投资组合
            if not enhanced_trading_service:
                return None
            
            portfolio = await enhanced_trading_service.get_portfolio(user_id)
            positions = await enhanced_trading_service.get_positions(user_id)
            allocation = await self.get_asset_allocation(user_id)
            
            if not portfolio or not allocation:
                return None
            
            # 计算当前配置
            current_allocation = {
                "stocks": portfolio.positions_value / portfolio.total_value if portfolio.total_value > 0 else 0,
                "cash": portfolio.cash / portfolio.total_value if portfolio.total_value > 0 else 0,
                "bonds": 0.0,  # 暂时设为0，实际应该从持仓中获取
                "alternatives": 0.0
            }
            
            # 目标配置
            target_allocation = {
                "stocks": allocation.stock_ratio,
                "bonds": allocation.bond_ratio,
                "cash": allocation.cash_ratio,
                "alternatives": allocation.alternative_ratio
            }
            
            # 计算再平衡建议
            rebalance_recommendations = self._calculate_rebalance_recommendations(
                current_allocation, target_allocation, portfolio.total_value
            )
            
            # 估算优化后的表现
            expected_return = self._estimate_portfolio_return(target_allocation)
            expected_risk = self._estimate_portfolio_risk(target_allocation)
            sharpe_ratio = expected_return / expected_risk if expected_risk > 0 else 0
            max_drawdown = expected_risk * 1.5  # 简化估算
            
            # 创建优化记录
            optimization = PortfolioOptimization(
                optimization_id=f"opt_{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                user_id=user_id,
                current_allocation=current_allocation,
                optimized_allocation=target_allocation,
                expected_return=expected_return,
                expected_risk=expected_risk,
                sharpe_ratio=sharpe_ratio,
                max_drawdown=max_drawdown,
                rebalance_recommendations=rebalance_recommendations,
                created_at=datetime.now()
            )
            
            # 保存优化记录
            optimizations_data = self._load_data(self.optimizations_file)
            optimizations_data["optimizations"].append(asdict(optimization))
            self._save_data(self.optimizations_file, optimizations_data)
            
            return asdict(optimization)
            
        except Exception as e:
            logger.error(f"优化投资组合失败: {e}")
            return None
    
    def _calculate_rebalance_recommendations(self, current: Dict[str, float], 
                                           target: Dict[str, float], 
                                           total_value: float) -> List[Dict[str, Any]]:
        """计算再平衡建议"""
        try:
            recommendations = []
            
            for asset_class in current.keys():
                current_ratio = current[asset_class]
                target_ratio = target[asset_class]
                difference = target_ratio - current_ratio
                
                if abs(difference) > 0.05:  # 差异超过5%才建议调整
                    action = "买入" if difference > 0 else "卖出"
                    amount = abs(difference) * total_value
                    
                    recommendations.append({
                        "asset_class": asset_class,
                        "action": action,
                        "current_ratio": current_ratio,
                        "target_ratio": target_ratio,
                        "difference": difference,
                        "amount": amount,
                        "priority": "high" if abs(difference) > 0.1 else "medium"
                    })
            
            # 按优先级排序
            recommendations.sort(key=lambda x: (x['priority'] == 'high', abs(x['difference'])), reverse=True)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"计算再平衡建议失败: {e}")
            return []
    
    def _estimate_portfolio_return(self, allocation: Dict[str, float]) -> float:
        """估算投资组合预期收益"""
        try:
            # 各类资产的预期收益
            asset_returns = {
                "stocks": 0.10,      # 股票预期收益10%
                "bonds": 0.05,       # 债券预期收益5%
                "cash": 0.02,        # 现金预期收益2%
                "alternatives": 0.08  # 另类投资预期收益8%
            }
            
            # 加权平均
            expected_return = sum(allocation[asset] * asset_returns[asset] for asset in allocation.keys())
            
            return expected_return
            
        except Exception as e:
            logger.error(f"估算投资组合收益失败: {e}")
            return 0.08
    
    def _estimate_portfolio_risk(self, allocation: Dict[str, float]) -> float:
        """估算投资组合预期风险"""
        try:
            # 各类资产的风险
            asset_risks = {
                "stocks": 0.15,      # 股票风险15%
                "bonds": 0.05,       # 债券风险5%
                "cash": 0.01,        # 现金风险1%
                "alternatives": 0.12  # 另类投资风险12%
            }
            
            # 简化计算：加权平均（实际应该考虑相关性）
            expected_risk = sum(allocation[asset] * asset_risks[asset] for asset in allocation.keys())
            
            return expected_risk
            
        except Exception as e:
            logger.error(f"估算投资组合风险失败: {e}")
            return 0.10
    
    async def get_user_recommendations(self, user_id: int) -> List[Dict[str, Any]]:
        """获取用户的策略推荐"""
        try:
            recommendations_data = self._load_data(self.recommendations_file)
            user_recommendations = [
                r for r in recommendations_data["recommendations"] 
                if r["user_id"] == user_id
            ]
            
            # 按创建时间排序
            user_recommendations.sort(key=lambda x: x['created_at'], reverse=True)
            
            return user_recommendations
            
        except Exception as e:
            logger.error(f"获取用户推荐失败: {e}")
            return []
    
    async def get_portfolio_optimizations(self, user_id: int) -> List[Dict[str, Any]]:
        """获取用户的投资组合优化记录"""
        try:
            optimizations_data = self._load_data(self.optimizations_file)
            user_optimizations = [
                o for o in optimizations_data["optimizations"] 
                if o["user_id"] == user_id
            ]
            
            # 按创建时间排序
            user_optimizations.sort(key=lambda x: x['created_at'], reverse=True)
            
            return user_optimizations
            
        except Exception as e:
            logger.error(f"获取投资组合优化记录失败: {e}")
            return []

# 创建全局智能投顾实例
robo_advisor = RoboAdvisor()
