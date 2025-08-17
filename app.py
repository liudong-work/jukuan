"""
量化交易系统Web应用
基于Dash框架的Web界面

版本: v1.1.0
发布日期: 2025-08-17
作者: liudong-work
"""

import dash
from dash import dcc, html, Input, Output, State, callback_context
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import logging
from datetime import datetime, timedelta
import os
import sys
import re
import json

# 添加src目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.data.jq_data_provider import JQDataProvider
from src.strategies.ma_cross_strategy import MACrossStrategy
from src.backtest.backtest_engine import BacktestEngine

# 导入聚宽登录模块
from src.utils.joinquant_login import create_login_section

# 配置日志
logging.basicConfig(level=logging.INFO)

# 版本信息
__version__ = "1.1.0"
__author__ = "liudong-work"
__date__ = "2025-08-17"

# 初始化Dash应用
app = dash.Dash(__name__, external_stylesheets=[
    dbc.themes.BOOTSTRAP,
    "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css"
])
app.title = f"量化交易系统 v{__version__}"

# 全局变量
data_provider = None
current_data = None
current_strategy = None
backtest_results = None
watchlist = []  # 自选股列表

# 自定义CSS样式
custom_css = {
    'card-header': {
        'background': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        'color': 'white',
        'font-weight': 'bold',
        'border-radius': '10px 10px 0 0'
    },
    'success-card': {
        'border-left': '4px solid #28a745',
        'box-shadow': '0 4px 6px rgba(0, 0, 0, 0.1)'
    },
    'warning-card': {
        'border-left': '4px solid #ffc107',
        'box-shadow': '0 4px 6px rgba(0, 0, 0, 0.1)'
    },
    'info-card': {
        'border-left': '4px solid #17a2b8',
        'box-shadow': '0 4px 6px rgba(0, 0, 0, 0.1)'
    }
}

def create_joinquant_login_section():
    """创建聚宽登录区域 - 使用独立模块"""
    return create_login_section()

