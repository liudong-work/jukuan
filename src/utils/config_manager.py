"""
配置文件管理模块
用于安全地管理用户配置和账号信息
"""

import json
import os
import base64
from typing import Dict, Optional, Any
from datetime import datetime
import logging

class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_dir: str = None):
        """
        初始化配置管理器
        
        Args:
            config_dir: 配置目录路径，默认为 ~/.jukuan
        """
        if config_dir is None:
            config_dir = os.path.expanduser("~/.jukuan")
        
        self.config_dir = config_dir
        self.logger = logging.getLogger(__name__)
        
        # 确保配置目录存在
        os.makedirs(self.config_dir, exist_ok=True)
    
    def _encode_password(self, password: str) -> str:
        """简单编码密码（实际应用中应使用更安全的加密）"""
        return base64.b64encode(password.encode()).decode()
    
    def _decode_password(self, encoded_password: str) -> str:
        """解码密码"""
        try:
            return base64.b64decode(encoded_password.encode()).decode()
        except Exception:
            return ""
    
    def save_credentials(self, username: str, password: str, remember: bool = True) -> bool:
        """
        保存账号信息
        
        Args:
            username: 用户名
            password: 密码
            remember: 是否记住
            
        Returns:
            bool: 保存是否成功
        """
        try:
            credentials_file = os.path.join(self.config_dir, "credentials.json")
            
            # 编码密码
            encoded_password = self._encode_password(password)
            
            credentials_data = {
                'username': username,
                'password': encoded_password,
                'remember': remember,
                'saved_at': datetime.now().isoformat(),
                'version': '1.0'
            }
            
            with open(credentials_file, 'w', encoding='utf-8') as f:
                json.dump(credentials_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"账号信息已保存到: {credentials_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"保存账号信息失败: {e}")
            return False
    
    def load_credentials(self) -> Optional[Dict[str, Any]]:
        """
        加载保存的账号信息
        
        Returns:
            Dict: 包含账号信息的字典，如果失败返回None
        """
        try:
            credentials_file = os.path.join(self.config_dir, "credentials.json")
            
            if not os.path.exists(credentials_file):
                return None
            
            with open(credentials_file, 'r', encoding='utf-8') as f:
                saved_data = json.load(f)
            
            # 解码密码
            if 'password' in saved_data:
                saved_data['password'] = self._decode_password(saved_data['password'])
            
            self.logger.info("成功加载保存的账号信息")
            return saved_data
            
        except Exception as e:
            self.logger.error(f"加载账号信息失败: {e}")
            return None
    
    def clear_credentials(self) -> bool:
        """
        清除保存的账号信息
        
        Returns:
            bool: 清除是否成功
        """
        try:
            credentials_file = os.path.join(self.config_dir, "credentials.json")
            
            if os.path.exists(credentials_file):
                os.remove(credentials_file)
                self.logger.info("已清除保存的账号信息")
            
            return True
            
        except Exception as e:
            self.logger.error(f"清除账号信息失败: {e}")
            return False
    
    def save_watchlist(self, watchlist: list) -> bool:
        """
        保存自选股列表
        
        Args:
            watchlist: 自选股列表，每个元素包含 code, name, added_time
            
        Returns:
            bool: 保存是否成功
        """
        try:
            watchlist_file = os.path.join(self.config_dir, "watchlist.json")
            
            watchlist_data = {
                'watchlist': watchlist,
                'saved_at': datetime.now().isoformat(),
                'version': '1.0'
            }
            
            with open(watchlist_file, 'w', encoding='utf-8') as f:
                json.dump(watchlist_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"自选股列表已保存到: {watchlist_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"保存自选股列表失败: {e}")
            return False
    
    def load_watchlist(self) -> list:
        """
        加载保存的自选股列表
        
        Returns:
            list: 自选股列表，如果失败返回空列表
        """
        try:
            watchlist_file = os.path.join(self.config_dir, "watchlist.json")
            
            if not os.path.exists(watchlist_file):
                return []
            
            with open(watchlist_file, 'r', encoding='utf-8') as f:
                watchlist_data = json.load(f)
            
            # 检查版本兼容性
            if 'watchlist' in watchlist_data:
                self.logger.info("成功加载保存的自选股列表")
                return watchlist_data['watchlist']
            else:
                # 兼容旧版本格式
                if isinstance(watchlist_data, list):
                    self.logger.info("成功加载旧版本格式的自选股列表")
                    return watchlist_data
                else:
                    return []
                    
        except Exception as e:
            self.logger.error(f"加载自选股列表失败: {e}")
            return []
    
    def clear_watchlist(self) -> bool:
        """
        清除保存的自选股列表
        
        Returns:
            bool: 清除是否成功
        """
        try:
            watchlist_file = os.path.join(self.config_dir, "watchlist.json")
            
            if os.path.exists(watchlist_file):
                os.remove(watchlist_file)
                self.logger.info("已清除保存的自选股列表")
            
            return True
            
        except Exception as e:
            self.logger.error(f"清除自选股列表失败: {e}")
            return False
    
    def save_config(self, config_name: str, config_data: Dict[str, Any]) -> bool:
        """
        保存配置信息
        
        Args:
            config_name: 配置名称
            config_data: 配置数据
            
        Returns:
            bool: 保存是否成功
        """
        try:
            config_file = os.path.join(self.config_dir, f"{config_name}.json")
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"配置已保存到: {config_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"保存配置失败: {e}")
            return False
    
    def load_config(self, config_name: str) -> Optional[Dict[str, Any]]:
        """
        加载配置信息
        
        Args:
            config_name: 配置名称
            
        Returns:
            Dict: 配置数据，如果失败返回None
        """
        try:
            config_file = os.path.join(self.config_dir, f"{config_name}.json")
            
            if not os.path.exists(config_file):
                return None
            
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            self.logger.info(f"成功加载配置: {config_name}")
            return config_data
            
        except Exception as e:
            self.logger.error(f"加载配置失败: {e}")
            return None
    
    def get_config_path(self) -> str:
        """获取配置目录路径"""
        return self.config_dir
    
    def list_configs(self) -> list:
        """列出所有配置文件"""
        try:
            configs = []
            for file in os.listdir(self.config_dir):
                if file.endswith('.json'):
                    configs.append(file[:-5])  # 移除.json后缀
            return configs
        except Exception as e:
            self.logger.error(f"列出配置文件失败: {e}")
            return []
