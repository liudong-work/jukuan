#!/bin/bash

echo "🚀 启动量化交易系统实时监控..."

# 检查端口是否被占用
if lsof -i :8000 > /dev/null 2>&1; then
    echo "✅ 服务器已在运行 (端口 8000)"
else
    echo "🔄 启动开发服务器..."
    /usr/local/opt/python@3.11/bin/python3.11 run_dev.py &
    sleep 5
fi

# 启动实时监控
echo "🔄 启动实时监控系统..."
curl -s -X POST "http://localhost:8000/api/v1/monitoring/start" > /dev/null

# 检查监控状态
echo "📊 检查监控状态..."
sleep 2
curl -s "http://localhost:8000/api/v1/monitoring/status" | /usr/local/opt/python@3.11/bin/python3.11 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    if data['status'] == 'success':
        status = data['data']
        print(f'✅ 监控系统状态:')
        print(f'   运行状态: {status[\"is_running\"]}')
        print(f'   风险告警: {status[\"risk_alerts_count\"]}')
        print(f'   性能告警: {status[\"performance_alerts_count\"]}')
        print(f'   系统告警: {status[\"system_alerts_count\"]}')
        print(f'   最后更新: {status[\"last_update\"]}')
    else:
        print('❌ 监控状态获取失败')
except:
    print('❌ 无法解析监控状态')
"

echo ""
echo "🌐 访问地址:"
echo "   主页: http://localhost:8000"
echo "   实时监控: http://localhost:8000/realtime-monitor"
echo "   ML策略: http://localhost:8000/ml-strategy"
echo "   实时数据: http://localhost:8000/realtime-data"
echo ""
echo "🎉 系统启动完成！"