# 页面布局
app.layout = dbc.Container([
    # 页面头部
    dbc.Row([
        dbc.Col([
            html.Div([
                html.H2([
                    html.Span("📈", className="me-2"),
                    "量化交易系统"
                ], className="text-center mb-2 text-primary fw-bold"),
                html.P("基于聚宽数据的智能量化交易平台", className="text-center text-muted mb-2")
            ], className="py-2")
        ])
    ], className="bg-light rounded mb-3"),
    
    # 导航标签页
    dbc.Row([
        dbc.Col([
            dbc.Tabs([
                # 数据连接标签页
                dbc.Tab([
                    dbc.Row([
                        dbc.Col([
                            dbc.Card([
                                dbc.CardHeader([
                                    html.H5([
                                        html.Span("🔌", className="me-2"),
                                        "聚宽数据连接"
                                    ], className="mb-0")
                                ], style=custom_css['card-header']),
                                dbc.CardBody([
                                    # 使用独立的聚宽登录组件
                                    create_joinquant_login_section(),
                                    
                                    # 数据获取区域
                                    dbc.Row([
                                        dbc.Col([
                                            dbc.Label("股票代码", className="fw-bold"),
                                            dbc.Input(
                                                id="stock-code",
                                                placeholder="如: 000001.XSHE",
                                                type="text",
                                                className="mb-3"
                                            )
                                        ], width=4),
                                        dbc.Col([
                                            dbc.Label("开始日期", className="fw-bold"),
                                            dcc.DatePickerSingle(
                                                id="start-date",
                                                placeholder="开始日期",
                                                date=datetime.now() - timedelta(days=365),
                                                className="mb-3"
                                            )
                                        ], width=4),
                                        dbc.Col([
                                            dbc.Label("结束日期", className="fw-bold"),
                                            dcc.DatePickerSingle(
                                                id="end-date",
                                                placeholder="结束日期",
                                                date=datetime.now(),
                                                className="mb-3"
                                            )
                                        ], width=4)
                                    ]),
                                    dbc.Row([
                                        dbc.Col([
                                            dbc.Button([
                                                html.Span("⬇️", className="me-2"),
                                                "获取数据"
                                            ], id="fetch-data", color="success", size="md")
                                        ], width=8),
                                        dbc.Col([
                                            html.Div(id="data-status", className="mt-2")
                                        ], width=4)
                                    ])
                                ])
                            ], style=custom_css['info-card'])
                        ], width=12)
                    ], className="mb-4")
                ], label="🔌 数据连接", tab_id="data-connection"),
                
                # 策略回测标签页
                dbc.Tab([
                    dbc.Row([
                        dbc.Col([
                            dbc.Card([
                                dbc.CardHeader([
                                    html.H5([
                                        html.Span("⚙️", className="me-2"),
                                        "策略配置"
                                    ], className="mb-0")
                                ], style=custom_css['card-header']),
                                dbc.CardBody([
                                    dbc.Row([
                                        dbc.Col([
                                            dbc.Label("短期均线周期", className="fw-bold"),
                                            dbc.Input(
                                                id="short-window",
                                                type="number",
                                                value=5,
                                                min=1,
                                                max=50,
                                                className="mb-3"
                                            )
                                        ], width=3),
                                        dbc.Col([
                                            dbc.Label("长期均线周期", className="fw-bold"),
                                            dbc.Input(
                                                id="long-window",
                                                type="number",
                                                value=20,
                                                min=5,
                                                max=200,
                                                className="mb-3"
                                            )
                                        ], width=3),
                                        dbc.Col([
                                            dbc.Label("仓位比例", className="fw-bold"),
                                            dbc.Input(
                                                id="position-size",
                                                type="number",
                                                value=0.1,
                                                min=0.01,
                                                max=1.0,
                                                step=0.01,
                                                className="mb-3"
                                            )
                                        ], width=3),
                                        dbc.Col([
                                            dbc.Label("初始资金", className="fw-bold"),
                                            dbc.Input(
                                                id="initial-capital",
                                                type="number",
                                                value=1000000,
                                                min=10000,
                                                step=10000,
                                                className="mb-3"
                                            )
                                        ], width=3)
                                    ]),
                                    dbc.Row([
                                        dbc.Col([
                                            dbc.Button([
                                                html.Span("▶️", className="me-2"),
                                                "运行回测"
                                            ], id="run-backtest", color="warning", size="md")
                                        ], width=8),
                                        dbc.Col([
                                            html.Div(id="backtest-status", className="mt-2")
                                        ], width=4)
                                    ])
                                ])
                            ], style=custom_css['warning-card'])
                        ], width=12)
                    ], className="mb-4"),
                    
                    # 回测结果区域
                    dbc.Row([
                        dbc.Col([
                            dbc.Card([
                                dbc.CardHeader([
                                    html.H5([
                                        html.Span("📊", className="me-2"),
                                        "回测结果"
                                    ], className="mb-0")
                                ], style=custom_css['card-header']),
                                dbc.CardBody([
                                    html.Div(id="backtest-summary"),
                                    html.Div(id="backtest-charts")
                                ])
                            ], style=custom_css['info-card'])
                        ], width=12)
                    ])
                ], label="📈 策略回测", tab_id="strategy-backtest"),
                
                # 智能选股标签页
                dbc.Tab([
                    dbc.Row([
                        dbc.Col([
                            dbc.Card([
                                dbc.CardHeader([
                                    html.H5([
                                        html.Span("🔍", className="me-2"),
                                        "智能选股"
                                    ], className="mb-0")
                                ], style=custom_css['card-header']),
                                dbc.CardBody([
                                    dbc.Row([
                                        dbc.Col([
                                            dbc.Label("选股策略", className="fw-bold"),
                                            dcc.Dropdown(
                                                id="screening-strategy",
                                                options=[
                                                    # 高频数据挖掘策略（充分利用有限数据）
                                                    {'label': '🔍 高频数据挖掘(深度分析)', 'value': 'high_frequency_mining'},
                                                    # 短期优化策略（适应有限数据）
                                                    {'label': '⚡ 短期均线交叉(3/8日)', 'value': 'short_term_ma'},
                                                    {'label': '⚡ 短期KDJ+MACD(5/10日)', 'value': 'short_term_kdj_macd'},
                                                    {'label': '⚡ 短期RSI+动量(5/3日)', 'value': 'short_term_rsi_momentum'},
                                                    # 传统策略
                                                    {'label': '📈 均线交叉策略', 'value': 'ma_cross'},
                                                    {'label': '🎯 KDJ+MACD双重金叉', 'value': 'kdj_macd'},
                                                    {'label': '📊 放量突破策略', 'value': 'volume_breakout'},
                                                    {'label': '📉 RSI超卖策略', 'value': 'rsi_oversold'},
                                                    {'label': '📋 布林带策略', 'value': 'bollinger_bands'},
                                                    {'label': '🚀 动量策略', 'value': 'momentum'},
                                                    {'label': '🔄 双重策略', 'value': 'dual_strategy'},
                                                    {'label': '🏭 行业轮动策略', 'value': 'industry_rotation'},
                                                    {'label': '⭐ 高级复合选股策略', 'value': 'advanced_conditions'},
                                                    {'label': '🎛️ 灵活选股策略', 'value': 'flexible_screening'}
                                                ],
                                                value='short_term_ma',  # 默认使用短期策略
                                                placeholder="选择选股策略",
                                                className="mb-3"
                                            )
                                        ], width=4),
                                        dbc.Col([
                                            dbc.Label("价格范围", className="fw-bold"),
                                            dbc.Row([
                                                dbc.Col([
                                                    dbc.Input(
                                                        id="min-price",
                                                        type="number",
                                                        value=5.0,
                                                        min=0.1,
                                                        step=0.1,
                                                        placeholder="最低价格",
                                                        className="mb-2"
                                                    )
                                                ], width=6),
                                                dbc.Col([
                                                    dbc.Input(
                                                        id="max-price",
                                                        type="number",
                                                        value=100.0,
                                                        min=0.1,
                                                        step=0.1,
                                                        placeholder="最高价格",
                                                        className="mb-2"
                                                    )
                                                ], width=6)
                                            ])
                                        ], width=4),
                                        dbc.Col([
                                            dbc.Button([
                                                html.Span("🔍", className="me-2"),
                                                "开始选股"
                                            ], id="start-screening", color="info", size="md", className="mt-4")
                                        ], width=4)
                                    ]),
                                    html.Div(id="screening-status", className="mt-3"),
                                    
                                    # 高级选股配置区域
                                    html.Div([
                                        html.Hr(),
                                        html.H6([
                                            html.Span("⚙️", className="me-2"),
                                            "高级选股配置"
                                        ], className="mt-3 mb-3 text-primary"),
                                        dbc.Row([
                                            dbc.Col([
                                                dbc.Checkbox(
                                                    id="exclude-tech-board",
                                                    label="排除科创板北交所",
                                                    value=True,
                                                    className="me-2 mb-2"
                                                ),
                                                html.Br(),
                                                dbc.Checkbox(
                                                    id="exclude-st",
                                                    label="排除ST股票",
                                                    value=True,
                                                    className="me-2 mb-2"
                                                ),
                                                html.Br(),
                                                dbc.Checkbox(
                                                    id="has-limit-up",
                                                    label="19天内有过涨停",
                                                    value=False,
                                                    className="me-2"
                                                )
                                            ], width=4),
                                            dbc.Col([
                                                dbc.Checkbox(
                                                    id="not-limit-up-today",
                                                    label="当日未涨停",
                                                    value=True,
                                                    className="me-2 mb-2"
                                                ),
                                                html.Br(),
                                                dbc.Checkbox(
                                                    id="not-limit-down-today",
                                                    label="当日未跌停",
                                                    value=True,
                                                    className="me-2 mb-2"
                                                ),
                                                html.Br(),
                                                dbc.Checkbox(
                                                    id="weekly-kdj-up",
                                                    label="周线KDJ向上",
                                                    value=False,
                                                    className="me-2"
                                                )
                                            ], width=4),
                                            dbc.Col([
                                                dbc.Checkbox(
                                                    id="weekly-macd-up",
                                                    label="周线MACD往上",
                                                    value=False,
                                                    className="me-2 mb-2"
                                                ),
                                                html.Br(),
                                                dbc.Checkbox(
                                                    id="daily-macd-up",
                                                    label="日线MACD向上",
                                                    value=False,
                                                    className="me-2 mb-2"
                                                ),
                                                html.Br(),
                                                dbc.Checkbox(
                                                    id="volume-increasing",
                                                    label="成交量升序",
                                                    value=False,
                                                    className="me-2"
                                                )
                                            ], width=4)
                                        ]),
                                        dbc.Row([
                                            dbc.Col([
                                                dbc.Button([
                                                    html.Span("✅", className="me-2"),
                                                    "应用高级配置"
                                                ], id="apply-advanced-config", color="secondary", size="sm", className="mt-3")
                                            ], width=12)
                                        ])
                                    ], id="advanced-config-area", style={"display": "none"}),
                                    
                                    html.Div(id="screening-results", className="mt-4")
                                ])
                            ], style=custom_css['success-card'])
                        ], width=12)
                    ])
                ], label="🔍 智能选股", tab_id="stock-screening"),
                
                # 板块分析标签页
                dbc.Tab([
                    dbc.Row([
                        dbc.Col([
                            dbc.Card([
                                dbc.CardHeader([
                                    html.H5([
                                        html.Span("📊", className="me-2"),
                                        "板块分析"
                                    ], className="mb-0")
                                ], style=custom_css['card-header']),
                                dbc.CardBody([
                                    dbc.Row([
                                        dbc.Col([
                                            dbc.Button([
                                                html.Span("🔄", className="me-2"),
                                                "刷新板块数据"
                                            ], id="refresh-sectors", color="primary", size="md")
                                        ], width=4),
                                        dbc.Col([
                                            html.Div(id="sector-loading-status", className="mt-2")
                                        ], width=8)
                                    ]),
                                    html.Hr(),
                                    dbc.Tabs([
                                        dbc.Tab([
                                            html.Div(id="sector-performance-results")
                                        ], label="🏭 申万行业", tab_id="sw-industry"),
                                        dbc.Tab([
                                            html.Div(id="concept-performance-results")
                                        ], label="💡 概念板块", tab_id="concept-sectors")
                                    ], id="sector-tabs", active_tab="sw-industry")
                                ])
                            ], style=custom_css['info-card'])
                        ], width=12)
                    ])
                ], label="📊 板块分析", tab_id="sector-analysis"),
                
                # 数据预览标签页
                dbc.Tab([
                    dbc.Row([
                        dbc.Col([
                            dbc.Card([
                                dbc.CardHeader([
                                    html.H5([
                                        html.Span("📋", className="me-2"),
                                        "数据预览"
                                    ], className="mb-0")
                                ], style=custom_css['card-header']),
                                dbc.CardBody([
                                    html.Div(id="data-table")
                                ])
                            ], style=custom_css['warning-card'])
                        ], width=12)
                    ])
                ], label="📋 数据预览", tab_id="data-preview"),
                
                # 银河证券标签页
                dbc.Tab([
                    dbc.Row([
                        dbc.Col([
                            dbc.Card([
                                dbc.CardHeader([
                                    html.H5([
                                        html.Span("🏦", className="me-2"),
                                        "银河证券"
                                    ], className="mb-0")
                                ], style=custom_css['card-header']),
                                dbc.CardBody([
                                    # 银河证券连接区域
                                    dbc.Row([
                                        dbc.Col([
                                            dbc.Card([
                                                dbc.CardHeader([
                                                    html.H6([
                                                        html.Span("🔗", className="me-2"),
                                                        "连接银河证券"
                                                    ], className="mb-0")
                                                ], style={'background': 'linear-gradient(135deg, #28a745 0%, #20c997 100%)', 'color': 'white'}),
                                                dbc.CardBody([
                                                    dbc.Row([
                                                        dbc.Col([
                                                            dbc.Label("资金账号", className="fw-bold"),
                                                            dbc.Input(
                                                                id="galaxy-account",
                                                                type="text",
                                                                placeholder="请输入资金账号",
                                                                className="mb-3"
                                                            )
                                                        ], width=4),
                                                        dbc.Col([
                                                            dbc.Label("交易密码", className="fw-bold"),
                                                            dbc.Input(
                                                                id="galaxy-password",
                                                                type="password",
                                                                placeholder="请输入交易密码",
                                                                className="mb-3"
                                                            )
                                                        ], width=4),
                                                        dbc.Col([
                                                            dbc.Label("服务器地址", className="fw-bold"),
                                                            dbc.Select(
                                                                id="galaxy-server",
                                                                options=[
                                                                    {"label": "银河证券主站", "value": "https://trade.galaxy.com.cn"},
                                                                    {"label": "银河证券测试站", "value": "https://test.galaxy.com.cn"}
                                                                ],
                                                                value="https://trade.galaxy.com.cn",
                                                                className="mb-3"
                                                            )
                                                        ], width=4)
                                                    ]),
                                                    dbc.Row([
                                                        dbc.Col([
                                                            dbc.Checkbox(
                                                                id="galaxy-remember",
                                                                label="记住账号信息",
                                                                value=False,
                                                                className="mb-3"
                                                            )
                                                        ], width=6),
                                                        dbc.Col([
                                                            dbc.Button([
                                                                html.Span("🔗", className="me-2"),
                                                                "连接银河证券"
                                                            ], id="connect-galaxy", color="success", size="md", className="w-100")
                                                        ], width=6)
                                                    ]),
                                                    html.Div(id="galaxy-connection-status", className="mt-3")
                                                ])
                                            ], style=custom_css['success-card'])
                                        ], width=12)
                                    ], className="mb-4"),
                                    
                                    # 账户信息区域
                                    dbc.Row([
                                        dbc.Col([
                                            dbc.Card([
                                                dbc.CardHeader([
                                                    html.H6([
                                                        html.Span("💰", className="me-2"),
                                                        "账户信息"
                                                    ], className="mb-0")
                                                ], style={'background': 'linear-gradient(135deg, #17a2b8 0%, #6f42c1 100%)', 'color': 'white'}),
                                                dbc.CardBody([
                                                    html.Div(id="galaxy-account-info")
                                                ])
                                            ], style=custom_css['info-card'])
                                        ], width=12)
                                    ], className="mb-4"),
                                    
                                    # 持仓信息区域
                                    dbc.Row([
                                        dbc.Col([
                                            dbc.Card([
                                                dbc.CardHeader([
                                                    html.H6([
                                                        html.Span("💼", className="me-2"),
                                                        "持仓信息"
                                                    ], className="mb-0")
                                                ], style={'background': 'linear-gradient(135deg, #ffc107 0%, #fd7e14 100%)', 'color': 'white'}),
                                                dbc.CardBody([
                                                    html.Div(id="galaxy-positions")
                                                ])
                                            ], style=custom_css['warning-card'])
                                        ], width=12)
                                    ], className="mb-4"),
                                    
                                    # 交易订单区域
                                    dbc.Row([
                                        dbc.Col([
                                            dbc.Card([
                                                dbc.CardHeader([
                                                    html.H6([
                                                        html.Span("📋", className="me-2"),
                                                        "交易订单"
                                                    ], className="mb-0")
                                                ], style={'background': 'linear-gradient(135deg, #6c757d 0%, #495057 100%)', 'color': 'white'}),
                                                dbc.CardBody([
                                                    html.Div(id="galaxy-orders")
                                                ])
                                            ], style=custom_css['info-card'])
                                        ], width=12)
                                    ])
                                ])
                            ], style=custom_css['info-card'])
                        ], width=12)
                    ])
                ], label="🏦 银河证券", tab_id="galaxy-securities")
            ], id="main-tabs", active_tab="data-connection")
        ], width=12)
    ])
], fluid=True, className="py-4")

