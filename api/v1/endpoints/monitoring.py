#!/usr/bin/env python3
"""
实时监控API端点
提供风控监控、性能监控、系统监控等接口
"""

from fastapi import APIRouter, HTTPException, status, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime, timedelta
import json

from services.realtime_monitor import (
    realtime_monitor, 
    RiskMetrics, 
    PerformanceMetrics, 
    Alert
)

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/status")
async def get_monitoring_status():
    """获取监控服务状态"""
    try:
        summary = realtime_monitor.get_monitoring_summary()
        return {
            "status": "success",
            "data": summary
        }
    except Exception as e:
        logger.error(f"获取监控状态失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取监控状态失败: {str(e)}"
        )

@router.post("/start")
async def start_monitoring():
    """启动实时监控"""
    try:
        realtime_monitor.start_monitoring()
        return {
            "status": "success",
            "message": "实时监控已启动",
            "data": {
                "is_running": realtime_monitor.is_running,
                "timestamp": datetime.now().isoformat()
            }
        }
    except Exception as e:
        logger.error(f"启动监控失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"启动监控失败: {str(e)}"
        )

@router.post("/stop")
async def stop_monitoring():
    """停止实时监控"""
    try:
        realtime_monitor.stop_monitoring()
        return {
            "status": "success",
            "message": "实时监控已停止",
            "data": {
                "is_running": realtime_monitor.is_running,
                "timestamp": datetime.now().isoformat()
            }
        }
    except Exception as e:
        logger.error(f"停止监控失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"停止监控失败: {str(e)}"
        )

@router.get("/risk/metrics")
async def get_risk_metrics():
    """获取风险指标"""
    try:
        if not realtime_monitor.is_running:
            # 如果监控未运行，手动计算一次
            portfolio_data = realtime_monitor._get_mock_portfolio_data()
            risk_metrics = realtime_monitor.risk_monitor.calculate_risk_metrics(portfolio_data)
        else:
            # 获取最新的风险指标
            risk_metrics = realtime_monitor.risk_monitor.risk_history[-1] if realtime_monitor.risk_monitor.risk_history else None
        
        if not risk_metrics:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="暂无风险指标数据"
            )
        
        # 转换为可序列化的格式
        metrics_dict = {
            "portfolio_value": risk_metrics.portfolio_value,
            "total_pnl": risk_metrics.total_pnl,
            "daily_pnl": risk_metrics.daily_pnl,
            "max_drawdown": risk_metrics.max_drawdown,
            "sharpe_ratio": risk_metrics.sharpe_ratio,
            "volatility": risk_metrics.volatility,
            "var_95": risk_metrics.var_95,
            "position_concentration": risk_metrics.position_concentration,
            "leverage_ratio": risk_metrics.leverage_ratio,
            "margin_usage": risk_metrics.margin_usage,
            "timestamp": risk_metrics.timestamp.isoformat()
        }
        
        return {
            "status": "success",
            "data": metrics_dict
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取风险指标失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取风险指标失败: {str(e)}"
        )

