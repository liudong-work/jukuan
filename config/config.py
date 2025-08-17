"""
系统配置文件
"""

import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 聚宽配置
JQ_USERNAME = os.getenv('JQ_USERNAME', '')
JQ_PASSWORD = os.getenv('JQ_PASSWORD', '')
JQ_TOKEN = os.getenv('JQ_TOKEN', '')

# 数据库配置
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///jukuan.db')

# 日志配置
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# 回测配置
DEFAULT_INITIAL_CAPITAL = 1000000
DEFAULT_COMMISSION_RATE = 0.0003  # 手续费率
DEFAULT_SLIPPAGE_RATE = 0.0001    # 滑点率

# 策略参数默认值
DEFAULT_MA_SHORT_WINDOW = 5
DEFAULT_MA_LONG_WINDOW = 20
DEFAULT_POSITION_SIZE = 0.1

# Web应用配置
WEB_HOST = os.getenv('WEB_HOST', '0.0.0.0')
WEB_PORT = int(os.getenv('WEB_PORT', 8050))
WEB_DEBUG = os.getenv('WEB_DEBUG', 'True').lower() == 'true'