# 回调函数：连接聚宽
@app.callback(
    Output("operation-status", "children"),
    Input("connect-jq", "n_clicks"),
    State("jq-username", "value"),
    State("jq-password", "value"),
    State("remember-credentials", "value"),
    prevent_initial_call=True
)
def connect_joinquant(n_clicks, username, password, remember):
    print(f"=== 连接聚宽回调被触发 ===")
    print(f"n_clicks: {n_clicks}")
    print(f"username: {username}")
    print(f"password: {'*' * len(password) if password else 'None'}")
    print(f"remember: {remember}")
    print(f"==========================")
    
    try:
        if not username or not password:
            print("用户名或密码为空")
            return dbc.Alert("⚠️ 请输入用户名和密码", color="warning", className="mb-0")
        
        print("开始使用新的登录管理模块...")
        
        # 使用新的登录管理模块
        try:
            from src.utils.joinquant_login import login_joinquant, get_data_provider
            print("登录管理模块导入成功")
        except Exception as e:
            print(f"登录管理模块导入失败: {e}")
            return dbc.Alert(f"❌ 模块导入失败: {str(e)}", color="danger", className="mb-0")
        
        # 执行登录
        try:
            print("正在登录聚宽...")
            success, message = login_joinquant(username, password, remember)
            
            if success:
                print("聚宽登录成功")
                
                # 更新全局的data_provider变量
                global data_provider
                data_provider = get_data_provider()
                print(f"全局data_provider已更新: {data_provider}")
                
                return dbc.Alert(f"✅ {message}", color="success", className="mb-0")
            else:
                print(f"聚宽登录失败: {message}")
                return dbc.Alert(f"❌ 登录失败: {message}", color="danger", className="mb-0")
                
        except Exception as e:
            print(f"聚宽登录异常: {e}")
            return dbc.Alert(f"❌ 登录异常: {str(e)}", color="danger", className="mb-0")
            
    except Exception as e:
        print(f"回调函数执行异常: {e}")
        import traceback
        traceback.print_exc()
        return dbc.Alert(f"❌ 回调函数异常: {str(e)}", color="danger", className="mb-0")

# 回调函数：退出登录聚宽
@app.callback(
    Output("operation-status", "children", allow_duplicate=True),
    Input("disconnect-jq", "n_clicks"),
    prevent_initial_call=True
)
def disconnect_joinquant(n_clicks):
    print(f"=== 退出登录聚宽回调被触发 ===")
    print(f"n_clicks: {n_clicks}")
    print(f"==========================")
    
    try:
        print("开始使用新的登录管理模块退出登录...")
        
        # 使用新的登录管理模块
        try:
            from src.utils.joinquant_login import logout_joinquant
            print("退出登录模块导入成功")
        except Exception as e:
            print(f"退出登录模块导入失败: {e}")
            return dbc.Alert(f"❌ 模块导入失败: {str(e)}", color="danger", className="mb-0")
        
        # 执行退出登录
        try:
            print("正在退出登录聚宽...")
            success, message = logout_joinquant()
            
            if success:
                print("聚宽退出登录成功")
                return dbc.Alert(f"✅ {message}", color="success", className="mb-0")
            else:
                print(f"聚宽退出登录失败: {message}")
                return dbc.Alert(f"❌ 退出登录失败: {message}", color="danger", className="mb-0")
                
        except Exception as e:
            print(f"聚宽退出登录异常: {e}")
            return dbc.Alert(f"❌ 退出登录异常: {str(e)}", color="danger", className="mb-0")
            
    except Exception as e:
        print(f"退出登录回调函数执行异常: {e}")
        import traceback
        traceback.print_exc()
        return dbc.Alert(f"❌ 退出登录回调函数异常: {str(e)}", color="danger", className="mb-0")

# 回调函数：清除保存的账号信息
@app.callback(
    Output("operation-status", "children", allow_duplicate=True),
    Input("clear-saved", "n_clicks"),
    prevent_initial_call=True
)
def clear_saved_credentials(n_clicks):
    print(f"=== 清除保存账号回调被触发 ===")
    print(f"n_clicks: {n_clicks}")
    print(f"==========================")
    
    try:
        print("开始使用新的登录管理模块清除保存的账号...")
        
        # 使用新的登录管理模块
        try:
            from src.utils.joinquant_login import clear_saved_credentials
            print("清除账号模块导入成功")
        except Exception as e:
            print(f"清除账号模块导入失败: {e}")
            return dbc.Alert(f"❌ 模块导入失败: {str(e)}", color="danger", className="mb-0")
        
        # 执行清除
        try:
            print("正在清除保存的账号信息...")
            success = clear_saved_credentials()
            
            if success:
                print("清除保存的账号信息成功")
                return dbc.Alert("✅ 已清除保存的账号信息", color="success", className="mb-0")
            else:
                print("清除保存的账号信息失败")
                return dbc.Alert("❌ 清除保存的账号信息失败", color="danger", className="mb-0")
                
        except Exception as e:
            print(f"清除保存的账号信息异常: {e}")
            return dbc.Alert(f"❌ 清除异常: {str(e)}", color="danger", className="mb-0")
            
    except Exception as e:
        print(f"清除账号回调函数执行异常: {e}")
        import traceback
        traceback.print_exc()
        return dbc.Alert(f"❌ 清除账号回调函数异常: {str(e)}", color="danger", className="mb-0")

# 回调函数：更新界面状态显示
# @app.callback(
#     [Output("connection-status-display", "children"),
#      Output("login-form", "style"),
#      Output("connected-status", "style")],
#     [Input("operation-status", "children")],
#     prevent_initial_call=True,
#     allow_duplicate=True
# )
# def update_interface_status(operation_status):
#     """根据操作状态更新界面显示"""
#     try:
#         from src.utils.joinquant_login import is_user_logged_in, get_connection_status
#         
#         is_logged_in = is_user_logged_in()
#         
#         # 更新连接状态显示
#         status_display = get_connection_status()
#         
#         # 根据登录状态切换界面显示
#         if is_logged_in:
#             # 已登录：隐藏登录表单，显示连接状态
#             login_form_style = {"display": "none"}
#             connected_status_style = {"display": "block"}
#         else:
#             # 未登录：显示登录表单，隐藏连接状态
#             login_form_style = {"display": "block"}
#             connected_status_style = {"display": "none"}
#         
#         return status_display, login_form_style, connected_status_style
#         
#     except Exception as e:
#         print(f"更新界面状态异常: {e}")
#         # 出错时显示登录表单
#         return "", {"display": "block"}, {"display": "none"}

