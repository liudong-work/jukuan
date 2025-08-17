"""
策略选股示例
演示如何使用不同的选股策略筛选股票
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import logging
from datetime import datetime

from src.data.jq_data_provider import JQDataProvider
from src.strategies.stock_screener import StockScreener

# 配置日志
logging.basicConfig(level=logging.INFO)

def main():
    """主函数"""
    print("=== 策略选股示例 ===")
    
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
    
    # 2. 创建股票筛选器
    print("\n2. 创建股票筛选器...")
    try:
        screener = StockScreener(data_provider)
        print("✅ 股票筛选器创建成功")
        
        # 显示可用策略
        strategies = screener.get_all_strategies()
        print(f"\n可用选股策略 ({len(strategies)} 种):")
        for strategy in strategies:
            print(f"  - {strategy['name']}: {strategy['description']}")
        
    except Exception as e:
        print(f"❌ 创建筛选器失败: {e}")
        return
    
    # 3. 示例股票列表
    print("\n3. 准备股票列表...")
    sample_stocks = [
        '000001.XSHE',  # 平安银行
        '000002.XSHE',  # 万科A
        '000858.XSHE',  # 五粮液
        '002415.XSHE',  # 海康威视
        '600000.XSHG',  # 浦发银行
        '600036.XSHG',  # 招商银行
        '600519.XSHG',  # 贵州茅台
        '000725.XSHE',  # 京东方A
        '002594.XSHE',  # 比亚迪
        '300059.XSHE'   # 东方财富
    ]
    print(f"✅ 准备 {len(sample_stocks)} 只示例股票")
    
    # 4. 执行不同策略的选股
    print("\n4. 执行选股策略...")
    
    # 4.1 均线交叉策略选股
    print("\n--- 均线交叉策略选股 ---")
    try:
        ma_results = screener.screen_by_ma_cross(
            sample_stocks, 
            short_window=5, 
            long_window=20,
            min_price=5.0,
            max_price=100.0
        )
        
        if ma_results:
            print(f"✅ 找到 {len(ma_results)} 只符合条件的股票:")
            for stock in ma_results:
                print(f"  {stock['code']}: {stock['price']:.2f}元 - {stock['signal']}")
        else:
            print("⚠️ 未找到符合条件的股票")
            
    except Exception as e:
        print(f"❌ 均线交叉选股失败: {e}")
    
    # 4.2 KDJ+MACD双重金叉选股
    print("\n--- KDJ+MACD双重金叉选股 ---")
    try:
        kdj_macd_results = screener.screen_by_kdj_macd(
            sample_stocks,
            min_price=5.0,
            max_price=100.0
        )
        
        if kdj_macd_results:
            print(f"✅ 找到 {len(kdj_macd_results)} 只符合条件的股票:")
            for stock in kdj_macd_results:
                print(f"  {stock['code']}: {stock['price']:.2f}元 - {stock['signal']}")
        else:
            print("⚠️ 未找到符合条件的股票")
            
    except Exception as e:
        print(f"❌ KDJ+MACD选股失败: {e}")
    
    # 4.3 放量突破策略选股
    print("\n--- 放量突破策略选股 ---")
    try:
        volume_results = screener.screen_by_volume_breakout(
            sample_stocks,
            volume_ratio=2.0,
            price_change=0.05,
            min_price=5.0,
            max_price=100.0
        )
        
        if volume_results:
            print(f"✅ 找到 {len(volume_results)} 只符合条件的股票:")
            for stock in volume_results:
                print(f"  {stock['code']}: {stock['price']:.2f}元 - {stock['signal']}")
        else:
            print("⚠️ 未找到符合条件的股票")
            
    except Exception as e:
        print(f"❌ 放量突破选股失败: {e}")
    
    # 4.4 RSI超卖策略选股
    print("\n--- RSI超卖策略选股 ---")
    try:
        rsi_results = screener.screen_by_rsi_oversold(
            sample_stocks,
            rsi_period=14,
            rsi_threshold=30.0,
            min_price=5.0,
            max_price=100.0
        )
        
        if rsi_results:
            print(f"✅ 找到 {len(rsi_results)} 只符合条件的股票:")
            for stock in rsi_results:
                print(f"  {stock['code']}: {stock['price']:.2f}元 - RSI: {stock['rsi']:.2f}")
        else:
            print("⚠️ 未找到符合条件的股票")
            
    except Exception as e:
        print(f"❌ RSI超卖选股失败: {e}")
    
    # 5. 选股结果汇总
    print("\n5. 选股结果汇总...")
    all_results = []
    if 'ma_results' in locals() and ma_results:
        all_results.extend(ma_results)
    if 'kdj_macd_results' in locals() and kdj_macd_results:
        all_results.extend(kdj_macd_results)
    if 'volume_results' in locals() and volume_results:
        all_results.extend(volume_results)
    if 'rsi_results' in locals() and rsi_results:
        all_results.extend(rsi_results)
    
    if all_results:
        print(f"✅ 总共找到 {len(all_results)} 只符合条件的股票")
        
        # 按策略分组
        strategy_groups = {}
        for stock in all_results:
            strategy = stock['strategy']
            if strategy not in strategy_groups:
                strategy_groups[strategy] = []
            strategy_groups[strategy].append(stock)
        
        print("\n按策略分组结果:")
        for strategy, stocks in strategy_groups.items():
            print(f"  {strategy}: {len(stocks)} 只")
            
    else:
        print("⚠️ 所有策略都未找到符合条件的股票")
    
    # 6. 清理资源
    print("\n6. 清理资源...")
    try:
        data_provider.disconnect()
        print("✅ 聚宽连接已断开")
    except Exception as e:
        print(f"❌ 断开连接异常: {e}")
    
    print("\n=== 策略选股示例运行完成 ===")

if __name__ == "__main__":
    main()