@router.get("/risk/history")
async def get_risk_history(limit: int = 100):
    """获取风险指标历史"""
    try:
        if not realtime_monitor.risk_monitor.risk_history:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="暂无风险指标历史数据"
            )
        
        # 获取最新的N条记录
        history = list(realtime_monitor.risk_monitor.risk_history)[-limit:]
        
        # 转换为可序列化的格式
        history_data = []
        for metrics in history:
            history_data.append({
                "portfolio_value": metrics.portfolio_value,
                "total_pnl": metrics.total_pnl,
                "daily_pnl": metrics.daily_pnl,
                "max_drawdown": metrics.max_drawdown,
                "sharpe_ratio": metrics.sharpe_ratio,
                "volatility": metrics.volatility,
                "var_95": metrics.var_95,
                "position_concentration": metrics.position_concentration,
                "leverage_ratio": metrics.leverage_ratio,
                "margin_usage": metrics.margin_usage,
                "timestamp": metrics.timestamp.isoformat()
            })
        
        return {
            "status": "success",
            "data": {
                "history": history_data,
                "count": len(history_data),
                "limit": limit
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取风险指标历史失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取风险指标历史失败: {str(e)}"
        )

@router.get("/performance/metrics")
async def get_performance_metrics():
    """获取性能指标"""
    try:
        if not realtime_monitor.is_running:
            # 如果监控未运行，手动计算一次
            strategy_data = realtime_monitor._get_mock_strategy_data()
            performance_metrics = realtime_monitor.performance_monitor.calculate_performance_metrics(strategy_data)
        else:
            # 获取最新的性能指标
            performance_metrics = realtime_monitor.performance_monitor.performance_history[-1] if realtime_monitor.performance_monitor.performance_history else None
        
        if not performance_metrics:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="暂无性能指标数据"
            )
        
        # 转换为可序列化的格式
        metrics_dict = {
            "strategy_count": performance_metrics.strategy_count,
            "active_strategies": performance_metrics.active_strategies,
            "total_trades": performance_metrics.total_trades,
            "win_rate": performance_metrics.win_rate,
            "avg_win": performance_metrics.avg_win,
            "avg_loss": performance_metrics.avg_loss,
            "profit_factor": performance_metrics.profit_factor,
            "max_consecutive_losses": performance_metrics.max_consecutive_losses,
            "current_streak": performance_metrics.current_streak,
            "timestamp": performance_metrics.timestamp.isoformat()
        }
        
        return {
            "status": "success",
            "data": metrics_dict
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取性能指标失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取性能指标失败: {str(e)}"
        )

@router.get("/performance/history")
async def get_performance_history(limit: int = 100):
    """获取性能指标历史"""
    try:
        if not realtime_monitor.performance_monitor.performance_history:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="暂无性能指标历史数据"
            )
        
        # 获取最新的N条记录
        history = list(realtime_monitor.performance_monitor.performance_history)[-limit:]
        
        # 转换为可序列化的格式
        history_data = []
        for metrics in history:
            history_data.append({
                "strategy_count": metrics.strategy_count,
                "active_strategies": metrics.active_strategies,
                "total_trades": metrics.total_trades,
                "win_rate": metrics.win_rate,
                "avg_win": metrics.avg_win,
                "avg_loss": metrics.avg_loss,
                "profit_factor": metrics.profit_factor,
                "max_consecutive_losses": metrics.max_consecutive_losses,
                "current_streak": metrics.current_streak,
                "timestamp": metrics.timestamp.isoformat()
            })
        
        return {
            "status": "success",
            "data": {
                "history": history_data,
                "count": len(history_data),
                "limit": limit
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取性能指标历史失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取性能指标历史失败: {str(e)}"
        )

@router.get("/system/metrics")
async def get_system_metrics():
    """获取系统指标"""
    try:
        system_metrics = realtime_monitor.system_monitor.monitor_system_health()
        
        if not system_metrics:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="暂无系统指标数据"
            )
        
        # 转换为可序列化的格式
        metrics_dict = {}
        for key, value in system_metrics.items():
            if isinstance(value, datetime):
                metrics_dict[key] = value.isoformat()
            else:
                metrics_dict[key] = value
        
        return {
            "status": "success",
            "data": metrics_dict
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取系统指标失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取系统指标失败: {str(e)}"
        )

@router.get("/alerts")
async def get_alerts(
    category: Optional[str] = None,
    level: Optional[str] = None,
    limit: int = 100
):
    """获取告警信息"""
    try:
        alerts = realtime_monitor.get_alerts(category=category, level=level)
        
        if not alerts:
            return {
                "status": "success",
                "data": {
                    "alerts": [],
                    "count": 0,
                    "category": category,
                    "level": level
                }
            }
        
        # 限制返回数量
        alerts = alerts[:limit]
        
        # 转换为可序列化的格式
        alerts_data = []
        for alert in alerts:
            alerts_data.append({
                "level": alert.level,
                "category": alert.category,
                "message": alert.message,
                "details": alert.details,
                "timestamp": alert.timestamp.isoformat(),
                "acknowledged": alert.acknowledged
            })
        
        return {
            "status": "success",
            "data": {
                "alerts": alerts_data,
                "count": len(alerts_data),
                "category": category,
                "level": level,
                "limit": limit
            }
        }
        
    except Exception as e:
        logger.error(f"获取告警信息失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取告警信息失败: {str(e)}"
        )