# 回调函数：获取数据
@app.callback(
    Output("data-status", "children"),
    Input("fetch-data", "n_clicks"),
    State("stock-code", "value"),
    State("start-date", "date"),
    State("end-date", "date"),
    prevent_initial_call=True
)
def fetch_data(n_clicks, stock_code, start_date, end_date):
    if not stock_code or not start_date or not end_date:
        return [dbc.Alert("⚠️ 请输入完整的参数", color="warning", className="mb-0")]
    
    # 检查聚宽连接状态
    try:
        from src.utils.joinquant_login import is_user_logged_in
        if not is_user_logged_in():
            return [dbc.Alert("⚠️ 请先连接聚宽", color="warning", className="mb-0")]
    except Exception as e:
        print(f"检查登录状态失败: {e}")
        return [dbc.Alert("⚠️ 请先连接聚宽", color="warning", className="mb-0")]
    
    # 获取数据提供者
    try:
        from src.utils.joinquant_login import get_data_provider
        data_provider = get_data_provider()
        if not data_provider:
            return [dbc.Alert("⚠️ 聚宽连接异常，请重新登录", color="warning", className="mb-0")]
    except Exception as e:
        print(f"获取数据提供者失败: {e}")
        return [dbc.Alert("⚠️ 聚宽连接异常，请重新登录", color="warning", className="mb-0")]
    
    global current_data
    try:
        current_data = data_provider.get_daily_data(stock_code, start_date, end_date)
        if not current_data.empty:
            return [dbc.Alert(f"✅ 成功获取 {len(current_data)} 条数据", color="success", className="mb-0")]
        else:
            return [dbc.Alert("❌ 获取数据失败", color="danger", className="mb-0")]
    except Exception as e:
        return [dbc.Alert(f"❌ 获取数据异常: {str(e)}", color="danger", className="mb-0")]

# 回调函数：运行回测
@app.callback(
    [Output("backtest-status", "children"),
     Output("backtest-summary", "children"),
     Output("backtest-charts", "children")],
    Input("run-backtest", "n_clicks"),
    State("short-window", "value"),
    State("long-window", "value"),
    State("position-size", "value"),
    State("initial-capital", "value"),
    prevent_initial_call=True
)
def run_backtest(n_clicks, short_window, long_window, position_size, initial_capital):
    if current_data is None:
        return (
            dbc.Alert("⚠️ 请先获取数据", color="warning", className="mb-0"),
            "",
            ""
        )
    
    try:
        # 创建策略
        strategy_params = {
            'short_window': short_window,
            'long_window': long_window,
            'position_size': position_size
        }
        
        strategy = MACrossStrategy(strategy_params)
        
        # 运行回测
        backtest_engine = BacktestEngine(initial_capital=initial_capital)
        results = backtest_engine.run_backtest(strategy, current_data)
        
        if not results:
            return (
                dbc.Alert("❌ 回测失败", color="danger", className="mb-0"),
                "",
                ""
            )
        
        # 生成摘要
        summary = backtest_engine.get_backtest_summary()
        summary_html = dbc.Card([
            dbc.CardHeader([
                html.H5([
                    html.Span(className="fas fa-chart-bar me-2"),
                    "回测摘要"
                ], className="mb-0")
            ], style=custom_css['card-header']),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        dbc.Table([
                            html.Thead([
                                html.Tr([
                                    html.Th("指标", className="fw-bold"),
                                    html.Th("数值", className="fw-bold text-end")
                                ])
                            ]),
                            html.Tbody([
                                html.Tr([
                                    html.Td(k),
                                    html.Td(f"{v:.4f}" if isinstance(v, float) else str(v), 
                                           className="text-end fw-bold")
                                ]) for k, v in summary.items()
                            ])
                        ], striped=True, bordered=True, hover=True, className="table-sm")
                    ])
                ])
            ])
        ], className="mb-3")
        
        # 生成图表
        charts_html = generate_charts(results, current_data)
        
        return (
            dbc.Alert("✅ 回测完成", color="success", className="mb-0"),
            summary_html,
            charts_html
        )
        
    except Exception as e:
        return (
            dbc.Alert(f"❌ 回测异常: {str(e)}", color="danger", className="mb-0"),
            "",
            ""
        )

# 回调函数：数据表格
@app.callback(
    Output("data-table", "children"),
    Input("fetch-data", "n_clicks"),
    prevent_initial_call=True
)
def update_data_table(n_clicks):
    if current_data is None or current_data.empty:
        return [dbc.Alert("⚠️ 暂无数据，请先获取数据", color="info", className="mb-0")]
    
    # 显示前10行数据
    display_data = current_data.head(10)
    
    return [dbc.Card([
        dbc.CardHeader([
            html.H5([
                html.Span(className="fas fa-table me-2"),
                f"数据预览 (显示前{len(display_data)}行)"
            ], className="mb-0")
        ], style=custom_css['card-header']),
        dbc.CardBody([
            dbc.Table.from_dataframe(
                display_data.reset_index(),
                striped=True,
                bordered=True,
                hover=True,
                responsive=True,
                className="table-sm"
            )
        ])
    ])]

# 回调函数：页面加载时自动填充保存的账号密码
@app.callback(
    [Output("jq-username", "value", allow_duplicate=True),
     Output("jq-password", "value", allow_duplicate=True),
     Output("remember-credentials", "value", allow_duplicate=True)],
    Input("connect-jq", "n_clicks"),
    prevent_initial_call='initial_duplicate'
)
def load_saved_credentials(pathname):
    """页面加载时自动填充保存的账号密码"""
    try:
        from src.utils.config_manager import ConfigManager
        
        config_manager = ConfigManager()
        saved_data = config_manager.load_credentials()
        
        if saved_data:
            username = saved_data.get('username', '')
            password = saved_data.get('password', '')
            remember = saved_data.get('remember', False)
            return username, password, remember
        
        return '', '', False
        
    except Exception as e:
        print(f"加载保存的账号信息失败: {e}")
        return '', '', False

# 回调函数：清除保存的账号信息
@app.callback(
    [Output("jq-username", "value", allow_duplicate=True),
     Output("jq-password", "value", allow_duplicate=True),
     Output("remember-credentials", "value", allow_duplicate=True)],
    Input("clear-credentials", "n_clicks"),
    prevent_initial_call=True
)
def clear_saved_credentials(n_clicks):
    """清除保存的账号信息"""
    try:
        from src.utils.config_manager import ConfigManager
        
        config_manager = ConfigManager()
        if config_manager.clear_credentials():
            print("已清除保存的账号信息")
        else:
            print("清除账号信息失败")
        
        return '', '', False
        
    except Exception as e:
        print(f"清除账号信息失败: {e}")
        return '', '', False

# 回调函数：显示/隐藏高级配置区域
@app.callback(
    Output("advanced-config-area", "style"),
    Input("screening-strategy", "value"),
    prevent_initial_call=True
)
def toggle_advanced_config(strategy_type):
    """根据选股策略类型显示/隐藏高级配置区域"""
    if strategy_type in ['advanced_conditions', 'flexible_screening']:
        return {"display": "block"}
    else:
        return {"display": "none"}

