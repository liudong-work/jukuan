"""
策略推荐示例
演示如何使用策略评分和推荐功能
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
    print("=== 策略推荐示例 ===")
    
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
    
    # 4. 获取策略推荐
    print("\n4. 获取策略推荐...")
    try:
        recommendations = screener.get_strategy_recommendations(sample_stocks, top_n=3)
        
        if recommendations:
            print(f"✅ 成功生成 {len(recommendations)} 个策略的推荐")
            
            for strategy_name, stocks in recommendations.items():
                print(f"\n--- {strategy_name} 推荐 ---")
                if stocks:
                    print(f"找到 {len(stocks)} 只推荐股票:")
                    for i, stock in enumerate(stocks, 1):
                        score = stock.get('strategy_score', 0)
                        print(f"  {i}. {stock['code']}: {stock['price']:.2f}元 - 评分: {score:.1f}")
                        if 'signal' in stock:
                            print(f"     信号: {stock['signal']}")
                else:
                    print("⚠️ 未找到符合条件的股票")
        else:
            print("❌ 策略推荐生成失败")
            
    except Exception as e:
        print(f"❌ 获取策略推荐失败: {e}")
    
    # 5. 测试单个策略评分
    print("\n5. 测试单个策略评分...")
    
    # 选择一只股票进行详细评分
    test_stock = '000001.XSHE'  # 平安银行
    
    try:
        # 获取股票数据
        end_date = '2025-05-14'
        start_date = '2024-05-07'
        
        data = data_provider.get_daily_data(test_stock, start_date, end_date)
        
        if not data.empty:
            print(f"\n{test_stock} 策略评分分析:")
            
            # 测试不同策略的评分
            strategies = ['ma_cross', 'rsi_oversold', 'momentum']
            
            for strategy in strategies:
                score = screener.calculate_strategy_score(data, strategy)
                print(f"  {strategy}: {score:.1f}分")
                
                # 显示评分详情
                if strategy == 'ma_cross':
                    data_copy = data.copy()
                    data_copy['MA_short'] = data_copy['close'].rolling(window=5).mean()
                    data_copy['MA_long'] = data_copy['close'].rolling(window=20).mean()
                    
                    ma_trend = (data_copy['MA_short'].iloc[-1] - data_copy['MA_short'].iloc[-5]) / data_copy['MA_short'].iloc[-5]
                    print(f"    均线趋势: {ma_trend:.3f}")
                    
                    volume_support = data_copy['volume'].iloc[-1] / data_copy['volume'].rolling(window=10).mean().iloc[-1]
                    print(f"    成交量支持: {volume_support:.2f}")
                    
                elif strategy == 'momentum':
                    data_copy = data.copy()
                    data_copy['momentum'] = data_copy['close'].pct_change(periods=10)
                    data_copy['momentum_ma'] = data_copy['momentum'].rolling(window=5).mean()
                    
                    momentum_strength = data_copy['momentum'].iloc[-1]
                    print(f"    动量强度: {momentum_strength:.3f}")
                    
                    momentum_consistency = (data_copy['momentum'] > 0).rolling(window=5).sum().iloc[-1] / 5
                    print(f"    动量持续性: {momentum_consistency:.2f}")
        else:
            print(f"❌ 无法获取 {test_stock} 的数据")
            
    except Exception as e:
        print(f"❌ 策略评分测试失败: {e}")
    
    # 6. 清理资源
    print("\n6. 清理资源...")
    try:
        data_provider.disconnect()
        print("✅ 聚宽连接已断开")
    except Exception as e:
        print(f"❌ 断开连接异常: {e}")
    
    print("\n=== 策略推荐示例运行完成 ===")

if __name__ == "__main__":
    main()
