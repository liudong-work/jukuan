#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
快速测试涨跌幅和成交量修复
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_fix():
    """测试修复效果"""
    try:
        print("=== 测试涨跌幅和成交量修复 ===")
        
        # 导入修复后的模块
        from src.strategies.stock_screener import StockScreener
        
        # 创建模拟数据提供者
        class MockDataProvider:
            def get_daily_data(self, stock_code, start_date, end_date):
                import pandas as pd
                import numpy as np
                
                # 创建有价格变化的模拟数据
                dates = pd.date_range(start=start_date, end=end_date, freq='D')
                np.random.seed(42)
                
                # 创建价格序列，确保有变化
                base_price = 20.0
                prices = [base_price]
                for i in range(len(dates) - 1):
                    change = np.random.normal(0.01, 0.03)  # 1%平均涨幅，3%波动
                    new_price = prices[-1] * (1 + change)
                    prices.append(max(new_price, 1.0))
                
                data = pd.DataFrame({
                    'open': [p * (1 + np.random.normal(0, 0.005)) for p in prices],
                    'high': [p * (1 + abs(np.random.normal(0, 0.01))) for p in prices],
                    'low': [p * (1 - abs(np.random.normal(0, 0.01))) for p in prices],
                    'close': prices,
                    'volume': np.random.uniform(1000000, 5000000, len(dates))
                }, index=dates)
                
                return data
        
        # 测试
        provider = MockDataProvider()
        screener = StockScreener(provider)
        
        # 测试MA交叉策略
        test_stocks = ['000001.XSHE']
        results = screener.screen_by_ma_cross(test_stocks, short_window=2, long_window=5)
        
        if results:
            print("✅ MA交叉策略测试成功")
            stock = results[0]
            print(f"   股票代码: {stock['code']}")
            print(f"   价格: {stock['price']:.2f}")
            print(f"   涨跌幅: {stock.get('change_pct', 'N/A')}")
            print(f"   成交量: {stock.get('volume', 'N/A'):,.0f}")
            
            # 验证数据
            if 'change_pct' in stock:
                print("   ✅ 涨跌幅数据正常")
            else:
                print("   ❌ 涨跌幅数据缺失")
                
            if stock.get('volume', 0) > 0:
                print("   ✅ 成交量数据正常")
            else:
                print("   ❌ 成交量数据异常")
        else:
            print("⚠️ 未找到符合条件的股票")
        
        # 测试RSI策略
        results = screener.screen_by_rsi_oversold(test_stocks, rsi_period=3, rsi_threshold=80)
        
        if results:
            print("\n✅ RSI策略测试成功")
            stock = results[0]
            print(f"   股票代码: {stock['code']}")
            print(f"   价格: {stock['price']:.2f}")
            print(f"   涨跌幅: {stock.get('change_pct', 'N/A')}")
            print(f"   成交量: {stock.get('volume', 'N/A'):,.0f}")
            print(f"   RSI: {stock.get('rsi', 'N/A'):.2f}")
            
            # 验证数据
            if 'change_pct' in stock:
                print("   ✅ 涨跌幅数据正常")
            else:
                print("   ❌ 涨跌幅数据缺失")
                
            if stock.get('volume', 0) > 0:
                print("   ✅ 成交量数据正常")
            else:
                print("   ❌ 成交量数据异常")
        else:
            print("⚠️ 未找到符合条件的股票")
        
        print("\n✅ 修复测试完成")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_fix()