# 回调函数：策略选股
@app.callback(
    [Output("screening-status", "children"),
     Output("screening-results", "children")],
    Input("start-screening", "n_clicks"),
    State("screening-strategy", "value"),
    State("min-price", "value"),
    State("max-price", "value"),
    State("exclude-tech-board", "value"),
    State("exclude-st", "value"),
    State("has-limit-up", "value"),
    State("not-limit-up-today", "value"),
    State("not-limit-down-today", "value"),
    State("weekly-kdj-up", "value"),
    State("weekly-macd-up", "value"),
    State("daily-macd-up", "value"),
    State("volume-increasing", "value"),
    prevent_initial_call=True
)
def start_stock_screening(n_clicks, strategy_type, min_price, max_price, 
                         exclude_tech_board, exclude_st, has_limit_up, not_limit_up_today,
                         not_limit_down_today, weekly_kdj_up, weekly_macd_up, 
                         daily_macd_up, volume_increasing):
    if not data_provider or not data_provider.is_connected:
        return (
            dbc.Alert("⚠️ 请先连接聚宽", color="warning", className="mb-0"),
            html.P("请先连接聚宽服务器")
        )
    
    try:
        from src.strategies.stock_screener import StockScreener
        
        # 创建股票筛选器
        screener = StockScreener(data_provider)
        
        # 获取股票列表（这里使用一些示例股票代码）
        sample_stocks = [
            '000001.XSHE', '000002.XSHE', '000858.XSHE', '002415.XSHE', '600000.XSHG',
            '600036.XSHG', '600519.XSHG', '000858.XSHE', '002415.XSHE', '000725.XSHE'
        ]
        
        # 根据策略类型执行选股（优化参数适应短期数据）
        if strategy_type == 'ma_cross':
            results = screener.screen_by_ma_cross(
                sample_stocks, 
                short_window=3,  # 优化：适应短期数据
                long_window=10,  # 优化：适应短期数据
                min_price=min_price or 5.0,
                max_price=max_price or 100.0
            )
        elif strategy_type == 'kdj_macd':
            results = screener.screen_by_kdj_macd(
                sample_stocks,
                min_price=min_price or 5.0,
                max_price=max_price or 100.0
            )
        elif strategy_type == 'volume_breakout':
            results = screener.screen_by_volume_breakout(
                sample_stocks,
                min_price=min_price or 5.0,
                max_price=max_price or 100.0
            )
        elif strategy_type == 'rsi_oversold':
            results = screener.screen_by_rsi_oversold(
                sample_stocks,
                min_price=min_price or 5.0,
                max_price=max_price or 100.0
            )
        elif strategy_type == 'bollinger_bands':
            results = screener.screen_by_bollinger_bands(
                sample_stocks,
                min_price=min_price or 5.0,
                max_price=max_price or 100.0
            )
        elif strategy_type == 'momentum':
            results = screener.screen_by_momentum(
                sample_stocks,
                min_price=min_price or 5.0,
                max_price=max_price or 100.0
            )
        elif strategy_type == 'short_term_ma':
            # 使用短期优化策略
            from src.strategies.short_term_strategies import ShortTermStrategies
            short_term_screener = ShortTermStrategies(data_provider)
            results = short_term_screener.screen_by_short_term_ma(
                sample_stocks,
                min_price=min_price or 5.0,
                max_price=max_price or 100.0
            )
        elif strategy_type == 'short_term_kdj_macd':
            # 使用短期优化策略
            from src.strategies.short_term_strategies import ShortTermStrategies
            short_term_screener = ShortTermStrategies(data_provider)
            results = short_term_screener.screen_by_short_term_kdj_macd(
                sample_stocks,
                min_price=min_price or 5.0,
                max_price=max_price or 100.0
            )
        elif strategy_type == 'short_term_rsi_momentum':
            # 使用短期优化策略
            from src.strategies.short_term_strategies import ShortTermStrategies
            short_term_screener = ShortTermStrategies(data_provider)
            results = short_term_screener.screen_by_rsi_momentum(
                sample_stocks,
                min_price=min_price or 5.0,
                max_price=max_price or 100.0
            )
        elif strategy_type == 'high_frequency_mining':
            # 使用高频数据挖掘策略
            from src.strategies.high_frequency_strategies import HighFrequencyDataMiner
            miner = HighFrequencyDataMiner(data_provider)
            
            # 对每只股票进行深度数据挖掘
            results = []
            for stock_code in sample_stocks[:20]:  # 限制数量，深度分析
                try:
                    mined_data = miner.mine_comprehensive_data(stock_code)
                    if mined_data and mined_data.get('signals'):
                        # 转换为标准格式
                        results.append({
                            'code': stock_code,
                            'name': stock_code,  # 简化处理
                            'price': mined_data['enhanced_data']['close'].iloc[-1] if 'enhanced_data' in mined_data else 0,
                            'strategy': '高频数据挖掘',
                            'signal': '深度分析完成',
                            'data_points': mined_data.get('data_points', 0),
                            'signals_count': len(mined_data.get('signals', [])),
                            'patterns_found': len(mined_data.get('patterns', {}).get('price', [])) + len(mined_data.get('patterns', {}).get('volume', [])),
                            'indicators_count': len(mined_data.get('indicators', {})),
                            'analysis_summary': self._generate_analysis_summary(mined_data)
                        })
                except Exception as e:
                    self.logger.warning(f"高频挖掘失败 {stock_code}: {e}")
                    continue
            
            if not results:
                return (
                    dbc.Alert("⚠️ 高频数据挖掘未找到符合条件的股票", color="warning", className="mb-0"),
                    html.P("请尝试调整参数或选择其他策略")
                )
        
        elif strategy_type == 'dual_strategy':
            results = screener.screen_by_dual_strategy(
                sample_stocks,
                strategy1='ma_cross',
                strategy2='rsi_oversold',
                min_price=min_price or 5.0,
                max_price=max_price or 100.0
            )
        elif strategy_type == 'industry_rotation':
            results = screener.screen_by_industry_rotation(
                min_price=min_price or 5.0,
                max_price=max_price or 100.0
            )
        elif strategy_type == 'advanced_conditions':
            # 高级复合选股策略
            from src.strategies.advanced_screener import AdvancedStockScreener
            advanced_screener = AdvancedStockScreener(data_provider)
            results = advanced_screener.screen_by_advanced_conditions(
                sample_stocks,
                min_price=min_price or 5.0,
                max_price=max_price or 100.0
            )
        elif strategy_type == 'flexible_screening':
            # 灵活选股策略
            from src.strategies.flexible_screener import FlexibleStockScreener
            flexible_screener = FlexibleStockScreener(data_provider)
            
            # 构建条件字典
            conditions = {
                'exclude_tech_board': exclude_tech_board or False,
                'exclude_st': exclude_st or False,
                'has_limit_up': has_limit_up or False,
                'not_limit_up_today': not_limit_up_today or False,
                'not_limit_down_today': not_limit_down_today or False,
                'weekly_kdj_up': weekly_kdj_up or False,
                'weekly_macd_up': weekly_macd_up or False,
                'daily_macd_up': daily_macd_up or False,
                'volume_increasing': volume_increasing or False
            }
            
            results = flexible_screener.screen_by_selected_conditions(
                sample_stocks,
                conditions,
                min_price=min_price or 5.0,
                max_price=max_price or 100.0
            )
        else:
            return (
                dbc.Alert("⚠️ 未知策略类型", color="warning", className="mb-0"),
                html.P("请选择有效的选股策略")
            )
        
        if not results:
            return (
                dbc.Alert("⚠️ 未找到符合条件的股票", color="warning", className="mb-0"),
                html.P("请尝试调整参数或选择其他策略")
            )
        
        # 生成结果表格
        results_df = pd.DataFrame(results)
        
        # 为每只股票添加"加入自选"按钮
        def create_stock_row(row_data):
            stock_code = row_data.get('code', 'N/A')
            stock_name = row_data.get('name', 'N/A')
            return html.Tr([
                html.Td(stock_code),
                html.Td(stock_name),
                html.Td(f"{row_data.get('price', 0):.2f}"),
                html.Td(f"{row_data.get('change_pct', 0):.2f}%"),
                html.Td(f"{row_data.get('volume', 0):,.0f}"),
                html.Td(
                    dbc.Button(
                        "⭐ 加入自选",
                        id={"type": "add-watchlist", "index": stock_code},
                        color="warning",
                        size="sm",
                        className="me-1"
                    )
                )
            ])
        
        # 创建自定义表格
        custom_table = dbc.Table([
            html.Thead([
                html.Tr([
                    html.Th("股票代码"),
                    html.Th("股票名称"),
                    html.Th("当前价格"),
                    html.Th("涨跌幅"),
                    html.Th("成交量"),
                    html.Th("操作")
                ])
            ]),
            html.Tbody([
                create_stock_row(row) for _, row in results_df.iterrows()
            ])
        ], striped=True, bordered=True, hover=True, className="table-sm")
        
        results_table = dbc.Card([
            dbc.CardHeader([
                html.H6([
                    html.Span("📋", className="me-2"),
                    "选股结果详情"
                ], className="mb-0")
            ], style={'background': 'linear-gradient(135deg, #17a2b8 0%, #138496 100%)', 'color': 'white'}),
            dbc.CardBody([
                custom_table
            ])
        ], className="mt-3")
        
        # 添加自选股管理区域
        watchlist_section = dbc.Card([
            dbc.CardHeader([
                html.H6([
                    html.Span("⭐", className="me-2"),
                    "自选股管理"
                ], className="mb-0")
            ], style={'background': 'linear-gradient(135deg, #ffc107 0%, #fd7e14 100%)', 'color': 'white'}),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        dbc.Button([
                            html.Span("🗑️", className="me-2"),
                            "清空自选股"
                        ], id="clear-watchlist", color="danger", size="sm", className="me-2"),
                        dbc.Button([
                            html.Span("📥", className="me-2"),
                            "导出自选股"
                        ], id="export-watchlist", color="info", size="sm", className="me-2")
                    ], width=6),
                    dbc.Col([
                        html.Div(id="watchlist-status", className="text-end")
                    ], width=6)
                ]),
                html.Hr(),
                html.Div(id="watchlist-display"),
                # 移除操作状态显示
                html.Div(id="remove-status", className="mt-2"),
                # 虚拟输入元素，用于处理空自选股的情况
                html.Div(id="dummy-remove", style={"display": "none"})
            ])
        ], className="mt-3")
        
        # 生成结果摘要
        strategy_name = results[0]['strategy'] if results else '未知'
        summary = dbc.Card([
            dbc.CardHeader([
                html.H5([
                    html.Span("📊", className="me-2"),
                    f"选股结果 - {len(results)} 只股票"
                ], className="mb-0")
            ], style=custom_css['card-header']),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H6("策略类型", className="text-muted mb-2"),
                                html.H5(strategy_name, className="text-primary mb-0")
                            ])
                        ], className="text-center border-0 shadow-sm")
                    ], width=4),
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H6("价格范围", className="text-muted mb-2"),
                                html.H5(f"{min_price or 5.0} - {max_price or 100.0}", className="text-success mb-0")
                            ])
                        ], className="text-center border-0 shadow-sm")
                    ], width=4),
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H6("筛选数量", className="text-muted mb-2"),
                                html.H5(f"{len(results)} 只", className="text-info mb-0")
                            ])
                        ], className="text-center border-0 shadow-sm")
                    ], width=4)
                ], className="mb-4"),
                
                # 如果是灵活选股策略，显示满足的条件
                html.Div([
                    html.H6([
                        html.Span("✅", className="me-2"),
                        "满足的条件"
                    ], className="mt-3 mb-3 text-success"),
                    dbc.Row([
                        dbc.Col([
                            html.Ul([
                                html.Li([
                                    html.Span("✅", className="me-2"),
                                    condition
                                ], className="mb-2") for condition in results[0].get('conditions_met', [])
                            ]) if results and 'conditions_met' in results[0] else html.P("无特殊条件", className="text-muted")
                        ])
                    ])
                ]) if strategy_type == 'flexible_screening' else html.Div(),
                
                results_table,
                watchlist_section
            ])
        ], className="mb-3")
        
        return (
            dbc.Alert("✅ 选股完成，找到 {len(results)} 只股票", color="success", className="mb-0"),
            summary
        )
        
    except Exception as e:
        logging.error(f"选股失败: {e}")
        return (
            dbc.Alert(f"❌ 选股失败: {str(e)}", color="danger", className="mb-0"),
            html.P(f"选股过程中发生错误: {str(e)}")
        )

