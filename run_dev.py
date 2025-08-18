#!/usr/bin/env python3
"""
开发模式启动脚本 - 支持热更新
"""

import uvicorn
import os
import sys

if __name__ == "__main__":
    # 开发模式配置
    config = {
        "app": "main:app",
        "host": "0.0.0.0",
        "port": 8000,
        "reload": True,  # 启用热更新
        "reload_dirs": ["./"],  # 监控整个项目目录
        "reload_excludes": [
            "*.pyc",
            "__pycache__",
            ".git",
            ".venv",
            "cache",
            "*.log"
        ],
        "log_level": "info",
        "access_log": True,
        "workers": 1
    }
    
    print("🚀 启动开发服务器 (热更新模式)")
    print(f"📍 地址: http://localhost:{config['port']}")
    print("🔄 热更新已启用 - 修改代码后自动重启")
    print("⏹️  按 Ctrl+C 停止服务")
    print("-" * 50)
    
    try:
        uvicorn.run(**config)
    except KeyboardInterrupt:
        print("\n👋 服务已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        sys.exit(1)
