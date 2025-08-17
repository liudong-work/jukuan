"""
聚宽接口简单策略示例
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import logging
from datetime import datetime, timedelta

from src.data.jq_data_provider import JQDataProvider
from src.strategies.ma_cross_strategy import MACrossStrategy
from src.backtest.backtest_engine import BacktestEngine

# 配置日志
logging.basicConfig(level=logging.INFO)

def main():
    """主函数"""
    print("=== 聚宽量化交易系统示例 ===")
    
    # 1. 初始化聚宽数据提供者
    print("\n1. 连接聚宽服务器...")
    try:
        data_provider = JQDataProvider()
        if not data_provider.is_connected:
            print("❌ 聚宽连接失败")
            return
        print("✅ 聚宽连接成功")
    except Exception as e:
        print(f"❌ 聚宽连接异常: {e}")
        return
    
    # 2. 获取股票数据
    print("\n2. 获取股票数据...")
    try:
        stock_code = '000001.XSHE'  # 平安银行
        # 使用聚宽账号允许的确切时间范围
        start_date = '2024-05-07'
        end_date = '2025-05-14'  # 根据聚宽提示的确切结束时间
        
        print(f"获取股票 {stock_code} 从 {start_date} 到 {end_date} 的数据...")
        data = data_provider.get_daily_data(stock_code, start_date, end_date)
        
        if data.empty:
            print("❌ 获取数据失败")
            return
        
        print(f"✅ 成功获取 {len(data)} 条数据")
        print(f"数据范围: {data.index[0]} 到 {data.index[-1]}")
        
    except Exception as e:
        print(f"❌ 获取数据异常: {e}")
        return
    
    # 3. 创建策略
    print("\n3. 创建交易策略...")
    try:
        strategy_params = {
            'short_window': 5,
            'long_window': 20,
            'position_size': 0.1
        }
        
        strategy = MACrossStrategy(strategy_params)
        print("✅ 策略创建成功")
        
    except Exception as e:
        print(f"❌ 策略创建异常: {e}")
        return
    
    # 4. 运行回测
    print("\n4. 运行回测...")
    try:
        backtest_engine = BacktestEngine(initial_capital=1000000)
        
        results = backtest_engine.run_backtest(
            strategy=strategy,
            data=data,
            start_date=start_date,
            end_date=end_date
        )
        
        if results:
            print("✅ 回测完成")
        else:
            print("❌ 回测失败")
            return
            
    except Exception as e:
        print(f"❌ 回测异常: {e}")
        return
    
    # 5. 显示回测结果
    print("\n5. 回测结果分析...")
    try:
        summary = backtest_engine.get_backtest_summary()
        
        print("\n=== 回测摘要 ===")
        for key, value in summary.items():
            print(f"{key}: {value}")
        
    except Exception as e:
        print(f"❌ 结果分析异常: {e}")
        return
    
    # 6. 清理资源
    print("\n6. 清理资源...")
    try:
        data_provider.disconnect()
        print("✅ 聚宽连接已断开")
    except Exception as e:
        print(f"❌ 断开连接异常: {e}")
    
    print("\n=== 示例运行完成 ===")

if __name__ == "__main__":
    main()
