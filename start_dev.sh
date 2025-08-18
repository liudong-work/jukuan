#!/bin/bash

# 开发模式启动脚本 - 支持热更新
echo "🚀 启动聚宽量化交易系统 v2.0.0 (开发模式)"
echo "🔄 热更新已启用 - 修改代码后自动重启"
echo ""

# 激活虚拟环境
source .venv/bin/activate

# 启动开发服务器
python run_dev.py