def generate_charts(results, data):
    """生成回测图表"""
    if not results or 'equity_curve' not in results:
        return html.P("暂无图表数据")
    
    try:
        # 权益曲线
        equity_df = pd.DataFrame(results['equity_curve'])
        if not equity_df.empty:
            equity_df.set_index('timestamp', inplace=True)
            
            # 创建子图
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=('权益曲线', '价格和均线', '交易信号', '收益率分布'),
                specs=[[{"secondary_y": False}, {"secondary_y": False}],
                       [{"secondary_y": False}, {"secondary_y": False}]]
            )
            
            # 权益曲线
            fig.add_trace(
                go.Scatter(x=equity_df.index, y=equity_df['equity'], 
                          mode='lines', name='权益'),
                row=1, col=1
            )
            
            # 价格和均线
            if 'close' in data.columns:
                fig.add_trace(
                    go.Scatter(x=data.index, y=data['close'], 
                              mode='lines', name='收盘价'),
                    row=1, col=2
                )
            
            # 交易信号
            if 'signal' in data.columns:
                buy_signals = data[data['signal'] == 1]
                sell_signals = data[data['signal'] == -1]
                
                if not buy_signals.empty:
                    fig.add_trace(
                        go.Scatter(x=buy_signals.index, y=buy_signals['close'],
                                  mode='markers', name='买入信号',
                                  marker=dict(color='red', symbol='triangle-up')),
                        row=2, col=1
                    )
                
                if not sell_signals.empty:
                    fig.add_trace(
                        go.Scatter(x=sell_signals.index, y=sell_signals['close'],
                                  mode='markers', name='卖出信号',
                                  marker=dict(color='green', symbol='triangle-down')),
                        row=2, col=1
                    )
            
            # 收益率分布
            if 'returns' in data.columns:
                returns = data['returns'].dropna()
                fig.add_trace(
                    go.Histogram(x=returns, name='收益率分布'),
                    row=2, col=2
                )
            
            fig.update_layout(height=600, showlegend=True)
            
            return dcc.Graph(figure=fig)
        
    except Exception as e:
        logging.error(f"生成图表失败: {e}")
        return html.P(f"生成图表失败: {str(e)}")
    
    return html.P("暂无图表数据")

# 回调函数：获取板块涨幅数据
@app.callback(
    [Output("sector-performance-results", "children"),
     Output("concept-performance-results", "children"),
     Output("sector-loading-status", "children")],
    Input("refresh-sectors", "n_clicks"),
    prevent_initial_call=True
)
def refresh_sector_performance(n_clicks):
    """刷新板块涨幅数据"""
    if not data_provider or not data_provider.is_connected:
        return (
            dbc.Alert("⚠️ 请先连接聚宽", color="warning", className="mb-0"),
            dbc.Alert("⚠️ 请先连接聚宽", color="warning", className="mb-0"),
            dbc.Alert("❌ 未连接聚宽", color="danger", className="mb-0")
        )
    
    try:
        # 获取申万行业涨幅
        sector_data = data_provider.get_sector_performance()
        
        # 获取概念板块涨幅
        concept_data = data_provider.get_concept_performance()
        
        # 生成申万行业表格
        if not sector_data.empty:
            sector_table = dbc.Card([
                dbc.CardHeader([
                    html.H6([
                        html.Span(className="fas fa-industry me-2"),
                        "申万行业涨幅排行 (前20名)"
                    ], className="mb-0")
                ], style={'background': 'linear-gradient(135deg, #28a745 0%, #20c997 100%)', 'color': 'white'}),
                dbc.CardBody([
                    dbc.Table([
                        html.Thead([
                            html.Tr([
                                html.Th("排名", className="text-center"),
                                html.Th("行业名称"),
                                html.Th("涨跌幅(%)", className="text-center"),
                                html.Th("开盘价", className="text-center"),
                                html.Th("收盘价", className="text-center"),
                                html.Th("成交量", className="text-center")
                            ])
                        ]),
                        html.Tbody([
                            html.Tr([
                                html.Td(f"{i+1}", className="text-center fw-bold"),
                                html.Td(row['name'], className="fw-bold"),
                                html.Td(f"{row['change_pct']:.2f}%", 
                                       className="text-center fw-bold",
                                       style={'color': 'red' if row['change_pct'] > 0 else 'green'}),
                                html.Td(f"{row['open']:.2f}", className="text-center"),
                                html.Td(f"{row['close']:.2f}", className="text-center"),
                                html.Td(f"{row['volume']:,.0f}", className="text-center")
                            ]) for i, (_, row) in enumerate(sector_data.head(20).iterrows())
                        ])
                    ], striped=True, bordered=True, hover=True, className="table-sm")
                ])
            ], className="mb-3")
        else:
            sector_table = dbc.Alert("⚠️ 暂无申万行业数据", color="info", className="mb-0")
        
        # 生成概念板块表格
        if not concept_data.empty:
            concept_table = dbc.Card([
                dbc.CardHeader([
                    html.H6([
                        html.Span(className="fas fa-lightbulb me-2"),
                        "概念板块涨幅排行 (前20名)"
                    ], className="mb-0")
                ], style={'background': 'linear-gradient(135deg, #ffc107 0%, #fd7e14 100%)', 'color': 'white'}),
                dbc.CardBody([
                    dbc.Table([
                        html.Thead([
                            html.Tr([
                                html.Th("排名", className="text-center"),
                                html.Th("概念名称"),
                                html.Th("涨跌幅(%)", className="text-center"),
                                html.Th("成分股数量", className="text-center")
                            ])
                        ]),
                        html.Tbody([
                            html.Tr([
                                html.Td(f"{i+1}", className="text-center fw-bold"),
                                html.Td(row['name'], className="fw-bold"),
                                html.Td(f"{row['change_pct']:.2f}%", 
                                       className="text-center fw-bold",
                                       style={'color': 'red' if row['change_pct'] > 0 else 'green'}),
                                html.Td(row['stock_count'], className="text-center")
                            ]) for i, (_, row) in enumerate(concept_data.head(20).iterrows())
                        ])
                    ], striped=True, bordered=True, hover=True, className="table-sm")
                ])
            ], className="mb-3")
        else:
            concept_table = dbc.Alert("⚠️ 暂无概念板块数据", color="info", className="mb-0")
        
        status = dbc.Alert("✅ 板块数据刷新成功", color="success", className="mb-0")
        
        return sector_table, concept_table, status
        
    except Exception as e:
        error_msg = f"获取板块数据失败: {str(e)}"
        logging.error(error_msg)
        return (
            dbc.Alert(f"❌ {error_msg}", color="danger", className="mb-0"),
            dbc.Alert(f"❌ {error_msg}", color="danger", className="mb-0"),
            dbc.Alert(f"❌ {error_msg}", color="danger", className="mb-0")
        )

