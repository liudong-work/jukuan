#!/bin/bash

echo "🚀 启动量化交易系统 v2.0.2 Web服务"
echo "=================================="

# 激活虚拟环境
echo "📦 激活虚拟环境..."
source .venv/bin/activate

# 检查依赖
echo "🔍 检查依赖..."
if ! python -c "import fastapi" 2>/dev/null; then
    echo "❌ FastAPI未安装，正在安装..."
    pip install -r requirements.txt
fi

# 检查端口占用
echo "🔌 检查端口占用..."
if lsof -ti:8000 >/dev/null 2>&1; then
    echo "⚠️  端口8000被占用，正在释放..."
    lsof -ti:8000 | xargs kill -9
    sleep 2
fi

# 启动服务
echo "🌟 启动Web服务..."
echo "📍 服务地址: http://localhost:8000"
echo "📊 实时监控: http://localhost:8000/dashboard"
echo "📈 股票表格: http://localhost:8000/stock-table"
echo "💼 交易管理: http://localhost:8000/trading"
echo "🤖 策略管理: http://localhost:8000/strategy"
echo "📚 API文档: http://localhost:8000/docs"
echo ""
echo "按 Ctrl+C 停止服务"
echo "=================================="

# 启动服务
python run_dev.py
