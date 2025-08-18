#!/usr/bin/env python3
"""
诊断JSON序列化问题
"""

import sys
import os
import json
import numpy as np
import pandas as pd

# 添加项目根目录到Python路径
sys.path.append('.')

def test_json_serialization():
    """测试JSON序列化"""
    try:
        from services.jq_service import jq_service
        
        print("✅ 聚宽服务导入成功")
        
        # 测试获取股票列表
        import asyncio
        
        async def test():
            stocks = await jq_service.get_stock_list('CN')
            print(f"获取到 {len(stocks)} 只股票")
            
            if stocks:
                # 测试第一只股票
                first_stock = stocks[0]
                print(f"第一只股票: {first_stock['code']}")
                
                # 逐个测试每个字段
                for key, value in first_stock.items():
                    try:
                        json.dumps({key: value})
                        print(f"✅ {key}: {type(value)} - {value}")
                    except Exception as e:
                        print(f"❌ {key}: {type(value)} - {value} - 错误: {e}")
                
                # 测试整个股票对象
                try:
                    json.dumps(first_stock)
                    print("✅ 单只股票序列化成功")
                except Exception as e:
                    print(f"❌ 单只股票序列化失败: {e}")
                
                # 测试股票列表
                try:
                    json.dumps(stocks[:5])  # 只测试前5只
                    print("✅ 5只股票序列化成功")
                except Exception as e:
                    print(f"❌ 5只股票序列化失败: {e}")
                
                # 测试10只股票
                try:
                    json.dumps(stocks[:10])
                    print("✅ 10只股票序列化成功")
                except Exception as e:
                    print(f"❌ 10只股票序列化失败: {e}")
                
                # 测试20只股票
                try:
                    json.dumps(stocks[:20])
                    print("✅ 20只股票序列化成功")
                except Exception as e:
                    print(f"❌ 20只股票序列化失败: {e}")
                
                # 测试50只股票
                try:
                    json.dumps(stocks[:50])
                    print("✅ 50只股票序列化成功")
                except Exception as e:
                    print(f"❌ 50只股票序列化失败: {e}")
                    
                # 测试所有股票
                try:
                    json.dumps(stocks)
                    print("✅ 所有股票序列化成功")
                except Exception as e:
                    print(f"❌ 所有股票序列化失败: {e}")
                    
        asyncio.run(test())
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_json_serialization()
