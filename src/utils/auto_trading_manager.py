#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
自动交易管理模块
用于Web界面集成自动交易功能
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime
import threading

class AutoTradingManager:
    """自动交易管理器"""
    
    def __init__(self):
        """初始化自动交易管理器"""
        self.logger = logging.getLogger(__name__)
        
        # 自动交易器实例
        self.auto_trader = None
        self.strategy_manager = None
        self.risk_manager = None
        
        # 状态管理
        self.is_initialized = False
        self.last_update = datetime.now()
        
        # 线程锁
        self._lock = threading.Lock()
        
    def initialize(self, data_provider):
        """初始化自动交易系统"""
        try:
            with self._lock:
                if self.is_initialized:
                    return True
                    
                # 导入模块
                from src.trading.auto_trader import AutoTrader
                from src.trading.strategy_manager import StrategyManager
                from src.trading.risk_manager import RiskManager
                
                # 创建组件
                self.strategy_manager = StrategyManager(data_provider)
                self.risk_manager = RiskManager()
                self.auto_trader = AutoTrader(data_provider, self.strategy_manager, self.risk_manager)
                
                self.is_initialized = True
                self.last_update = datetime.now()
                
                self.logger.info("自动交易系统初始化成功")
                return True
                
        except Exception as e:
            self.logger.error(f"自动交易系统初始化失败: {e}")
            return False
            
    def start_trading(self) -> Dict:
        """启动自动交易"""
        try:
            if not self.is_initialized:
                return {'success': False, 'message': '自动交易系统未初始化'}
                
            with self._lock:
                if self.auto_trader.is_running:
                    return {'success': False, 'message': '自动交易已在运行中'}
                    
                self.auto_trader.start_trading()
                self.last_update = datetime.now()
                
                return {'success': True, 'message': '自动交易已启动'}
                
        except Exception as e:
            self.logger.error(f"启动自动交易失败: {e}")
            return {'success': False, 'message': f'启动失败: {str(e)}'}
            
    def stop_trading(self) -> Dict:
        """停止自动交易"""
        try:
            if not self.is_initialized:
                return {'success': False, 'message': '自动交易系统未初始化'}
                
            with self._lock:
                if not self.auto_trader.is_running:
                    return {'success': False, 'message': '自动交易未在运行'}
                    
                self.auto_trader.stop_trading()
                self.last_update = datetime.now()
                
                return {'success': True, 'message': '自动交易已停止'}
                
        except Exception as e:
            self.logger.error(f"停止自动交易失败: {e}")
            return {'success': False, 'message': f'停止失败: {str(e)}'}
            
    def get_trading_status(self) -> Dict:
        """获取交易状态"""
        try:
            if not self.is_initialized:
                return {
                    'is_initialized': False,
                    'is_running': False,
                    'message': '系统未初始化'
                }
                
            with self._lock:
                status = self.auto_trader.get_trading_status()
                status['is_initialized'] = True
                status['last_update'] = self.last_update.strftime('%Y-%m-%d %H:%M:%S')
                
                return status
                
        except Exception as e:
            self.logger.error(f"获取交易状态失败: {e}")
            return {
                'is_initialized': False,
                'is_running': False,
                'message': f'获取状态失败: {str(e)}'
            }
            
    def get_orders(self) -> List[Dict]:
        """获取订单列表"""
        try:
            if not self.is_initialized:
                return []
                
            with self._lock:
                return self.auto_trader.get_orders()
                
        except Exception as e:
            self.logger.error(f"获取订单列表失败: {e}")
            return []
            
    def get_positions(self) -> Dict:
        """获取持仓信息"""
        try:
            if not self.is_initialized:
                return {}
                
            with self._lock:
                return self.auto_trader.get_positions()
                
        except Exception as e:
            self.logger.error(f"获取持仓信息失败: {e}")
            return {}
            
    def get_risk_summary(self) -> Dict:
        """获取风险摘要"""
        try:
            if not self.is_initialized:
                return {}
                
            with self._lock:
                return self.risk_manager.get_risk_summary()
                
        except Exception as e:
            self.logger.error(f"获取风险摘要失败: {e}")
            return {}
            
    def update_config(self, config: Dict) -> Dict:
        """更新配置"""
        try:
            if not self.is_initialized:
                return {'success': False, 'message': '系统未初始化'}
                
            with self._lock:
                # 更新自动交易器配置
                self.auto_trader.config.update(config)
                
                # 更新风险管理器配置
                if 'risk_config' in config:
                    self.risk_manager.set_risk_config(config['risk_config'])
                    
                self.last_update = datetime.now()
                
                return {'success': True, 'message': '配置更新成功'}
                
        except Exception as e:
            self.logger.error(f"更新配置失败: {e}")
            return {'success': False, 'message': f'更新失败: {str(e)}'}
            
    def emergency_stop(self) -> Dict:
        """紧急停止"""
        try:
            if not self.is_initialized:
                return {'success': False, 'message': '系统未初始化'}
                
            with self._lock:
                # 停止自动交易
                if self.auto_trader.is_running:
                    self.auto_trader.stop_trading()
                    
                # 触发紧急停止
                self.risk_manager.emergency_stop()
                
                self.last_update = datetime.now()
                
                return {'success': True, 'message': '紧急停止已执行'}
                
        except Exception as e:
            self.logger.error(f"紧急停止失败: {e}")
            return {'success': False, 'message': f'紧急停止失败: {str(e)}'}
            
    def get_system_info(self) -> Dict:
        """获取系统信息"""
        return {
            'is_initialized': self.is_initialized,
            'last_update': self.last_update.strftime('%Y-%m-%d %H:%M:%S'),
            'version': '1.0.0',
            'features': [
                '自动策略执行',
                '实时风险监控',
                '自动止损止盈',
                '多策略支持',
                '模拟交易模式'
            ]
        }