# 自选股管理回调函数
@app.callback(
    Output("watchlist-status", "children"),
    [Input({"type": "add-watchlist", "index": dash.ALL}, "n_clicks"),
     Input("clear-watchlist", "n_clicks"),
     Input("export-watchlist", "n_clicks")],
    prevent_initial_call=True
)
def manage_watchlist(add_clicks, clear_clicks, export_clicks):
    global watchlist
    
    ctx = callback_context
    if not ctx.triggered:
        return ""
    
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    # 调试信息
    print(f"=== 自选股管理调试信息 ===")
    print(f"触发ID: {trigger_id}")
    print(f"完整触发信息: {ctx.triggered[0]}")
    print(f"==========================")
    
    if trigger_id == "clear-watchlist":
        # 清空自选股
        watchlist.clear()
        
        # 保存到本地文件（清空后的空列表）
        try:
            from src.utils.config_manager import ConfigManager
            config_manager = ConfigManager()
            if config_manager.clear_watchlist():
                print("自选股已清空，本地文件也已清除")
            else:
                print("自选股清空后清除本地文件失败")
        except Exception as e:
            print(f"清除自选股本地文件失败: {e}")
        
        return dbc.Alert("🗑️ 自选股已清空", color="warning", className="mb-0")
    
    elif trigger_id == "export-watchlist":
        # 导出自选股
        if not watchlist:
            return dbc.Alert("⚠️ 暂无自选股可导出", color="warning", className="mb-0")
        
        # 创建CSV数据
        csv_data = "股票代码,股票名称,添加时间\n"
        for stock in watchlist:
            csv_data += f"{stock['code']},{stock['name']},{stock['added_time']}\n"
        
        # 创建下载链接
        download_link = html.A(
            "📥 下载自选股列表",
            href=f"data:text/csv;charset=utf-8,{csv_data}",
            download="自选股列表.csv",
            className="btn btn-info btn-sm"
        )
        
        return dbc.Alert("📥 自选股导出成功", color="success", className="mb-0")
    
    else:
        # 添加自选股
        try:
            # 解析股票代码
            stock_code = None
            
            # 检查是否是新的按钮ID格式
            if trigger_id.startswith('add-watchlist-'):
                stock_code = trigger_id.replace('add-watchlist-', '')
                print(f"新格式按钮ID解析成功: {stock_code}")
            else:
                # 兼容旧的格式
                try:
                    button_data = json.loads(trigger_id)
                    if button_data.get('type') == 'add-watchlist':
                        stock_code = button_data.get('index')
                        print(f"旧格式JSON解析成功: {stock_code}")
                except:
                    # 尝试直接提取股票代码
                    code_match = re.search(r'(\d{6})', trigger_id)
                    if code_match:
                        stock_code = code_match.group(1)
                        print(f"正则表达式提取成功: {stock_code}")
            
            print(f"最终解析出的股票代码: {stock_code}")
            
            if stock_code:
                # 检查是否已经在自选股中
                if any(stock['code'] == stock_code for stock in watchlist):
                    return dbc.Alert(f"⚠️ {stock_code} 已在自选股中", color="warning", className="mb-0")
                
                # 添加到自选股
                stock_info = {
                    'code': stock_code,
                    'name': f"股票{stock_code}",  # 这里可以根据实际数据获取股票名称
                    'added_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                watchlist.append(stock_info)
                
                # 保存到本地文件
                try:
                    from src.utils.config_manager import ConfigManager
                    config_manager = ConfigManager()
                    if config_manager.save_watchlist(watchlist):
                        print("自选股已添加，已保存到本地")
                    else:
                        print("自选股添加后保存到本地失败")
                except Exception as e:
                    print(f"保存自选股失败: {e}")
                
                return dbc.Alert(f"⭐ {stock_code} 已添加到自选股", color="success", className="mb-0")
            else:
                return dbc.Alert(f"⚠️ 无法解析股票代码，触发ID: {trigger_id}", color="warning", className="mb-0")
            
        except Exception as e:
            print(f"添加自选股异常: {e}")
            return dbc.Alert(f"❌ 添加自选股失败: {str(e)}", color="danger", className="mb-0")

# 移除自选股回调函数 - 使用模式匹配回调
@app.callback(
    [Output("remove-status", "children"),
     Output("watchlist-display", "children", allow_duplicate=True)],
    [Input({"type": "remove-watchlist-btn", "index": dash.ALL}, "n_clicks")],
    prevent_initial_call=True
)
def remove_from_watchlist(*remove_clicks):
    global watchlist
    
    ctx = callback_context
    if not ctx.triggered:
        return "", dash.no_update
    
    try:
        trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
        trigger_value = ctx.triggered[0]['value']
        
        # 调试信息
        print(f"=== 移除自选股调试信息 ===")
        print(f"移除触发ID: {trigger_id}")
        print(f"触发值: {trigger_value}")
        print(f"完整触发信息: {ctx.triggered[0]}")
        print(f"==========================")
        
        # 检查是否是有效的移除操作（n_clicks > 0）
        if trigger_value is None or trigger_value <= 0:
            print(f"无效的移除操作，n_clicks值: {trigger_value}")
            return "", dash.no_update
        
        # 解析股票代码 - 从按钮ID中提取
        if isinstance(trigger_id, str) and trigger_id.startswith('{"index":"'):
            # 解析JSON格式的ID - 兼容当前的按钮ID格式
            try:
                import json
                id_data = json.loads(trigger_id)
                stock_code = id_data.get('index')
                print(f"从JSON ID解析成功: {stock_code}")
            except json.JSONDecodeError:
                print(f"JSON解析失败: {trigger_id}")
                stock_code = None
        elif isinstance(trigger_id, str) and trigger_id.startswith('{"type":"remove-watchlist-btn","index":"'):
            # 兼容旧的格式
            try:
                import json
                id_data = json.loads(trigger_id)
                stock_code = id_data.get('index')
                print(f"从旧格式JSON ID解析成功: {stock_code}")
            except json.JSONDecodeError:
                print(f"旧格式JSON解析失败: {trigger_id}")
                stock_code = None
        else:
            print(f"无法解析按钮ID: {trigger_id}")
            stock_code = None
        
        print(f"移除解析出的股票代码: {stock_code}")
        
        if stock_code:
            # 从自选股中移除
            original_count = len(watchlist)
            watchlist = [stock for stock in watchlist if stock['code'] != stock_code]
            removed_count = original_count - len(watchlist)
            
            if removed_count > 0:
                # 保存到本地文件
                try:
                    from src.utils.config_manager import ConfigManager
                    config_manager = ConfigManager()
                    if config_manager.save_watchlist(watchlist):
                        print("自选股已移除，已保存到本地")
                    else:
                        print("自选股移除后保存到本地失败")
                except Exception as e:
                    print(f"保存自选股失败: {e}")
                
                # 显示移除成功消息并更新列表
                return (
                    dbc.Alert(f"❌ {stock_code} 已从自选股中移除", color="info", className="mb-0"),
                    display_watchlist()
                )
            else:
                print(f"未找到股票代码: {stock_code}")
                return (
                    dbc.Alert(f"⚠️ 未找到股票代码: {stock_code}", color="warning", className="mb-0"),
                    dash.no_update
                )
        else:
            print("无效的股票代码")
            return (
                dbc.Alert("⚠️ 无效的股票代码", color="warning", className="mb-0"),
                dash.no_update
            )
        
    except Exception as e:
        print(f"移除自选股失败: {e}")
        return (
            dbc.Alert(f"❌ 移除自选股失败: {str(e)}", color="danger", className="mb-0"),
            dash.no_update
        )

# 统一更新自选股显示的回调函数
@app.callback(
    Output("watchlist-display", "children"),
    [Input("watchlist-status", "children"),
     Input("remove-status", "children")],
    prevent_initial_call=True
)
def update_watchlist_display(status_children, remove_status_children):
    """当自选股状态发生变化时，更新显示"""
    return display_watchlist()

def display_watchlist():
    """显示自选股列表"""
    global watchlist
    
    if not watchlist:
        return html.P("暂无自选股", className="text-muted")
    
    # 创建自选股表格
    watchlist_table = dbc.Table([
        html.Thead([
            html.Tr([
                html.Th("股票代码"),
                html.Th("股票名称"),
                html.Th("添加时间"),
                html.Th("操作")
            ])
        ]),
        html.Tbody([
            html.Tr([
                html.Td(stock['code']),
                html.Td(stock['name']),
                html.Td(stock['added_time']),
                html.Td(
                    dbc.Button(
                        "❌ 移除",
                        id={"type": "remove-watchlist-btn", "index": stock['code']},  # 使用模式匹配ID格式
                        color="danger",
                        size="sm"
                    )
                )
            ]) for stock in watchlist
        ])
    ], striped=True, bordered=True, hover=True, className="table-sm")
    
    return watchlist_table

# 页面加载时自动加载保存的自选股
@app.callback(
    Output("watchlist-display", "children", allow_duplicate=True),
    Input("_pages_location", "pathname"),
    prevent_initial_call='initial_duplicate'
)
def load_saved_watchlist(pathname):
    """页面加载时自动加载保存的自选股"""
    global watchlist
    
    try:
        from src.utils.config_manager import ConfigManager
        
        config_manager = ConfigManager()
        saved_watchlist = config_manager.load_watchlist()
        
        if saved_watchlist:
            watchlist.clear()
            watchlist.extend(saved_watchlist)
            print(f"成功加载 {len(saved_watchlist)} 只自选股")
        else:
            print("没有找到保存的自选股")
            
    except Exception as e:
        print(f"加载自选股失败: {e}")
    
    return display_watchlist()

# 银河证券回调函数

@app.callback(
    Output("galaxy-connection-status", "children"),
    Input("connect-galaxy", "n_clicks"),
    [State("galaxy-account", "value"),
     State("galaxy-password", "value"),
     State("galaxy-server", "value"),
     State("galaxy-remember", "value")],
    prevent_initial_call=True
)
def connect_galaxy_securities(n_clicks, account, password, server, remember):
    """连接银河证券服务器"""
    if not n_clicks:
        return ""
        
    try:
        if not account or not password:
            return dbc.Alert("⚠️ 请输入资金账号和交易密码", color="warning", className="mb-0")
        
        print(f"=== 连接银河证券 ===")
        print(f"账号: {account}")
        print(f"服务器: {server}")
        print(f"记住账号: {remember}")
        
        # 导入银河证券模块
        from src.trading.brokers.galaxy_securities import GalaxySecuritiesBroker
        
        # 创建配置
        config = {
            'account': account,
            'password': password,
            'server_url': server
        }
        
        # 创建交易接口实例
        global galaxy_broker
        galaxy_broker = GalaxySecuritiesBroker(config)
        
        # 尝试连接
        if galaxy_broker.connect():
            print("银河证券连接成功")
            return dbc.Alert("✅ 银河证券连接成功", color="success", className="mb-0")
        else:
            print("银河证券连接失败")
            return dbc.Alert("❌ 银河证券连接失败", color="danger", className="mb-0")
            
    except Exception as e:
        print(f"连接银河证券异常: {e}")
        return dbc.Alert(f"❌ 连接异常: {str(e)}", color="danger", className="mb-0")

@app.callback(
    Output("galaxy-account-info", "children"),
    Input("connect-galaxy", "n_clicks"),
    prevent_initial_call=True
)
def update_galaxy_account_info(n_clicks):
    """更新银河证券账户信息"""
    if not n_clicks:
        return "请先连接银河证券服务器"
        
    try:
        if 'galaxy_broker' not in globals() or not galaxy_broker.is_connected:
            return dbc.Alert("请先连接银河证券服务器", color="warning", className="mb-0")
        
        # 获取账户信息
        account_info = galaxy_broker.get_account_info()
        
        if 'error' in account_info:
            return dbc.Alert(f"获取账户信息失败: {account_info['error']}", color="danger", className="mb-0")
        
        # 显示账户信息
        return dbc.Card([
            dbc.CardBody([
                html.H6("账户概览", className="text-primary mb-3"),
                dbc.Row([
                    dbc.Col([
                        html.Div([
                            html.Small("总资产", className="text-muted"),
                            html.H5(f"¥{account_info['total_assets']:,.2f}", className="text-success mb-0")
                        ])
                    ], width=4),
                    dbc.Col([
                        html.Div([
                            html.Small("可用资金", className="text-muted"),
                            html.H5(f"¥{account_info['available_cash']:,.2f}", className="text-info mb-0")
                        ])
                    ], width=4),
                    dbc.Col([
                        html.Div([
                            html.Small("市值", className="text-muted"),
                            html.H5(f"¥{account_info['market_value']:,.2f}", className="text-warning mb-0")
                        ])
                    ], width=4)
                ], className="mb-3"),
                dbc.Row([
                    dbc.Col([
                        html.Div([
                            html.Small("总盈亏", className="text-muted"),
                            html.H6(f"¥{account_info['total_profit']:,.2f}", 
                                   className="text-success" if account_info['total_profit'] >= 0 else "text-danger")
                        ])
                    ], width=6),
                    dbc.Col([
                        html.Div([
                            html.Small("当日盈亏", className="text-muted"),
                            html.H6(f"¥{account_info['today_profit']:,.2f}", 
                                   className="text-success" if account_info['today_profit'] >= 0 else "text-danger")
                        ])
                    ], width=6)
                ])
            ])
        ], style=custom_css['info-card'])
        
    except Exception as e:
        print(f"获取账户信息失败: {e}")
        return dbc.Alert(f"❌ 获取账户信息失败: {str(e)}", color="danger", className="mb-0")

@app.callback(
    Output("galaxy-positions", "children"),
    Input("connect-galaxy", "n_clicks"),
    prevent_initial_call=True
)
def update_galaxy_positions(n_clicks):
    """更新银河证券持仓信息"""
    if not n_clicks:
        return "请先连接银河证券服务器"
        
    try:
        if 'galaxy_broker' not in globals() or not galaxy_broker.is_connected:
            return dbc.Alert("请先连接银河证券服务器", color="warning", className="mb-0")
        
        # 获取持仓信息
        positions = galaxy_broker.get_positions()
        
        if not positions:
            return html.Div("暂无持仓", className="text-muted text-center")
        
        # 创建持仓表格
        return dbc.Table([
            html.Thead([
                html.Tr([
                    html.Th("股票代码"),
                    html.Th("股票名称"),
                    html.Th("持仓数量"),
                    html.Th("成本价"),
                    html.Th("当前价"),
                    html.Th("盈亏"),
                    html.Th("操作")
                ])
            ]),
            html.Tbody([
                html.Tr([
                    html.Td(pos['stock_code']),
                    html.Td(pos['stock_name']),
                    html.Td(f"{pos['quantity']:,}"),
                    html.Td(f"¥{pos['avg_cost']:.2f}"),
                    html.Td(f"¥{pos['current_price']:.2f}"),
                    html.Td([
                        html.Span(f"¥{pos['profit_loss']:,.2f}", 
                                 className="text-success" if pos['profit_loss'] >= 0 else "text-danger"),
                        html.Br(),
                        html.Small(f"{pos['profit_loss_ratio']:.2f}%", 
                                  className="text-success" if pos['profit_loss_ratio'] >= 0 else "text-danger")
                    ]),
                    html.Td([
                        dbc.Button("卖出", size="sm", color="danger", 
                                  id=f"sell-{pos['stock_code'].replace('.', '_')}")
                    ])
                ]) for pos in positions
            ])
        ], bordered=True, hover=True, responsive=True, striped=True)
        
    except Exception as e:
        print(f"获取持仓信息失败: {e}")
        return dbc.Alert(f"❌ 获取持仓信息失败: {str(e)}", color="danger", className="mb-0")

@app.callback(
    Output("galaxy-orders", "children"),
    Input("connect-galaxy", "n_clicks"),
    prevent_initial_call=True
)
def update_galaxy_orders(n_clicks):
    """更新银河证券订单信息"""
    if not n_clicks:
        return "请先连接银河证券服务器"
        
    try:
        if 'galaxy_broker' not in globals() or not galaxy_broker.is_connected:
            return dbc.Alert("请先连接银河证券服务器", color="warning", className="mb-0")
        
        # 获取订单信息
        orders = galaxy_broker.get_orders()
        
        if not orders:
            return html.Div("暂无订单", className="text-muted text-center")
        
        # 创建订单表格
        return dbc.Table([
            html.Thead([
                html.Tr([
                    html.Th("订单ID"),
                    html.Th("股票代码"),
                    html.Th("类型"),
                    html.Th("数量"),
                    html.Th("价格"),
                    html.Th("状态"),
                    html.Th("操作")
                ])
            ]),
            html.Tbody([
                html.Tr([
                    html.Td(order['order_id']),
                    html.Td(order['stock_code']),
                    html.Td([
                        html.Span(order['order_type'], 
                                 className="badge bg-success" if order['order_type'] == 'buy' else "badge bg-danger")
                    ]),
                    html.Td(f"{order['order_quantity']:,}"),
                    html.Td(f"¥{order['order_price']:.2f}"),
                    html.Td([
                        html.Span(order['order_status'], 
                                 className="badge bg-primary" if order['order_status'] == 'pending' else 
                                         "badge bg-success" if order['order_status'] == 'filled' else "badge bg-secondary")
                    ]),
                    html.Td([
                        dbc.Button("撤单", size="sm", color="warning", 
                                  id={"type": "cancel-order", "index": order['order_id']})
                        if order['order_status'] == 'pending' else html.Span("-")
                    ])
                ]) for order in orders
            ])
        ], bordered=True, hover=True, responsive=True, striped=True)
        
    except Exception as e:
        print(f"获取订单信息失败: {e}")
        return dbc.Alert(f"❌ 获取订单信息失败: {str(e)}", color="danger", className="mb-0")

# 全局变量
galaxy_broker = None

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=8051)
