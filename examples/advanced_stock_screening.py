"""
高级策略选股示例
演示新增的选股策略功能
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
    print("=== 高级策略选股示例 ===")
    
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
        '300059.XSHE',  # 东方财富
        '000063.XSHE',  # 中兴通讯
        '002230.XSHE',  # 科大讯飞
        '300750.XSHE',  # 宁德时代
        '600276.XSHG',  # 恒瑞医药
        '000568.XSHE'   # 泸州老窖
    ]
    print(f"✅ 准备 {len(sample_stocks)} 只示例股票")
    
    # 4. 执行新增的选股策略
    print("\n4. 执行新增选股策略...")
    
    # 4.1 布林带策略选股
    print("\n--- 布林带策略选股 ---")
    try:
        bb_results = screener.screen_by_bollinger_bands(
            sample_stocks,
            bb_period=20,
            bb_std=2.0,
            min_price=5.0,
            max_price=100.0
        )
        
        if bb_results:
            print(f"✅ 找到 {len(bb_results)} 只符合条件的股票:")
            for stock in bb_results:
                print(f"  {stock['code']}: {stock['price']:.2f}元 - {stock['signal']}")
                print(f"    布林带位置: {stock['bb_position']:.3f}")
        else:
            print("⚠️ 未找到符合条件的股票")
            
    except Exception as e:
        print(f"❌ 布林带选股失败: {e}")
    
    # 4.2 动量策略选股
    print("\n--- 动量策略选股 ---")
    try:
        momentum_results = screener.screen_by_momentum(
            sample_stocks,
            momentum_period=10,
            momentum_threshold=0.03,
            min_price=5.0,
            max_price=100.0
        )
        
        if momentum_results:
            print(f"✅ 找到 {len(momentum_results)} 只符合条件的股票:")
            for stock in momentum_results:
                print(f"  {stock['code']}: {stock['price']:.2f}元 - {stock['signal']}")
                print(f"    动量: {stock['momentum']:.3f}, 成交量比: {stock['volume_ratio']:.2f}")
        else:
            print("⚠️ 未找到符合条件的股票")
            
    except Exception as e:
        print(f"❌ 动量选股失败: {e}")
    
    # 4.3 双重策略选股
    print("\n--- 双重策略选股 (MA交叉+RSI超卖) ---")
    try:
        dual_results = screener.screen_by_dual_strategy(
            sample_stocks,
            strategy1='ma_cross',
            strategy2='rsi_oversold',
            min_price=5.0,
            max_price=100.0
        )
        
        if dual_results:
            print(f"✅ 找到 {len(dual_results)} 只符合条件的股票:")
            for stock in dual_results:
                print(f"  {stock['code']}: {stock['price']:.2f}元 - {stock['signal']}")
                print(f"    策略组合: {stock['strategy1']} + {stock['strategy2']}")
        else:
            print("⚠️ 未找到符合条件的股票")
            
    except Exception as e:
        print(f"❌ 双重策略选股失败: {e}")
    
    # 4.4 行业轮动策略选股
    print("\n--- 行业轮动策略选股 ---")
    try:
        industry_results = screener.screen_by_industry_rotation(
            industry_list=['计算机', '电子', '医药生物'],
            min_price=5.0,
            max_price=100.0
        )
        
        if industry_results:
            print(f"✅ 找到 {len(industry_results)} 只符合条件的股票:")
            for stock in industry_results:
                print(f"  {stock['code']}: {stock['price']:.2f}元 - {stock['signal']}")
                print(f"    行业: {stock['industry']}, 相对强度: {stock['relative_strength']:.3f}")
        else:
            print("⚠️ 未找到符合条件的股票")
            
    except Exception as e:
        print(f"❌ 行业轮动选股失败: {e}")
    
    # 5. 策略效果对比分析
    print("\n5. 策略效果对比分析...")
    
    # 收集所有策略的结果
    all_strategy_results = {}
    
    strategies_to_test = [
        ('ma_cross', '均线交叉'),
        ('kdj_macd', 'KDJ+MACD'),
        ('volume_breakout', '放量突破'),
        ('rsi_oversold', 'RSI超卖'),
        ('bollinger_bands', '布林带'),
        ('momentum', '动量策略')
    ]
    
    for strategy_id, strategy_name in strategies_to_test:
        try:
            if strategy_id == 'ma_cross':
                results = screener.screen_by_ma_cross(sample_stocks, 5, 20, 5.0, 100.0)
            elif strategy_id == 'kdj_macd':
                results = screener.screen_by_kdj_macd(sample_stocks, 5.0, 100.0)
            elif strategy_id == 'volume_breakout':
                results = screener.screen_by_volume_breakout(sample_stocks, 2.0, 0.05, 5.0, 100.0)
            elif strategy_id == 'rsi_oversold':
                results = screener.screen_by_rsi_oversold(sample_stocks, 14, 30.0, 5.0, 100.0)
            elif strategy_id == 'bollinger_bands':
                results = screener.screen_by_bollinger_bands(sample_stocks, 20, 2.0, 5.0, 100.0)
            elif strategy_id == 'momentum':
                results = screener.screen_by_momentum(sample_stocks, 10, 0.03, 5.0, 100.0)
            
            all_strategy_results[strategy_name] = len(results) if results else 0
            
        except Exception as e:
            print(f"❌ {strategy_name} 策略测试失败: {e}")
            all_strategy_results[strategy_name] = 0
    
    # 显示策略效果对比
    print("\n策略效果对比:")
    print("-" * 40)
    for strategy_name, count in all_strategy_results.items():
        print(f"{strategy_name:12}: {count:2d} 只股票")
    
    # 找出最有效的策略
    best_strategy = max(all_strategy_results.items(), key=lambda x: x[1])
    print(f"\n🏆 最有效策略: {best_strategy[0]} (找到 {best_strategy[1]} 只股票)")
    
    # 6. 清理资源
    print("\n6. 清理资源...")
    try:
        data_provider.disconnect()
        print("✅ 聚宽连接已断开")
    except Exception as e:
        print(f"❌ 断开连接异常: {e}")
    
    print("\n=== 高级策略选股示例运行完成 ===")

if __name__ == "__main__":
    main()
