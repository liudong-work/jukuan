"""
KDJ+MACD金叉策略示例
演示如何使用KDJ和MACD双重金叉策略
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import logging
from datetime import datetime

from src.data.jq_data_provider import JQDataProvider
from src.strategies.kdj_macd_strategy import KDJMACDStrategy
from src.backtest.backtest_engine import BacktestEngine

# 配置日志
logging.basicConfig(level=logging.INFO)

def main():
    """主函数"""
    print("=== KDJ+MACD金叉策略示例 ===")
    
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
        end_date = '2025-05-14'
        
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
    
    # 3. 创建KDJ+MACD策略
    print("\n3. 创建KDJ+MACD策略...")
    try:
        strategy_params = {
            'kdj_n': 9,           # KDJ计算周期
            'kdj_m1': 3,          # KDJ的M1参数
            'kdj_m2': 3,          # KDJ的M2参数
            'macd_fast': 12,      # MACD快线周期
            'macd_slow': 26,      # MACD慢线周期
            'macd_signal': 9,     # MACD信号线周期
            'position_size': 0.1  # 仓位比例
        }
        
        strategy = KDJMACDStrategy(strategy_params)
        print("✅ KDJ+MACD策略创建成功")
        print(f"策略信息: {strategy.get_strategy_info()}")
        
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
        
        # 显示详细指标
        strategy_metrics = results['strategy_metrics']
        portfolio_metrics = results['portfolio_metrics']
        
        print("\n=== 策略性能指标 ===")
        print(f"总收益率: {strategy_metrics.get('total_return', 0):.2%}")
        print(f"年化收益率: {strategy_metrics.get('annual_return', 0):.2%}")
        print(f"夏普比率: {strategy_metrics.get('sharpe_ratio', 0):.2f}")
        print(f"最大回撤: {strategy_metrics.get('max_drawdown', 0):.2%}")
        
        print("\n=== 投资组合指标 ===")
        print(f"最终资产: {portfolio_metrics.get('final_value', 0):,.0f}")
        print(f"总交易次数: {results['trade_summary']['total_trades']}")
        
        # 显示交易记录
        print(f"\n=== 交易记录 ===")
        trade_log = results['trade_log']
        if trade_log:
            print(f"买入交易: {len([t for t in trade_log if t['signal'] == 1])} 次")
            print(f"卖出交易: {len([t for t in trade_log if t['signal'] == -1])} 次")
            
            # 显示最近的几笔交易
            recent_trades = trade_log[-5:] if len(trade_log) > 5 else trade_log
            for trade in recent_trades:
                signal_text = "买入" if trade['signal'] == 1 else "卖出"
                print(f"  {trade['timestamp']}: {signal_text} {trade['quantity']}股 @ {trade['price']:.2f}")
        
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
    
    print("\n=== KDJ+MACD策略示例运行完成 ===")

if __name__ == "__main__":
    main()
