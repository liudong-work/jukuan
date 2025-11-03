#!/usr/bin/env python3
"""
实时监控服务
提供风控监控、性能监控、异常告警等核心功能
"""

import asyncio
import threading
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
import json
import queue
from collections import deque, defaultdict
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

@dataclass
class RiskMetrics:
    """风险指标"""
    portfolio_value: float
    total_pnl: float
    daily_pnl: float
    max_drawdown: float
    sharpe_ratio: float
    volatility: float
    var_95: float  # 95%置信度下的VaR
    position_concentration: float
    leverage_ratio: float
    margin_usage: float
    timestamp: datetime

@dataclass
class PerformanceMetrics:
    """性能指标"""
    strategy_count: int
    active_strategies: int
    total_trades: int
    win_rate: float
    avg_win: float
    avg_loss: float
    profit_factor: float
    max_consecutive_losses: int
    current_streak: int
    timestamp: datetime

@dataclass
class Alert:
    """告警信息"""
    level: str  # INFO, WARNING, ERROR, CRITICAL
    category: str  # RISK, PERFORMANCE, SYSTEM, TRADING
    message: str
    details: Dict[str, Any]
    timestamp: datetime
    acknowledged: bool = False

class RiskMonitor:
    """风险监控器"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """初始化风险监控器"""
        self.config = config or {
            'max_drawdown_threshold': 0.15,      # 最大回撤阈值 15%
            'var_threshold': 0.05,               # VaR阈值 5%
            'position_concentration_limit': 0.3,  # 单一持仓集中度限制 30%
            'leverage_limit': 2.0,               # 杠杆限制 2倍
            'margin_usage_limit': 0.8,           # 保证金使用率限制 80%
            'daily_loss_limit': 0.1,             # 日亏损限制 10%
        }
        
        self.risk_history = deque(maxlen=1000)
        self.alerts = []
        self.risk_callbacks = []
        
        logger.info("风险监控器初始化完成")
    
    def add_risk_callback(self, callback: Callable[[RiskMetrics, List[Alert]], None]):
        """添加风险回调函数"""
        self.risk_callbacks.append(callback)
    
    def calculate_risk_metrics(self, portfolio_data: Dict[str, Any]) -> RiskMetrics:
        """计算风险指标"""
        try:
            portfolio_value = portfolio_data.get('total_value', 0)
            positions = portfolio_data.get('positions', {})
            trades = portfolio_data.get('trades', [])
            
            # 计算基础指标
            total_pnl = portfolio_data.get('total_pnl', 0)
            daily_pnl = portfolio_data.get('daily_pnl', 0)
            
            # 计算最大回撤
            max_drawdown = self._calculate_max_drawdown(portfolio_data.get('equity_curve', []))
            
            # 计算夏普比率
            sharpe_ratio = self._calculate_sharpe_ratio(portfolio_data.get('returns', []))
            
            # 计算波动率
            volatility = self._calculate_volatility(portfolio_data.get('returns', []))
            
            # 计算VaR
            var_95 = self._calculate_var(portfolio_data.get('returns', []), 0.95)
            
            # 计算持仓集中度
            position_concentration = self._calculate_position_concentration(positions, portfolio_value)
            
            # 计算杠杆比率
            leverage_ratio = self._calculate_leverage_ratio(positions, portfolio_value)
            
            # 计算保证金使用率
            margin_usage = self._calculate_margin_usage(portfolio_data)
            
            metrics = RiskMetrics(
                portfolio_value=portfolio_value,
                total_pnl=total_pnl,
                daily_pnl=daily_pnl,
                max_drawdown=max_drawdown,
                sharpe_ratio=sharpe_ratio,
                volatility=volatility,
                var_95=var_95,
                position_concentration=position_concentration,
                leverage_ratio=leverage_ratio,
                margin_usage=margin_usage,
                timestamp=datetime.now()
            )
            
            # 保存历史数据
            self.risk_history.append(metrics)
            
            # 检查风险阈值
            self._check_risk_thresholds(metrics)
            
            return metrics
            
        except Exception as e:
            logger.error(f"计算风险指标失败: {e}")
            return None
    
    def _calculate_max_drawdown(self, equity_curve: List[float]) -> float:
        """计算最大回撤"""
        if not equity_curve or len(equity_curve) < 2:
            return 0.0
        
        peak = equity_curve[0]
        max_dd = 0.0
        
        for value in equity_curve:
            if value > peak:
                peak = value
            dd = (peak - value) / peak
            max_dd = max(max_dd, dd)
        
        return max_dd
    
    def _calculate_sharpe_ratio(self, returns: List[float]) -> float:
        """计算夏普比率"""
        if not returns or len(returns) < 2:
            return 0.0
        
        returns_array = np.array(returns)
        mean_return = np.mean(returns_array)
        std_return = np.std(returns_array)
        
        if std_return == 0:
            return 0.0
        
        # 假设无风险利率为0
        sharpe = mean_return / std_return * np.sqrt(252)  # 年化
        return sharpe
    
    def _calculate_volatility(self, returns: List[float]) -> float:
        """计算波动率"""
        if not returns or len(returns) < 2:
            return 0.0
        
        returns_array = np.array(returns)
        std_return = np.std(returns_array)
        volatility = std_return * np.sqrt(252)  # 年化
        return volatility
    
    def _calculate_var(self, returns: List[float], confidence: float) -> float:
        """计算VaR"""
        if not returns or len(returns) < 2:
            return 0.0
        
        returns_array = np.array(returns)
        var = np.percentile(returns_array, (1 - confidence) * 100)
        return abs(var)
    
    def _calculate_position_concentration(self, positions: Dict, portfolio_value: float) -> float:
        """计算持仓集中度"""
        if not positions or portfolio_value == 0:
            return 0.0
        
        max_position_value = max([pos.get('market_value', 0) for pos in positions.values()])
        concentration = max_position_value / portfolio_value
        return concentration
    
    def _calculate_leverage_ratio(self, positions: Dict, portfolio_value: float) -> float:
        """计算杠杆比率"""
        if not positions or portfolio_value == 0:
            return 1.0
        
        total_position_value = sum([pos.get('market_value', 0) for pos in positions.values()])
        leverage = total_position_value / portfolio_value
        return leverage
    
    def _calculate_margin_usage(self, portfolio_data: Dict) -> float:
        """计算保证金使用率"""
        margin_used = portfolio_data.get('margin_used', 0)
        margin_available = portfolio_data.get('margin_available', 1)
        
        if margin_available == 0:
            return 0.0
        
        usage = margin_used / margin_available
        return usage
    
    def _check_risk_thresholds(self, metrics: RiskMetrics):
        """检查风险阈值"""
        alerts = []
        
        # 检查最大回撤
        if metrics.max_drawdown > self.config['max_drawdown_threshold']:
            alerts.append(Alert(
                level='WARNING',
                category='RISK',
                message=f"最大回撤超过阈值: {metrics.max_drawdown:.2%} > {self.config['max_drawdown_threshold']:.2%}",
                details={'max_drawdown': metrics.max_drawdown, 'threshold': self.config['max_drawdown_threshold']},
                timestamp=datetime.now()
            ))
        
        # 检查VaR
        if metrics.var_95 > self.config['var_threshold']:
            alerts.append(Alert(
                level='WARNING',
                category='RISK',
                message=f"VaR超过阈值: {metrics.var_95:.2%} > {self.config['var_threshold']:.2%}",
                details={'var_95': metrics.var_95, 'threshold': self.config['var_threshold']},
                timestamp=datetime.now()
            ))
        
        # 检查持仓集中度
        if metrics.position_concentration > self.config['position_concentration_limit']:
            alerts.append(Alert(
                level='WARNING',
                category='RISK',
                message=f"持仓集中度过高: {metrics.position_concentration:.2%} > {self.config['position_concentration_limit']:.2%}",
                details={'concentration': metrics.position_concentration, 'limit': self.config['position_concentration_limit']},
                timestamp=datetime.now()
            ))
        
        # 检查杠杆比率
        if metrics.leverage_ratio > self.config['leverage_limit']:
            alerts.append(Alert(
                level='ERROR',
                category='RISK',
                message=f"杠杆比率过高: {metrics.leverage_ratio:.2f}x > {self.config['leverage_limit']:.2f}x",
                details={'leverage': metrics.leverage_ratio, 'limit': self.config['leverage_limit']},
                timestamp=datetime.now()
            ))
        
        # 检查保证金使用率
        if metrics.margin_usage > self.config['margin_usage_limit']:
            alerts.append(Alert(
                level='ERROR',
                category='RISK',
                message=f"保证金使用率过高: {metrics.margin_usage:.2%} > {self.config['margin_usage_limit']:.2%}",
                details={'margin_usage': metrics.margin_usage, 'limit': self.config['margin_usage_limit']},
                timestamp=datetime.now()
            ))
        
        # 检查日亏损
        if metrics.daily_pnl < -self.config['daily_loss_limit'] * metrics.portfolio_value:
            alerts.append(Alert(
                level='CRITICAL',
                category='RISK',
                message=f"日亏损超过限制: {metrics.daily_pnl:.2f} < -{self.config['daily_loss_limit']:.2%} * {metrics.portfolio_value:.2f}",
                details={'daily_pnl': metrics.daily_pnl, 'limit': -self.config['daily_loss_limit'] * metrics.portfolio_value},
                timestamp=datetime.now()
            ))
        
        # 添加告警
        for alert in alerts:
            self.alerts.append(alert)
            logger.warning(f"风险告警: {alert.message}")
        
        # 触发回调
        if alerts and self.risk_callbacks:
            for callback in self.risk_callbacks:
                try:
                    callback(metrics, alerts)
                except Exception as e:
                    logger.error(f"风险回调执行失败: {e}")

class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """初始化性能监控器"""
        self.config = config or {
            'min_win_rate': 0.4,           # 最低胜率 40%
            'max_consecutive_losses': 10,   # 最大连续亏损次数
            'min_profit_factor': 1.2,       # 最低盈亏比 1.2
        }
        
        self.performance_history = deque(maxlen=1000)
        self.alerts = []
        self.performance_callbacks = []
        
        logger.info("性能监控器初始化完成")
    
    def add_performance_callback(self, callback: Callable[[PerformanceMetrics, List[Alert]], None]):
        """添加性能回调函数"""
        self.performance_callbacks.append(callback)
    
    def calculate_performance_metrics(self, strategy_data: Dict[str, Any]) -> PerformanceMetrics:
        """计算性能指标"""
        try:
            strategies = strategy_data.get('strategies', {})
            trades = strategy_data.get('trades', [])
            
            # 基础统计
            strategy_count = len(strategies)
            active_strategies = len([s for s in strategies.values() if s.get('is_active', False)])
            total_trades = len(trades)
            
            if total_trades == 0:
                return PerformanceMetrics(
                    strategy_count=strategy_count,
                    active_strategies=active_strategies,
                    total_trades=total_trades,
                    win_rate=0.0,
                    avg_win=0.0,
                    avg_loss=0.0,
                    profit_factor=0.0,
                    max_consecutive_losses=0,
                    current_streak=0,
                    timestamp=datetime.now()
                )
            
            # 计算交易统计
            winning_trades = [t for t in trades if t.get('pnl', 0) > 0]
            losing_trades = [t for t in trades if t.get('pnl', 0) < 0]
            
            win_rate = len(winning_trades) / total_trades
            avg_win = np.mean([t.get('pnl', 0) for t in winning_trades]) if winning_trades else 0
            avg_loss = abs(np.mean([t.get('pnl', 0) for t in losing_trades])) if losing_trades else 0
            
            # 计算盈亏比
            total_wins = sum([t.get('pnl', 0) for t in winning_trades])
            total_losses = abs(sum([t.get('pnl', 0) for t in losing_trades]))
            profit_factor = total_wins / total_losses if total_losses > 0 else float('inf')
            
            # 计算连续亏损
            max_consecutive_losses, current_streak = self._calculate_consecutive_losses(trades)
            
            metrics = PerformanceMetrics(
                strategy_count=strategy_count,
                active_strategies=active_strategies,
                total_trades=total_trades,
                win_rate=win_rate,
                avg_win=avg_win,
                avg_loss=avg_loss,
                profit_factor=profit_factor,
                max_consecutive_losses=max_consecutive_losses,
                current_streak=current_streak,
                timestamp=datetime.now()
            )
            
            # 保存历史数据
            self.performance_history.append(metrics)
            
            # 检查性能阈值
            self._check_performance_thresholds(metrics)
            
            return metrics
            
        except Exception as e:
            logger.error(f"计算性能指标失败: {e}")
            return None
    
    def _calculate_consecutive_losses(self, trades: List[Dict]) -> tuple:
        """计算连续亏损次数"""
        if not trades:
            return 0, 0
        
        max_consecutive = 0
        current_consecutive = 0
        
        for trade in trades:
            pnl = trade.get('pnl', 0)
            if pnl < 0:
                current_consecutive += 1
                max_consecutive = max(max_consecutive, current_consecutive)
            else:
                current_consecutive = 0
        
        return max_consecutive, current_consecutive
    
    def _check_performance_thresholds(self, metrics: PerformanceMetrics):
        """检查性能阈值"""
        alerts = []
        
        # 检查胜率
        if metrics.win_rate < self.config['min_win_rate']:
            alerts.append(Alert(
                level='WARNING',
                category='PERFORMANCE',
                message=f"胜率过低: {metrics.win_rate:.2%} < {self.config['min_win_rate']:.2%}",
                details={'win_rate': metrics.win_rate, 'threshold': self.config['min_win_rate']},
                timestamp=datetime.now()
            ))
        
        # 检查连续亏损
        if metrics.max_consecutive_losses > self.config['max_consecutive_losses']:
            alerts.append(Alert(
                level='WARNING',
                category='PERFORMANCE',
                message=f"连续亏损次数过多: {metrics.max_consecutive_losses} > {self.config['max_consecutive_losses']}",
                details={'consecutive_losses': metrics.max_consecutive_losses, 'limit': self.config['max_consecutive_losses']},
                timestamp=datetime.now()
            ))
        
        # 检查盈亏比
        if metrics.profit_factor < self.config['min_profit_factor']:
            alerts.append(Alert(
                level='WARNING',
                category='PERFORMANCE',
                message=f"盈亏比过低: {metrics.profit_factor:.2f} < {self.config['min_profit_factor']:.2f}",
                details={'profit_factor': metrics.profit_factor, 'threshold': self.config['min_profit_factor']},
                timestamp=datetime.now()
            ))
        
        # 添加告警
        for alert in alerts:
            self.alerts.append(alert)
            logger.warning(f"性能告警: {alert.message}")
        
        # 触发回调
        if alerts and self.performance_callbacks:
            for callback in self.performance_callbacks:
                try:
                    callback(metrics, alerts)
                except Exception as e:
                    logger.error(f"性能回调执行失败: {e}")

class SystemMonitor:
    """系统监控器"""
    
    def __init__(self):
        """初始化系统监控器"""
        self.system_metrics = {}
        self.alerts = []
        self.system_callbacks = []
        
        logger.info("系统监控器初始化完成")
    
    def add_system_callback(self, callback: Callable[[Dict[str, Any], List[Alert]], None]):
        """添加系统回调函数"""
        self.system_callbacks.append(callback)
    
    def monitor_system_health(self) -> Dict[str, Any]:
        """监控系统健康状态"""
        try:
            import psutil
            
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # 内存使用率
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # 磁盘使用率
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            
            # 网络状态
            network = psutil.net_io_counters()
            
            # 进程状态
            process = psutil.Process()
            process_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            metrics = {
                'cpu_percent': cpu_percent,
                'memory_percent': memory_percent,
                'memory_available': memory.available / 1024 / 1024 / 1024,  # GB
                'disk_percent': disk_percent,
                'disk_free': disk.free / 1024 / 1024 / 1024,  # GB
                'network_bytes_sent': network.bytes_sent,
                'network_bytes_recv': network.bytes_recv,
                'process_memory_mb': process_memory,
                'timestamp': datetime.now()
            }
            
            self.system_metrics = metrics
            
            # 检查系统阈值
            self._check_system_thresholds(metrics)
            
            return metrics
            
        except ImportError:
            logger.warning("psutil未安装，无法监控系统状态")
            return {}
        except Exception as e:
            logger.error(f"系统监控失败: {e}")
            return {}
    
    def _check_system_thresholds(self, metrics: Dict[str, Any]):
        """检查系统阈值"""
        alerts = []
        
        # 检查CPU使用率
        if metrics.get('cpu_percent', 0) > 80:
            alerts.append(Alert(
                level='WARNING',
                category='SYSTEM',
                message=f"CPU使用率过高: {metrics['cpu_percent']:.1f}%",
                details={'cpu_percent': metrics['cpu_percent']},
                timestamp=datetime.now()
            ))
        
        # 检查内存使用率
        if metrics.get('memory_percent', 0) > 90:
            alerts.append(Alert(
                level='WARNING',
                category='SYSTEM',
                message=f"内存使用率过高: {metrics['memory_percent']:.1f}%",
                details={'memory_percent': metrics['memory_percent']},
                timestamp=datetime.now()
            ))
        
        # 检查磁盘使用率
        if metrics.get('disk_percent', 0) > 90:
            alerts.append(Alert(
                level='WARNING',
                category='SYSTEM',
                message=f"磁盘使用率过高: {metrics['disk_percent']:.1f}%",
                details={'disk_percent': metrics['disk_percent']},
                timestamp=datetime.now()
            ))
        
        # 添加告警
        for alert in alerts:
            self.alerts.append(alert)
            logger.warning(f"系统告警: {alert.message}")
        
        # 触发回调
        if alerts and self.system_callbacks:
            for callback in self.system_callbacks:
                try:
                    callback(metrics, alerts)
                except Exception as e:
                    logger.error(f"系统回调执行失败: {e}")

class RealtimeMonitor:
    """实时监控主服务"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """初始化实时监控服务"""
        self.config = config or {
            'monitoring_interval': 5,      # 监控间隔（秒）
            'alert_retention_hours': 24,   # 告警保留时间（小时）
            'max_alerts': 1000,            # 最大告警数量
        }
        
        # 初始化各个监控器
        self.risk_monitor = RiskMonitor(config.get('risk', {}) if config else {})
        self.performance_monitor = PerformanceMonitor(config.get('performance', {}) if config else {})
        self.system_monitor = SystemMonitor()
        
        # 监控状态
        self.is_running = False
        self.monitoring_thread = None
        self.stop_event = threading.Event()
        
        # 数据队列
        self.data_queue = queue.Queue()
        
        # 回调函数
        self.monitoring_callbacks = []
        
        logger.info("实时监控服务初始化完成")
    
    def add_monitoring_callback(self, callback: Callable[[Dict[str, Any], List[Alert]], None]):
        """添加监控回调函数"""
        self.monitoring_callbacks.append(callback)
    
    def start_monitoring(self):
        """启动监控"""
        if self.is_running:
            logger.warning("监控服务已在运行")
            return
        
        self.is_running = True
        self.stop_event.clear()
        
        # 启动监控线程
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop)
        self.monitoring_thread.daemon = True
        self.monitoring_thread.start()
        
        logger.info("实时监控服务已启动")
    
    def stop_monitoring(self):
        """停止监控"""
        if not self.is_running:
            return
        
        self.is_running = False
        self.stop_event.set()
        
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        
        logger.info("实时监控服务已停止")
    
    def _monitoring_loop(self):
        """监控主循环"""
        while not self.stop_event.is_set():
            try:
                # 获取监控数据
                monitoring_data = self._collect_monitoring_data()
                
                # 执行监控检查
                self._execute_monitoring_checks(monitoring_data)
                
                # 触发回调
                self._trigger_callbacks(monitoring_data)
                
                # 清理过期告警
                self._cleanup_expired_alerts()
                
                # 等待下次监控
                self.stop_event.wait(self.config['monitoring_interval'])
                
            except Exception as e:
                logger.error(f"监控循环异常: {e}")
                time.sleep(1)
    
    def _collect_monitoring_data(self) -> Dict[str, Any]:
        """收集监控数据"""
        try:
            # 这里应该从实际的数据源获取数据
            # 目前使用模拟数据
            portfolio_data = self._get_mock_portfolio_data()
            strategy_data = self._get_mock_strategy_data()
            
            # 计算各项指标
            risk_metrics = self.risk_monitor.calculate_risk_metrics(portfolio_data)
            performance_metrics = self.performance_monitor.calculate_performance_metrics(strategy_data)
            system_metrics = self.system_monitor.monitor_system_health()
            
            monitoring_data = {
                'risk_metrics': risk_metrics,
                'performance_metrics': performance_metrics,
                'system_metrics': system_metrics,
                'portfolio_data': portfolio_data,
                'strategy_data': strategy_data,
                'timestamp': datetime.now()
            }
            
            return monitoring_data
            
        except Exception as e:
            logger.error(f"收集监控数据失败: {e}")
            return {}
    
    def _execute_monitoring_checks(self, monitoring_data: Dict[str, Any]):
        """执行监控检查"""
        # 风险监控检查已在RiskMonitor中执行
        # 性能监控检查已在PerformanceMonitor中执行
        # 系统监控检查已在SystemMonitor中执行
        pass
    
    def _trigger_callbacks(self, monitoring_data: Dict[str, Any]):
        """触发监控回调"""
        # 收集所有告警
        all_alerts = []
        all_alerts.extend(self.risk_monitor.alerts)
        all_alerts.extend(self.performance_monitor.alerts)
        all_alerts.extend(self.system_monitor.alerts)
        
        # 触发回调
        for callback in self.monitoring_callbacks:
            try:
                callback(monitoring_data, all_alerts)
            except Exception as e:
                logger.error(f"监控回调执行失败: {e}")
    
    def _cleanup_expired_alerts(self):
        """清理过期告警"""
        cutoff_time = datetime.now() - timedelta(hours=self.config['alert_retention_hours'])
        
        # 清理风险告警
        self.risk_monitor.alerts = [
            alert for alert in self.risk_monitor.alerts 
            if alert.timestamp > cutoff_time
        ]
        
        # 清理性能告警
        self.performance_monitor.alerts = [
            alert for alert in self.performance_monitor.alerts 
            if alert.timestamp > cutoff_time
        ]
        
        # 清理系统告警
        self.system_monitor.alerts = [
            alert for alert in self.system_monitor.alerts 
            if alert.timestamp > cutoff_time
        ]
        
        # 限制告警数量
        if len(self.risk_monitor.alerts) > self.config['max_alerts']:
            self.risk_monitor.alerts = self.risk_monitor.alerts[-self.config['max_alerts']:]
        
        if len(self.performance_monitor.alerts) > self.config['max_alerts']:
            self.performance_monitor.alerts = self.performance_monitor.alerts[-self.config['max_alerts']:]
        
        if len(self.system_monitor.alerts) > self.config['max_alerts']:
            self.system_monitor.alerts = self.system_monitor.alerts[-self.config['max_alerts']:]
    
    def _get_mock_portfolio_data(self) -> Dict[str, Any]:
        """获取模拟投资组合数据"""
        return {
            'total_value': 1000000,
            'total_pnl': 50000,
            'daily_pnl': 2000,
            'equity_curve': [950000, 960000, 970000, 980000, 990000, 1000000, 1005000],
            'returns': [0.01, 0.01, 0.01, 0.01, 0.01, 0.005],
            'positions': {
                '000001': {'market_value': 200000, 'pnl': 10000},
                '000002': {'market_value': 150000, 'pnl': 5000},
                '600036': {'market_value': 100000, 'pnl': -2000}
            },
            'trades': [
                {'timestamp': datetime.now(), 'pnl': 1000},
                {'timestamp': datetime.now(), 'pnl': -500},
                {'timestamp': datetime.now(), 'pnl': 800}
            ],
            'margin_used': 200000,
            'margin_available': 1000000
        }
    
    def _get_mock_strategy_data(self) -> Dict[str, Any]:
        """获取模拟策略数据"""
        return {
            'strategies': {
                'strategy_1': {'is_active': True, 'performance': 0.15},
                'strategy_2': {'is_active': True, 'performance': 0.08},
                'strategy_3': {'is_active': False, 'performance': -0.05}
            },
            'trades': [
                {'timestamp': datetime.now(), 'pnl': 1000, 'strategy': 'strategy_1'},
                {'timestamp': datetime.now(), 'pnl': -500, 'strategy': 'strategy_2'},
                {'timestamp': datetime.now(), 'pnl': 800, 'strategy': 'strategy_1'},
                {'timestamp': datetime.now(), 'pnl': 1200, 'strategy': 'strategy_2'},
                {'timestamp': datetime.now(), 'pnl': -300, 'strategy': 'strategy_1'}
            ]
        }
    
    def get_monitoring_summary(self) -> Dict[str, Any]:
        """获取监控摘要"""
        return {
            'is_running': self.is_running,
            'risk_alerts_count': len(self.risk_monitor.alerts),
            'performance_alerts_count': len(self.performance_monitor.alerts),
            'system_alerts_count': len(self.system_monitor.alerts),
            'total_alerts_count': len(self.risk_monitor.alerts) + len(self.performance_monitor.alerts) + len(self.system_monitor.alerts),
            'last_update': datetime.now().isoformat()
        }
    
    def get_alerts(self, category: str = None, level: str = None) -> List[Alert]:
        """获取告警信息"""
        all_alerts = []
        all_alerts.extend(self.risk_monitor.alerts)
        all_alerts.extend(self.performance_monitor.alerts)
        all_alerts.extend(self.system_monitor.alerts)
        
        # 按类别过滤
        if category:
            all_alerts = [alert for alert in all_alerts if alert.category == category]
        
        # 按级别过滤
        if level:
            all_alerts = [alert for alert in all_alerts if alert.level == level]
        
        # 按时间排序
        all_alerts.sort(key=lambda x: x.timestamp, reverse=True)
        
        return all_alerts

# 全局监控服务实例
realtime_monitor = RealtimeMonitor()

def cleanup_realtime_monitor():
    """清理实时监控服务"""
    if realtime_monitor:
        realtime_monitor.stop_monitoring()

# 注册清理函数
import atexit
atexit.register(cleanup_realtime_monitor)
