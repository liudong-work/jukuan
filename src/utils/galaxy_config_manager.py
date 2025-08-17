#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
银河证券配置管理器
管理账号信息、服务器配置等
"""

import json
import os
import logging
from typing import Dict, Optional
from datetime import datetime

class GalaxyConfigManager:
    """银河证券配置管理器"""
    
    def __init__(self):
        """初始化配置管理器"""
        self.logger = logging.getLogger(__name__)
        
        # 配置文件路径
        self.config_dir = os.path.expanduser("~/.jukuan")
        self.galaxy_config_file = os.path.join(self.config_dir, "galaxy_config.json")
        
        # 默认配置
        self.default_config = {
            'account': '',
            'password': '',
            'server_url': 'https://trade.galaxy.com.cn',  # 银河证券交易服务器
            'server_name': '银河证券',
            'remember_credentials': False,
            'auto_connect': False,
            'trading_settings': {
                'commission_rate': 0.0003,      # 佣金费率
                'stamp_tax_rate': 0.001,        # 印花税率
                'transfer_fee': 0.00002,        # 过户费
                'min_commission': 5.0,          # 最低佣金
                'max_position_ratio': 0.95,     # 最大仓位比例
                'risk_level': 'R3'              # 风险等级
            },
            'last_update': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # 确保配置目录存在
        self._ensure_config_dir()
        
    def _ensure_config_dir(self):
        """确保配置目录存在"""
        try:
            if not os.path.exists(self.config_dir):
                os.makedirs(self.config_dir)
                self.logger.info(f"创建配置目录: {self.config_dir}")
        except Exception as e:
            self.logger.error(f"创建配置目录失败: {e}")
            
    def load_config(self) -> Dict:
        """加载配置"""
        try:
            if os.path.exists(self.galaxy_config_file):
                with open(self.galaxy_config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    
                # 合并默认配置
                merged_config = self.default_config.copy()
                merged_config.update(config)
                
                self.logger.info("银河证券配置加载成功")
                return merged_config
            else:
                self.logger.info("银河证券配置文件不存在，使用默认配置")
                return self.default_config.copy()
                
        except Exception as e:
            self.logger.error(f"加载银河证券配置失败: {e}")
            return self.default_config.copy()
            
    def save_config(self, config: Dict) -> bool:
        """保存配置"""
        try:
            # 更新最后修改时间
            config['last_update'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            with open(self.galaxy_config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
                
            self.logger.info(f"银河证券配置已保存到: {self.galaxy_config_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"保存银河证券配置失败: {e}")
            return False
            
    def update_credentials(self, account: str, password: str, remember: bool = False) -> bool:
        """更新账号信息"""
        try:
            config = self.load_config()
            
            config['account'] = account
            config['password'] = password
            config['remember_credentials'] = remember
            
            # 如果不记住密码，则清空密码
            if not remember:
                config['password'] = ''
                
            return self.save_config(config)
            
        except Exception as e:
            self.logger.error(f"更新账号信息失败: {e}")
            return False
            
    def get_credentials(self) -> Dict:
        """获取账号信息"""
        try:
            config = self.load_config()
            
            if config.get('remember_credentials', False):
                return {
                    'account': config.get('account', ''),
                    'password': config.get('password', ''),
                    'server_url': config.get('server_url', ''),
                    'server_name': config.get('server_name', '')
                }
            else:
                return {
                    'account': config.get('account', ''),
                    'password': '',
                    'server_url': config.get('server_url', ''),
                    'server_name': config.get('server_name', '')
                }
                
        except Exception as e:
            self.logger.error(f"获取账号信息失败: {e}")
            return {}
            
    def update_trading_settings(self, trading_settings: Dict) -> bool:
        """更新交易设置"""
        try:
            config = self.load_config()
            config['trading_settings'].update(trading_settings)
            return self.save_config(config)
            
        except Exception as e:
            self.logger.error(f"更新交易设置失败: {e}")
            return False
            
    def get_trading_settings(self) -> Dict:
        """获取交易设置"""
        try:
            config = self.load_config()
            return config.get('trading_settings', {})
            
        except Exception as e:
            self.logger.error(f"获取交易设置失败: {e}")
            return {}
            
    def update_server_config(self, server_url: str, server_name: str) -> bool:
        """更新服务器配置"""
        try:
            config = self.load_config()
            config['server_url'] = server_url
            config['server_name'] = server_name
            return self.save_config(config)
            
        except Exception as e:
            self.logger.error(f"更新服务器配置失败: {e}")
            return False
            
    def clear_credentials(self) -> bool:
        """清除账号信息"""
        try:
            config = self.load_config()
            config['account'] = ''
            config['password'] = ''
            config['remember_credentials'] = False
            return self.save_config(config)
            
        except Exception as e:
            self.logger.error(f"清除账号信息失败: {e}")
            return False
            
    def get_config_summary(self) -> Dict:
        """获取配置摘要"""
        try:
            config = self.load_config()
            
            return {
                'account': config.get('account', ''),
                'server_name': config.get('server_name', ''),
                'server_url': config.get('server_url', ''),
                'remember_credentials': config.get('remember_credentials', False),
                'auto_connect': config.get('auto_connect', False),
                'trading_settings': config.get('trading_settings', {}),
                'last_update': config.get('last_update', ''),
                'config_file': self.galaxy_config_file
            }
            
        except Exception as e:
            self.logger.error(f"获取配置摘要失败: {e}")
            return {}
            
    def validate_config(self) -> Dict:
        """验证配置"""
        try:
            config = self.load_config()
            validation_result = {
                'is_valid': True,
                'errors': [],
                'warnings': []
            }
            
            # 检查必填字段
            if not config.get('account'):
                validation_result['is_valid'] = False
                validation_result['errors'].append('账号不能为空')
                
            if not config.get('server_url'):
                validation_result['is_valid'] = False
                validation_result['errors'].append('服务器地址不能为空')
                
            # 检查交易设置
            trading_settings = config.get('trading_settings', {})
            if trading_settings.get('commission_rate', 0) <= 0:
                validation_result['warnings'].append('佣金费率设置异常')
                
            if trading_settings.get('max_position_ratio', 0) > 1:
                validation_result['warnings'].append('最大仓位比例不能超过100%')
                
            return validation_result
            
        except Exception as e:
            self.logger.error(f"验证配置失败: {e}")
            return {
                'is_valid': False,
                'errors': [f'验证失败: {str(e)}'],
                'warnings': []
            }
            
    def reset_to_default(self) -> bool:
        """重置为默认配置"""
        try:
            return self.save_config(self.default_config.copy())
            
        except Exception as e:
            self.logger.error(f"重置配置失败: {e}")
            return False
