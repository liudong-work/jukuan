"""
聚宽登录管理模块
提供聚宽账号的完整登录管理功能，包括登录、退出登录、状态管理、配置管理等
"""

import dash
from dash import html, dcc, callback_context
import dash_bootstrap_components as dbc
from datetime import datetime
import logging
import os
import sys

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

try:
    from src.data.jq_data_provider import JQDataProvider
    from src.utils.config_manager import ConfigManager
    JQ_AVAILABLE = True
except ImportError:
    JQ_AVAILABLE = False
    print("警告: 聚宽相关模块导入失败")

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class JoinQuantLoginManager:
    """聚宽登录管理器 - 完整的登录管理功能"""
    
    def __init__(self):
        self.is_connected = False
        self.data_provider = None
        self.connection_status = "未连接"
        self.current_user = None
        self.config_manager = ConfigManager() if JQ_AVAILABLE else None
        self.connection_time = None
        
        # 自动加载保存的账号信息
        self._load_saved_credentials()
    
    def _load_saved_credentials(self):
        """加载保存的账号信息"""
        if not self.config_manager:
            return
        
        try:
            credentials = self.config_manager.load_credentials()
            if credentials:
                self.saved_username = credentials.get('username')
                self.saved_password = credentials.get('password')
                logger.info("已加载保存的账号信息")
            else:
                self.saved_username = None
                self.saved_password = None
        except Exception as e:
            logger.error(f"加载保存的账号信息失败: {e}")
            self.saved_username = None
            self.saved_password = None
    
    def create_login_section(self):
        """创建聚宽登录界面"""
        return dbc.Card([
            dbc.CardHeader([
                html.H5([
                    html.Span("🔐", className="me-2"),
                    "聚宽账号管理"
                ], className="mb-0")
            ], style={'background': 'linear-gradient(135deg, #007bff 0%, #0056b3 100%)', 'color': 'white'}),
            dbc.CardBody([
                # 连接状态显示
                html.Div(id="connection-status-display", className="mb-3"),
                
                # 登录表单（未连接时显示）
                html.Div(id="login-form", children=[
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("用户名", html_for="jq-username"),
                            dbc.Input(
                                id="jq-username",
                                type="text",
                                placeholder="请输入聚宽用户名",
                                value=self.saved_username or "",
                                className="mb-3"
                            )
                        ], width=6),
                        dbc.Col([
                            dbc.Label("密码", html_for="jq-password"),
                            dbc.Input(
                                id="jq-password",
                                type="password",
                                placeholder="请输入聚宽密码",
                                value=self.saved_password or "",
                                className="mb-3"
                            )
                        ], width=6)
                    ]),
                    dbc.Row([
                        dbc.Col([
                            dbc.Checkbox(
                                id="remember-credentials",
                                label="记住账号密码",
                                value=bool(self.saved_username),
                                className="mb-3"
                            )
                        ], width=6),
                        dbc.Col([
                            dbc.Button([
                                html.Span("🗑️", className="me-2"),
                                "清除保存"
                            ], id="clear-saved", color="warning", size="sm", className="float-end")
                        ], width=6)
                    ]),
                    dbc.Row([
                        dbc.Col([
                            dbc.Button([
                                html.Span("🔗", className="me-2"),
                                "登录聚宽"
                            ], id="connect-jq", color="primary", size="md", className="w-100")
                        ], width=12)
                    ])
                ]),
                
                # 已连接状态显示（连接后显示）
                html.Div(id="connected-status", style={"display": "none"}, children=[
                    dbc.Row([
                        dbc.Col([
                            dbc.Alert([
                                html.H6("✅ 聚宽连接成功", className="mb-2"),
                                html.P(f"当前用户: {self.current_user or '未知'}", className="mb-1"),
                                html.P(f"连接时间: {self.connection_time or '未知'}", className="mb-1"),
                                html.P(f"连接状态: {self.connection_status}", className="mb-2")
                            ], color="success", className="mb-3")
                        ], width=12)
                    ]),
                    dbc.Row([
                        dbc.Col([
                            dbc.Button([
                                html.Span("❌", className="me-2"),
                                "退出登录"
                            ], id="disconnect-jq", color="danger", size="md", className="w-100")
                        ], width=12)
                    ])
                ]),
                
                # 操作状态显示
                html.Div(id="operation-status", className="mt-3")
            ])
        ], className="mb-3")
    
    def login(self, username, password, remember=False):
        """登录聚宽"""
        try:
            if not JQ_AVAILABLE:
                return False, "聚宽SDK未安装，请运行: pip install jqdatasdk"
            
            if not username or not password:
                return False, "用户名和密码不能为空"
            
            logger.info(f"开始登录聚宽，用户名: {username}")
            
            # 创建数据提供者实例，传入用户名和密码
            self.data_provider = JQDataProvider(username, password)
            
            # 检查连接状态
            if self.data_provider.is_connected:
                self.is_connected = True
                self.current_user = username
                self.connection_status = "已连接"
                self.connection_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                logger.info(f"聚宽登录成功: {username}")
                
                # 如果选择记住账号，保存到本地
                if remember and self.config_manager:
                    self.config_manager.save_credentials(username, password)
                    logger.info("账号信息已保存到本地")
                
                return True, "登录成功"
            else:
                logger.error("聚宽登录失败: 无法建立连接")
                return False, "登录失败: 无法建立连接"
                
        except Exception as e:
            logger.error(f"聚宽登录失败: {e}")
            return False, f"登录失败: {str(e)}"
    
    def logout(self):
        """退出登录"""
        try:
            if self.data_provider:
                self.data_provider.disconnect()
            
            self.is_connected = False
            self.connection_status = "已断开"
            self.current_user = None
            self.connection_time = None
            self.data_provider = None
            logger.info("聚宽已退出登录")
            return True, "退出登录成功"
        except Exception as e:
            logger.error(f"退出登录失败: {e}")
            return False, str(e)
    
    def get_connection_status(self):
        """获取连接状态"""
        if self.is_connected:
            return dbc.Alert([
                html.H6("✅ 聚宽连接成功", className="mb-2"),
                html.P(f"当前用户: {self.current_user}", className="mb-1"),
                html.P(f"连接时间: {self.connection_time}", className="mb-1"),
                html.P(f"连接状态: {self.connection_status}", className="mb-0")
            ], color="success", className="mb-0")
        else:
            return dbc.Alert(
                "❌ 聚宽未连接",
                color="danger",
                className="mb-0"
            )
    
    def get_data_provider(self):
        """获取数据提供者实例"""
        return self.data_provider if self.is_connected else None
    
    def is_user_logged_in(self):
        """检查用户是否已登录"""
        return self.is_connected and self.data_provider is not None
    
    def get_user_info(self):
        """获取用户信息"""
        if self.is_connected:
            return {
                'username': self.current_user,
                'connection_time': self.connection_time,
                'status': self.connection_status
            }
        return None
    
    def clear_saved_credentials(self):
        """清除保存的账号信息"""
        if not self.config_manager:
            return False
        
        try:
            self.config_manager.clear_credentials()
            self.saved_username = None
            self.saved_password = None
            logger.info("已清除保存的账号信息")
            return True
        except Exception as e:
            logger.error(f"清除保存的账号信息失败: {e}")
            return False
    
    def refresh_status(self):
        """刷新连接状态"""
        if self.data_provider:
            try:
                # 这里可以添加实际的连接状态检查
                # 暂时返回当前状态
                return self.is_connected
            except Exception as e:
                logger.error(f"刷新连接状态失败: {e}")
                self.is_connected = False
                return False
        return False

# 创建全局实例
login_manager = JoinQuantLoginManager()

# ==================== 便捷函数接口 ====================

def create_login_section():
    """创建聚宽登录区域的便捷函数"""
    return login_manager.create_login_section()

def login_joinquant(username, password, remember=False):
    """登录聚宽的便捷函数"""
    return login_manager.login(username, password, remember)

def logout_joinquant():
    """退出登录聚宽的便捷函数"""
    return login_manager.logout()

def get_connection_status():
    """获取连接状态的便捷函数"""
    return login_manager.get_connection_status()

def get_data_provider():
    """获取数据提供者实例的便捷函数"""
    return login_manager.get_data_provider()

def is_user_logged_in():
    """检查用户是否已登录的便捷函数"""
    return login_manager.is_user_logged_in()

def get_user_info():
    """获取用户信息的便捷函数"""
    return login_manager.get_user_info()

def clear_saved_credentials():
    """清除保存的账号信息的便捷函数"""
    return login_manager.clear_saved_credentials()

def refresh_connection_status():
    """刷新连接状态的便捷函数"""
    return login_manager.refresh_status()
