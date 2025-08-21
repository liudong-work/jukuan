"""
智能交易助手
为个人投资者提供智能化的投资决策支持
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
    from .market_data_service import market_data_service
    from .ml_strategy_service import ml_strategy_service
    from .robo_advisor import robo_advisor
except ImportError:
    enhanced_trading_service = None
    market_data_service = None
    ml_strategy_service = None
    robo_advisor = None

logger = logging.getLogger(__name__)

class MarketSentiment(Enum):
    """市场情绪枚举"""
    EXTREMELY_BEARISH = "极度悲观"
    BEARISH = "悲观"
    NEUTRAL = "中性"
    BULLISH = "乐观"
    EXTREMELY_BULLISH = "极度乐观"

class TradingSignal(Enum):
    """交易信号枚举"""
    STRONG_BUY = "强烈买入"
    BUY = "买入"
    HOLD = "持有"
    SELL = "卖出"
    STRONG_SELL = "强烈卖出"

@dataclass
class MarketAnalysis:
    """市场分析结果"""
    timestamp: datetime
    market_sentiment: MarketSentiment
    confidence_score: float
    key_factors: List[str]
    risk_level: str
    opportunity_level: str
    summary: str

@dataclass
class StockAnalysis:
    """个股分析结果"""
    stock_code: str
    stock_name: str
    timestamp: datetime
    technical_score: float
    fundamental_score: float
    sentiment_score: float
    overall_score: float
    trading_signal: TradingSignal
    confidence: float
    key_insights: List[str]
    risk_warnings: List[str]
    price_targets: Dict[str, float]

@dataclass
class PortfolioInsight:
    """投资组合洞察"""
    timestamp: datetime
    portfolio_health: str
    diversification_score: float
    risk_score: float
    opportunity_score: float
    rebalancing_needs: List[Dict[str, Any]]
    top_performers: List[str]
    underperformers: List[str]
    recommendations: List[str]

class SmartTradingAssistant:
    """智能交易助手"""
    
    def __init__(self):
        self.analysis_file = "data/smart_assistant_analyses.json"
        self.insights_file = "data/smart_assistant_insights.json"
        
        # 确保数据文件存在
        self._ensure_data_files()
        
        logger.info("智能交易助手已启动")
    
    def _init_data_files(self):
        """初始化数据文件"""
        if not os.path.exists(self.analysis_file):
            self._save_data(self.analysis_file, {"analyses": []})
        if not os.path.exists(self.insights_file):
            self._save_data(self.insights_file, {"insights": []})
    
    def _save_data(self, file_path: str, data: Any):
        """保存数据到文件"""
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
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
    
    def _ensure_data_files(self):
        """确保数据文件存在"""
        try:
            # 确保数据目录存在
            os.makedirs("data", exist_ok=True)
            
            # 初始化分析文件
            if not os.path.exists(self.analysis_file):
                self._save_data(self.analysis_file, {"analyses": []})
            
            # 初始化洞察文件
            if not os.path.exists(self.insights_file):
                self._save_data(self.insights_file, {"insights": []})
                
        except Exception as e:
            logger.error(f"初始化数据文件失败: {e}")
    
    async def get_analysis_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取分析历史"""
        try:
            analyses_data = self._load_data(self.analysis_file)
            if not analyses_data or "analyses" not in analyses_data:
                return []
            
            # 按时间排序并限制数量
            analyses = sorted(analyses_data["analyses"], 
                            key=lambda x: x.get("timestamp", ""), 
                            reverse=True)
            
            return analyses[:limit]
            
        except Exception as e:
            logger.error(f"获取分析历史失败: {e}")
            return []
    
    async def get_insight_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取洞察历史"""
        try:
            insights_data = self._load_data(self.insights_file)
            if not insights_data or "insights" not in insights_data:
                return []
            
            # 按时间排序并限制数量
            insights = sorted(insights_data["insights"], 
                            key=lambda x: x.get("timestamp", ""), 
                            reverse=True)
            
            return insights[:limit]
            
        except Exception as e:
            logger.error(f"获取洞察历史失败: {e}")
            return []
    
    async def clear_old_data(self, days: int = 30):
        """清理旧数据"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # 清理分析数据
            analyses_data = self._load_data(self.analysis_file)
            if analyses_data and "analyses" in analyses_data:
                analyses_data["analyses"] = [
                    a for a in analyses_data["analyses"]
                    if datetime.fromisoformat(a.get("timestamp", "")) > cutoff_date
                ]
                self._save_data(self.analysis_file, analyses_data)
            
            # 清理洞察数据
            insights_data = self._load_data(self.insights_file)
            if insights_data and "insights" in insights_data:
                insights_data["insights"] = [
                    i for i in insights_data["insights"]
                    if datetime.fromisoformat(i.get("timestamp", "")) > cutoff_date
                ]
                self._save_data(self.insights_file, insights_data)
            
            logger.info(f"已清理{days}天前的数据")
            
        except Exception as e:
            logger.error(f"清理旧数据失败: {e}")
    
    async def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        try:
            status = {
                "timestamp": datetime.now().isoformat(),
                "service_status": "running",
                "data_files": {
                    "analysis_file": os.path.exists(self.analysis_file),
                    "insights_file": os.path.exists(self.insights_file)
                },
                "data_counts": {
                    "analyses": 0,
                    "insights": 0
                },
                "last_analysis": None,
                "last_insight": None
            }
            
            # 统计数据量
            analyses_data = self._load_data(self.analysis_file)
            if analyses_data and "analyses" in analyses_data:
                status["data_counts"]["analyses"] = len(analyses_data["analyses"])
                if analyses_data["analyses"]:
                    status["last_analysis"] = analyses_data["analyses"][-1].get("timestamp")
            
            insights_data = self._load_data(self.insights_file)
            if insights_data and "insights" in insights_data:
                status["data_counts"]["insights"] = len(insights_data["insights"])
                if insights_data["insights"]:
                    status["last_insight"] = insights_data["insights"][-1].get("timestamp")
            
            return status
            
        except Exception as e:
            logger.error(f"获取系统状态失败: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "service_status": "error",
                "error": str(e)
            }
    
    async def backup_data(self, backup_dir: str = "backups") -> Dict[str, Any]:
        """备份数据"""
        try:
            import shutil
            from datetime import datetime
            
            # 创建备份目录
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(backup_dir, f"smart_assistant_{timestamp}")
            os.makedirs(backup_path, exist_ok=True)
            
            # 备份数据文件
            if os.path.exists(self.analysis_file):
                shutil.copy2(self.analysis_file, backup_path)
            
            if os.path.exists(self.insights_file):
                shutil.copy2(self.insights_file, backup_path)
            
            return {
                "message": "数据备份成功",
                "backup_path": backup_path,
                "timestamp": timestamp
            }
            
        except Exception as e:
            logger.error(f"数据备份失败: {e}")
            return {"error": f"数据备份失败: {e}"}
    
    async def restore_data(self, backup_path: str) -> Dict[str, Any]:
        """恢复数据"""
        try:
            import shutil
            
            if not os.path.exists(backup_path):
                return {"error": "备份路径不存在"}
            
            # 恢复数据文件
            backup_files = os.listdir(backup_path)
            
            for file_name in backup_files:
                if file_name.endswith('.json'):
                    source_file = os.path.join(backup_path, file_name)
                    if "analysis" in file_name:
                        shutil.copy2(source_file, self.analysis_file)
                    elif "insight" in file_name:
                        shutil.copy2(source_file, self.insights_file)
            
            return {
                "message": "数据恢复成功",
                "restored_files": backup_files
            }
            
        except Exception as e:
            logger.error(f"数据恢复失败: {e}")
            return {"error": f"数据恢复失败: {e}"}
    
    async def analyze_market_sentiment(self) -> MarketAnalysis:
        """分析市场情绪"""
        try:
            # 创建模拟市场分析（后续可以集成真实数据）
            analysis = MarketAnalysis(
                timestamp=datetime.now(),
                market_sentiment=MarketSentiment.NEUTRAL,
                confidence_score=0.6,
                key_factors=["市场波动正常", "成交量适中"],
                risk_level="中",
                opportunity_level="中",
                summary="市场情绪中性，建议观望为主"
            )
            
            # 保存分析结果
            self._save_analysis(analysis)
            
            return analysis
            
        except Exception as e:
            logger.error(f"分析市场情绪失败: {e}")
            return self._create_mock_market_analysis()
    
    def _create_mock_market_analysis(self) -> MarketAnalysis:
        """创建模拟市场分析"""
        return MarketAnalysis(
            timestamp=datetime.now(),
            market_sentiment=MarketSentiment.NEUTRAL,
            confidence_score=0.5,
            key_factors=["数据服务不可用，使用模拟数据"],
            risk_level="中",
            opportunity_level="中",
            summary="市场情绪分析服务暂时不可用"
        )
    
    async def analyze_stock(self, stock_code: str) -> StockAnalysis:
        """分析个股"""
        try:
            # 创建模拟个股分析
            analysis = StockAnalysis(
                stock_code=stock_code,
                stock_name="测试股票",
                timestamp=datetime.now(),
                technical_score=0.3,
                fundamental_score=0.4,
                sentiment_score=0.2,
                overall_score=0.3,
                trading_signal=TradingSignal.HOLD,
                confidence=0.6,
                key_insights=["技术面表现一般", "基本面相对稳健"],
                risk_warnings=["建议谨慎操作"],
                price_targets={"短期目标": 10.5, "支撑位": 9.8, "当前价格": 10.0}
            )
            
            return analysis
            
        except Exception as e:
            logger.error(f"分析个股失败: {e}")
            return self._create_mock_stock_analysis(stock_code)
    
    def _create_mock_stock_analysis(self, stock_code: str) -> StockAnalysis:
        """创建模拟个股分析"""
        return StockAnalysis(
            stock_code=stock_code,
            stock_name="未知",
            timestamp=datetime.now(),
            technical_score=0.0,
            fundamental_score=0.0,
            sentiment_score=0.0,
            overall_score=0.0,
            trading_signal=TradingSignal.HOLD,
            confidence=0.5,
            key_insights=["数据服务不可用，使用模拟数据"],
            risk_warnings=["建议谨慎操作"],
            price_targets={}
        )
    
    async def analyze_portfolio(self) -> PortfolioInsight:
        """分析投资组合"""
        try:
            # 创建模拟投资组合洞察
            insight = PortfolioInsight(
                timestamp=datetime.now(),
                portfolio_health="健康",
                diversification_score=0.7,
                risk_score=0.4,
                opportunity_score=0.6,
                rebalancing_needs=[],
                top_performers=["000001.XSHE"],
                underperformers=[],
                recommendations=["投资组合表现良好，可以继续持有"]
            )
            
            # 保存洞察结果
            self._save_insight(insight)
            
            return insight
            
        except Exception as e:
            logger.error(f"分析投资组合失败: {e}")
            return self._create_mock_portfolio_insight()
    
    def _create_mock_portfolio_insight(self) -> PortfolioInsight:
        """创建模拟投资组合洞察"""
        return PortfolioInsight(
            timestamp=datetime.now(),
            portfolio_health="未知",
            diversification_score=0.5,
            risk_score=0.5,
            opportunity_score=0.5,
            rebalancing_needs=[],
            top_performers=[],
            underperformers=[],
            recommendations=["数据服务不可用，建议检查系统状态"]
        )
    
    def _save_analysis(self, analysis: MarketAnalysis):
        """保存市场分析"""
        try:
            analyses_data = self._load_data(self.analysis_file)
            analyses_data["analyses"].append(asdict(analysis))
            self._save_data(self.analysis_file, analyses_data)
        except Exception as e:
            logger.error(f"保存市场分析失败: {e}")
    
    def _save_insight(self, insight: PortfolioInsight):
        """保存投资组合洞察"""
        try:
            insights_data = self._load_data(self.insights_file)
            insights_data["insights"].append(asdict(insight))
            self._save_data(self.insights_file, insights_data)
        except Exception as e:
            logger.error(f"保存投资组合洞察失败: {e}")
    
    async def get_trading_advice(self, stock_code: str = None) -> Dict[str, Any]:
        """获取交易建议"""
        try:
            advice = {}
            
            # 市场分析
            market_analysis = await self.analyze_market_sentiment()
            advice["market_analysis"] = asdict(market_analysis)
            
            # 个股分析（如果指定了股票代码）
            if stock_code:
                stock_analysis = await self.analyze_stock(stock_code)
                advice["stock_analysis"] = asdict(stock_analysis)
            
            # 投资组合洞察
            portfolio_insight = await self.analyze_portfolio()
            advice["portfolio_insight"] = asdict(portfolio_insight)
            
            # 综合建议
            advice["summary"] = "市场情绪中性，建议观望为主；投资组合表现良好，可以继续持有"
            
            return advice
            
        except Exception as e:
            logger.error(f"获取交易建议失败: {e}")
            return {"error": f"获取交易建议失败: {e}"}

# 创建全局智能交易助手实例
smart_trading_assistant = SmartTradingAssistant()
