#!/usr/bin/env python3
"""
量化交易系统启动脚本
"""

import os
import sys
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def setup_logging():
    """设置日志配置"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('jukuan.log', encoding='utf-8')
        ]
    )

def check_dependencies():
    """检查依赖包"""
    required_packages = [
        'pandas', 'numpy', 'dash', 'plotly', 'jqdatasdk'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ 缺少以下依赖包: {', '.join(missing_packages)}")
        print("请运行: pip install -r requirements.txt")
        return False
    
    return True

def check_config():
    """检查配置文件"""
    env_file = project_root / '.env'
    if not env_file.exists():
        print("⚠️  未找到 .env 配置文件")
        print("请复制 env_example.txt 为 .env 并配置聚宽账号信息")
        return False
    
    return True

def main():
    """主函数"""
    print("=== 聚宽量化交易系统 ===")
    
    # 设置日志
    setup_logging()
    
    # 检查依赖
    if not check_dependencies():
        sys.exit(1)
    
    # 检查配置
    if not check_config():
        print("请配置环境变量后重新运行")
        sys.exit(1)
    
    print("✅ 系统检查完成")
    print("\n选择运行模式:")
    print("1. 命令行示例")
    print("2. Web界面")
    print("3. 退出")
    
    while True:
        try:
            choice = input("\n请输入选择 (1-3): ").strip()
            
            if choice == '1':
                run_command_line_example()
                break
            elif choice == '2':
                run_web_interface()
                break
            elif choice == '3':
                print("再见!")
                sys.exit(0)
            else:
                print("无效选择，请输入 1-3")
        except KeyboardInterrupt:
            print("\n\n再见!")
            sys.exit(0)

def run_command_line_example():
    """运行命令行示例"""
    print("\n=== 运行命令行示例 ===")
    
    try:
        from examples.jq_simple_strategy import main as run_example
        run_example()
    except Exception as e:
        print(f"❌ 运行示例失败: {e}")
        logging.error(f"运行示例失败: {e}")

def run_web_interface():
    """运行Web界面"""
    print("\n=== 启动Web界面 ===")
    print("Web界面将在 http://localhost:8050 启动")
    print("按 Ctrl+C 停止服务")
    
    try:
        from app import app
        app.run_server(debug=True, host='0.0.0.0', port=8050)
    except Exception as e:
        print(f"❌ 启动Web界面失败: {e}")
        logging.error(f"启动Web界面失败: {e}")

if __name__ == "__main__":
    main()
