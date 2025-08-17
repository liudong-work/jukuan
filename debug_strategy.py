#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
调试策略逻辑
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def debug_strategy():
    """调试策略逻辑"""
    try:
        print("=== 调试策略逻辑 ===")
        
        from src.strategies.stock_screener import StockScreener
        
        # 创建模拟数据提供者
        class MockDataProvider:
            def get_daily_data(self, stock_code, start_date, end_date):
                import pandas as pd
                import numpy as np
                
                # 创建简单的测试数据
                dates = pd.date_range(start=start_date, end=end_date, freq='D')
                
                # 创建明显的均线交叉数据
                # 前5天：短期均线 < 长期均线
                # 第6天：短期均线 = 长期均线（交叉点）
                # 后4天：短期均线 > 长期均线（形成金叉）
                close_prices = [15.0, 14.0, 13.0, 12.0, 11.0, 12.0, 13.0, 14.0, 15.0, 16.0]
                volumes = [1000000] * len(close_prices)
                
                data = pd.DataFrame({
                    'open': close_prices,
                    'high': [p * 1.02 for p in close_prices],
                    'low': [p * 0.98 for p in close_prices],
                    'close': close_prices,
                    'volume': volumes
                }, index=dates[:len(close_prices)])
                
                print(f"   创建了 {len(data)} 条测试数据")
                print(f"   价格范围: {data['close'].min():.2f} - {data['close'].max():.2f}")
                return data
        
        provider = MockDataProvider()
        screener = StockScreener(provider)
        
        # 测试MA交叉策略
        test_stocks = ['000001.XSHE']
        print(f"\n测试股票: {test_stocks}")
        
        # 手动计算均线
        data = provider.get_daily_data('000001.XSHE', '2024-01-01', '2024-01-10')
        if not data.empty:
            data['MA_short'] = data['close'].rolling(window=2).mean()
            data['MA_long'] = data['close'].rolling(window=5).mean()
            
            print(f"   短期均线(2日): {data['MA_short'].dropna().tolist()}")
            print(f"   长期均线(5日): {data['MA_long'].dropna().tolist()}")
            
            # 检查金叉
            latest = data.iloc[-1]
            prev = data.iloc[-2]
            
            golden_cross = (latest['MA_short'] > latest['MA_long'] and 
                           prev['MA_short'] <= prev['MA_long'])
            
            print(f"   金叉条件: {golden_cross}")
            print(f"   最新短期均线: {latest['MA_short']:.2f}")
            print(f"   最新长期均线: {latest['MA_long']:.2f}")
            print(f"   前一日短期均线: {prev['MA_short']:.2f}")
            print(f"   前一日长期均线: {prev['MA_long']:.2f}")
        
        # 执行策略
        results = screener.screen_by_ma_cross(test_stocks, short_window=2, long_window=5)
        
        if results:
            print(f"\n✅ 找到 {len(results)} 只股票")
            for stock in results:
                print(f"   代码: {stock['code']}")
                print(f"   价格: {stock['price']:.2f}")
                print(f"   涨跌幅: {stock.get('change_pct', 'N/A')}")
                print(f"   成交量: {stock.get('volume', 'N/A'):,.0f}")
        else:
            print("\n❌ 未找到符合条件的股票")
        
    except Exception as e:
        print(f"❌ 调试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_strategy()