@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: int):
    """确认告警"""
    try:
        # 获取所有告警
        all_alerts = realtime_monitor.get_alerts()
        
        if alert_id >= len(all_alerts):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="告警不存在"
            )
        
        # 标记告警为已确认
        alert = all_alerts[alert_id]
        alert.acknowledged = True
        
        return {
            "status": "success",
            "message": "告警已确认",
            "data": {
                "alert_id": alert_id,
                "acknowledged": True,
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"确认告警失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"确认告警失败: {str(e)}"
        )

@router.post("/alerts/acknowledge-all")
async def acknowledge_all_alerts():
    """确认所有告警"""
    try:
        # 获取所有告警
        all_alerts = realtime_monitor.get_alerts()
        
        # 标记所有告警为已确认
        for alert in all_alerts:
            alert.acknowledged = True
        
        return {
            "status": "success",
            "message": "所有告警已确认",
            "data": {
                "acknowledged_count": len(all_alerts),
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"确认所有告警失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"确认所有告警失败: {str(e)}"
        )

@router.get("/dashboard")
async def get_monitoring_dashboard():
    """获取监控仪表板数据"""
    try:
        # 获取各项指标
        risk_metrics = None
        performance_metrics = None
        system_metrics = None
        
        try:
            risk_metrics = realtime_monitor.risk_monitor.risk_history[-1] if realtime_monitor.risk_monitor.risk_history else None
        except:
            pass
        
        try:
            performance_metrics = realtime_monitor.performance_monitor.performance_history[-1] if realtime_monitor.performance_monitor.performance_history else None
        except:
            pass
        
        try:
            system_metrics = realtime_monitor.system_monitor.monitor_system_health()
        except:
            pass
        
        # 获取告警统计
        alerts = realtime_monitor.get_alerts()
        alert_stats = {
            "total": len(alerts),
            "critical": len([a for a in alerts if a.level == "CRITICAL"]),
            "error": len([a for a in alerts if a.level == "ERROR"]),
            "warning": len([a for a in alerts if a.level == "WARNING"]),
            "info": len([a for a in alerts if a.level == "INFO"])
        }
        
        # 构建仪表板数据
        dashboard_data = {
            "monitoring_status": realtime_monitor.get_monitoring_summary(),
                    "risk_metrics": asdict(risk_metrics) if risk_metrics else None,
        "performance_metrics": asdict(performance_metrics) if performance_metrics else None,
            "system_metrics": system_metrics,
            "alert_stats": alert_stats,
            "recent_alerts": [asdict(a) for a in alerts[:5]] if alerts else [],
            "timestamp": datetime.now().isoformat()
        }
        
        # 处理datetime序列化
        for key, value in dashboard_data.items():
            if isinstance(value, dict):
                for k, v in value.items():
                    if isinstance(v, datetime):
                        value[k] = v.isoformat()
        
        return {
            "status": "success",
            "data": dashboard_data
        }
        
    except Exception as e:
        logger.error(f"获取监控仪表板失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取监控仪表板失败: {str(e)}"
        )

@router.post("/config/update")
async def update_monitoring_config(config: Dict[str, Any]):
    """更新监控配置"""
    try:
        # 更新风险监控配置
        if 'risk' in config:
            realtime_monitor.risk_monitor.config.update(config['risk'])
        
        # 更新性能监控配置
        if 'performance' in config:
            realtime_monitor.performance_monitor.config.update(config['performance'])
        
        # 更新主监控配置
        if 'monitoring' in config:
            realtime_monitor.config.update(config['monitoring'])
        
        return {
            "status": "success",
            "message": "监控配置已更新",
            "data": {
                "risk_config": realtime_monitor.risk_monitor.config,
                "performance_config": realtime_monitor.performance_monitor.config,
                "monitoring_config": realtime_monitor.config,
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"更新监控配置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新监控配置失败: {str(e)}"
        )

@router.get("/config")
async def get_monitoring_config():
    """获取监控配置"""
    try:
        config = {
            "risk": realtime_monitor.risk_monitor.config,
            "performance": realtime_monitor.performance_monitor.config,
            "monitoring": realtime_monitor.config
        }
        
        return {
            "status": "success",
            "data": config
        }
        
    except Exception as e:
        logger.error(f"获取监控配置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取监控配置失败: {str(e)}"
        )
