#!/bin/bash

# 量化交易系统 v2.0.0 启动脚本

echo "🚀 启动量化交易系统 v2.0.0..."

# 检查虚拟环境
if [ ! -d ".venv" ]; then
    echo "❌ 虚拟环境不存在，请先创建虚拟环境"
    exit 1
fi

# 激活虚拟环境
echo "📦 激活虚拟环境..."
source .venv/bin/activate

# 检查依赖
echo "🔍 检查依赖..."
pip list | grep -q fastapi || {
    echo "❌ FastAPI未安装，正在安装依赖..."
    pip install -r requirements.txt
}

# 检查端口占用
echo "🔍 检查端口8000..."
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null ; then
    echo "⚠️  端口8000被占用，正在停止现有进程..."
    lsof -ti:8000 | xargs kill -9
    sleep 2
fi

# 启动服务
echo "🚀 启动Web服务..."
echo "📍 服务地址: http://localhost:8000"
echo "📚 API文档: http://localhost:8000/docs"
echo "🔍 系统状态: http://localhost:8000/health"
echo ""
echo "按 Ctrl+C 停止服务"
echo ""

python main.py
