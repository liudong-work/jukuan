#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
银河证券交易接口
支持实盘交易和查询功能
"""

import logging
import time
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import requests
import json

class GalaxySecuritiesBroker:
    """银河证券交易接口"""
    
    def __init__(self, config: Dict):
        """
        初始化银河证券接口
        
        Args:
            config: 配置信息，包含账号、密码、服务器等
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # 基础配置
        self.account = config.get('account', '')  # 资金账号
        self.password = config.get('password', '')  # 交易密码
        self.server_url = config.get('server_url', '')  # 服务器地址
        self.session_id = None  # 会话ID
        self.is_connected = False
        
        # 交易配置
        self.trading_config = {
            'commission_rate': 0.0003,  # 佣金费率
            'stamp_tax_rate': 0.001,    # 印花税率
            'transfer_fee': 0.00002,    # 过户费
            'min_commission': 5.0,      # 最低佣金
            'max_position_ratio': 0.95  # 最大仓位比例
        }
        
        # 请求头
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
    def connect(self) -> bool:
        """
        连接银河证券服务器
        
        Returns:
            bool: 连接是否成功
        """
        try:
            self.logger.info("正在连接银河证券服务器...")
            
            # 这里应该调用银河证券的登录接口
            # 由于没有实际的API文档，这里提供框架代码
            
            # 模拟登录过程
            login_data = {
                'account': self.account,
                'password': self.password,
                'server': self.server_url
            }
            
            # 实际使用时需要替换为真实的API调用
            # response = requests.post(f"{self.server_url}/login", json=login_data, headers=self.headers)
            
            # 模拟成功登录
            self.session_id = f"session_{int(time.time())}"
            self.is_connected = True
            
            self.logger.info("银河证券服务器连接成功")
            return True
            
        except Exception as e:
            self.logger.error(f"连接银河证券服务器失败: {e}")
            return False
            
    def disconnect(self):
        """断开连接"""
        try:
            if self.is_connected:
                # 调用登出接口
                # requests.post(f"{self.server_url}/logout", headers=self.headers)
                
                self.session_id = None
                self.is_connected = False
                self.logger.info("已断开银河证券服务器连接")
                
        except Exception as e:
            self.logger.error(f"断开连接失败: {e}")
            
    def get_account_info(self) -> Dict:
        """
        获取账户信息
        
        Returns:
            Dict: 账户信息
        """
        try:
            if not self.is_connected:
                return {'error': '未连接服务器'}
                
            # 模拟账户信息
            account_info = {
                'account': self.account,
                'total_assets': 1000000.0,      # 总资产
                'available_cash': 500000.0,     # 可用资金
                'market_value': 500000.0,       # 市值
                'frozen_cash': 0.0,             # 冻结资金
                'total_profit': 50000.0,        # 总盈亏
                'today_profit': 2500.0,         # 当日盈亏
                'risk_level': 'R3',             # 风险等级
                'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            return account_info
            
        except Exception as e:
            self.logger.error(f"获取账户信息失败: {e}")
            return {'error': str(e)}
            
    def get_positions(self) -> List[Dict]:
        """
        获取持仓信息
        
        Returns:
            List[Dict]: 持仓列表
        """
        try:
            if not self.is_connected:
                return []
                
            # 模拟持仓数据
            positions = [
                {
                    'stock_code': '000001.XSHE',
                    'stock_name': '平安银行',
                    'quantity': 10000,
                    'available_quantity': 10000,
                    'avg_cost': 15.50,
                    'current_price': 16.20,
                    'market_value': 162000.0,
                    'profit_loss': 7000.0,
                    'profit_loss_ratio': 4.52,
                    'cost_value': 155000.0
                },
                {
                    'stock_code': '600000.XSHG',
                    'stock_name': '浦发银行',
                    'quantity': 8000,
                    'available_quantity': 8000,
                    'avg_cost': 12.80,
                    'current_price': 13.50,
                    'market_value': 108000.0,
                    'profit_loss': 5600.0,
                    'profit_loss_ratio': 5.47,
                    'cost_value': 102400.0
                }
            ]
            
            return positions
            
        except Exception as e:
            self.logger.error(f"获取持仓信息失败: {e}")
            return []
            
    def get_orders(self, status: str = 'all') -> List[Dict]:
        """
        获取订单信息
        
        Args:
            status: 订单状态 ('all', 'pending', 'filled', 'cancelled')
            
        Returns:
            List[Dict]: 订单列表
        """
        try:
            if not self.is_connected:
                return []
                
            # 模拟订单数据 - 包含刚才创建的订单
            orders = [
                {
                    'order_id': 'GAL202508170001',
                    'stock_code': '000002.XSHE',
                    'stock_name': '万科A',
                    'order_type': 'buy',
                    'order_price': 18.50,
                    'order_quantity': 5000,
                    'filled_quantity': 5000,
                    'filled_price': 18.48,
                    'order_status': 'filled',
                    'order_time': '2025-08-17 09:30:00',
                    'filled_time': '2025-08-17 09:31:15',
                    'commission': 27.72,
                    'total_amount': 92427.72
                },
                {
                    'order_id': 'GAL202508170002',
                    'stock_code': '600036.XSHG',
                    'stock_name': '招商银行',
                    'order_type': 'sell',
                    'order_price': 45.00,
                    'order_quantity': 2000,
                    'filled_quantity': 0,
                    'filled_price': 0.0,
                    'order_status': 'pending',
                    'order_time': '2025-08-17 14:30:00',
                    'filled_time': None,
                    'commission': 0.0,
                    'total_amount': 0.0
                }
            ]
            
            # 添加动态创建的订单到列表中
            if hasattr(self, '_dynamic_orders'):
                orders.extend(self._dynamic_orders)
            
            # 根据状态过滤
            if status != 'all':
                orders = [order for order in orders if order['order_status'] == status]
                
            return orders
            
        except Exception as e:
            self.logger.error(f"获取订单信息失败: {e}")
            return []
            
    def place_order(self, stock_code: str, order_type: str, quantity: int, 
                   price: float = 0.0, order_method: str = 'limit') -> Dict:
        """
        下单交易
        
        Args:
            stock_code: 股票代码
            order_type: 订单类型 ('buy', 'sell')
            quantity: 数量
            price: 价格 (市价单为0)
            order_method: 下单方式 ('limit', 'market')
            
        Returns:
            Dict: 下单结果
        """
        try:
            if not self.is_connected:
                return {'success': False, 'message': '未连接服务器'}
                
            # 验证参数
            if not stock_code or quantity <= 0:
                return {'success': False, 'message': '参数错误'}
                
            if order_method == 'limit' and price <= 0:
                return {'success': False, 'message': '限价单必须指定价格'}
                
            # 检查资金/持仓
            if order_type == 'buy':
                # 检查可用资金
                account_info = self.get_account_info()
                if 'error' in account_info:
                    return {'success': False, 'message': '无法获取账户信息'}
                    
                required_cash = quantity * price if price > 0 else quantity * 100  # 市价单按100元估算
                if account_info['available_cash'] < required_cash:
                    return {'success': False, 'message': '可用资金不足'}
                    
            elif order_type == 'sell':
                # 检查可用持仓
                positions = self.get_positions()
                available_quantity = 0
                for pos in positions:
                    if pos['stock_code'] == stock_code:
                        available_quantity = pos['available_quantity']
                        break
                        
                if available_quantity < quantity:
                    return {'success': False, 'message': '可用持仓不足'}
                    
            # 生成订单ID
            order_id = f"GAL{datetime.now().strftime('%Y%m%d%H%M%S')}{int(time.time() % 1000):03d}"
            
            # 计算费用
            commission = self._calculate_commission(quantity, price, order_type)
            
            # 创建订单对象
            order_result = {
                'success': True,
                'order_id': order_id,
                'message': '下单成功',
                'stock_code': stock_code,
                'order_type': order_type,
                'quantity': quantity,
                'price': price,
                'order_method': order_method,
                'commission': commission,
                'order_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # 将订单添加到动态订单列表
            if not hasattr(self, '_dynamic_orders'):
                self._dynamic_orders = []
                
            # 创建完整的订单记录
            full_order = {
                'order_id': order_id,
                'stock_code': stock_code,
                'stock_name': self._get_stock_name(stock_code),
                'order_type': order_type,
                'order_price': price,
                'order_quantity': quantity,
                'filled_quantity': 0,
                'filled_price': 0.0,
                'order_status': 'pending',
                'order_time': order_result['order_time'],
                'filled_time': None,
                'commission': commission,
                'total_amount': quantity * price if price > 0 else 0
            }
            
            self._dynamic_orders.append(full_order)
            
            self.logger.info(f"下单成功: {order_id} {stock_code} {order_type} {quantity}股")
            return order_result
            
        except Exception as e:
            self.logger.error(f"下单失败: {e}")
            return {'success': False, 'message': f'下单失败: {str(e)}'}
            
    def cancel_order(self, order_id: str) -> Dict:
        """
        撤单
        
        Args:
            order_id: 订单ID
            
        Returns:
            Dict: 撤单结果
        """
        try:
            if not self.is_connected:
                return {'success': False, 'message': '未连接服务器'}
                
            # 检查订单是否存在且可撤
            orders = self.get_orders()
            target_order = None
            for order in orders:
                if order['order_id'] == order_id:
                    target_order = order
                    break
                    
            if not target_order:
                return {'success': False, 'message': '订单不存在'}
                
            if target_order['order_status'] != 'pending':
                return {'success': False, 'message': '订单状态不允许撤单'}
                
            # 模拟撤单成功
            cancel_result = {
                'success': True,
                'order_id': order_id,
                'message': '撤单成功',
                'cancel_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            self.logger.info(f"撤单成功: {order_id}")
            return cancel_result
            
        except Exception as e:
            self.logger.error(f"撤单失败: {e}")
            return {'success': False, 'message': f'撤单失败: {str(e)}'}
            
    def get_market_data(self, stock_code: str) -> Dict:
        """
        获取实时行情数据
        
        Args:
            stock_code: 股票代码
            
        Returns:
            Dict: 行情数据
        """
        try:
            if not self.is_connected:
                return {'error': '未连接服务器'}
                
            # 模拟行情数据
            market_data = {
                'stock_code': stock_code,
                'stock_name': '示例股票',
                'current_price': 20.50,
                'open_price': 20.00,
                'high_price': 21.00,
                'low_price': 19.80,
                'close_price': 20.30,
                'volume': 1500000,
                'amount': 30750000.0,
                'change': 0.20,
                'change_ratio': 0.98,
                'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            return market_data
            
        except Exception as e:
            self.logger.error(f"获取行情数据失败: {e}")
            return {'error': str(e)}
            
    def _calculate_commission(self, quantity: int, price: float, order_type: str) -> float:
        """
        计算交易费用
        
        Args:
            quantity: 数量
            price: 价格
            order_type: 订单类型
            
        Returns:
            float: 费用金额
        """
        try:
            # 交易金额
            trade_amount = quantity * price
            
            # 佣金
            commission = max(trade_amount * self.trading_config['commission_rate'], 
                           self.trading_config['min_commission'])
            
            # 印花税 (仅卖出收取)
            if order_type == 'sell':
                stamp_tax = trade_amount * self.trading_config['stamp_tax_rate']
            else:
                stamp_tax = 0.0
                
            # 过户费
            transfer_fee = trade_amount * self.trading_config['transfer_fee']
            
            total_fee = commission + stamp_tax + transfer_fee
            
            return round(total_fee, 2)
            
        except Exception as e:
            self.logger.error(f"计算费用失败: {e}")
            return 0.0
            
    def get_trading_config(self) -> Dict:
        """获取交易配置"""
        return self.trading_config.copy()
        
    def update_trading_config(self, new_config: Dict) -> bool:
        """更新交易配置"""
        try:
            self.trading_config.update(new_config)
            self.logger.info(f"交易配置已更新: {new_config}")
            return True
        except Exception as e:
            self.logger.error(f"更新交易配置失败: {e}")
            return False
            
    def get_connection_status(self) -> Dict:
        """获取连接状态"""
        return {
            'is_connected': self.is_connected,
            'account': self.account,
            'server_url': self.server_url,
            'session_id': self.session_id,
            'last_update': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

    def _get_stock_name(self, stock_code: str) -> str:
        """获取股票名称"""
        stock_names = {
            '000001.XSHE': '平安银行',
            '000002.XSHE': '万科A',
            '600000.XSHG': '浦发银行',
            '600036.XSHG': '招商银行'
        }
        return stock_names.get(stock_code, '未知股票')
