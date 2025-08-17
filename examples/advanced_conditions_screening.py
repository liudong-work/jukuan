"""
高级复合选股策略示例
演示复杂的多条件选股逻辑
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import logging
from datetime import datetime

from src.data.jq_data_provider import JQDataProvider
from src.strategies.advanced_screener import AdvancedStockScreener

# 配置日志
logging.basicConfig(level=logging.INFO)

def main():
    """主函数"""
    print("=== 高级复合选股策略示例 ===")
    
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
    
    # 2. 创建高级选股器
    print("\n2. 创建高级选股器...")
    try:
        advanced_screener = AdvancedStockScreener(data_provider)
        print("✅ 高级选股器创建成功")
        
        # 显示策略信息
        strategy_info = advanced_screener.get_strategy_info()
        print(f"\n策略名称: {strategy_info['name']}")
        print(f"策略描述: {strategy_info['description']}")
        print(f"\n选股条件 ({len(strategy_info['conditions'])} 个):")
        for i, condition in enumerate(strategy_info['conditions'], 1):
            print(f"  {i:2d}. {condition}")
        
    except Exception as e:
        print(f"❌ 创建高级选股器失败: {e}")
        return
    
    # 3. 准备股票列表（排除科创板北交所）
    print("\n3. 准备股票列表...")
    
    # 手动构建股票列表，排除科创板北交所
    sample_stocks = [
        # 深市主板
        '000001.XSHE',  # 平安银行
        '000002.XSHE',  # 万科A
        '000858.XSHE',  # 五粮液
        '000725.XSHE',  # 京东方A
        '000063.XSHE',  # 中兴通讯
        '000568.XSHE',  # 泸州老窖
        '000596.XSHE',  # 古井贡酒
        '000799.XSHE',  # 酒鬼酒
        '000858.XSHE',  # 五粮液
        '000895.XSHE',  # 双汇发展
        
        # 深市中小板
        '002415.XSHE',  # 海康威视
        '002594.XSHE',  # 比亚迪
        '002230.XSHE',  # 科大讯飞
        '002475.XSHE',  # 立讯精密
        '002714.XSHE',  # 牧原股份
        '002304.XSHE',  # 洋河股份
        '002027.XSHE',  # 分众传媒
        '002008.XSHE',  # 大族激光
        '002001.XSHE',  # 新和成
        '002142.XSHE',  # 宁波银行
        
        # 深市创业板
        '300059.XSHE',  # 东方财富
        '300750.XSHE',  # 宁德时代
        '300760.XSHE',  # 迈瑞医疗
        '300015.XSHE',  # 爱尔眼科
        '300122.XSHE',  # 智飞生物
        '300124.XSHE',  # 汇川技术
        '300142.XSHE',  # 沃森生物
        '300347.XSHE',  # 泰格医药
        '300601.XSHE',  # 康泰生物
        '300498.XSHE',  # 温氏股份
        
        # 沪市主板
        '600000.XSHG',  # 浦发银行
        '600036.XSHG',  # 招商银行
        '600519.XSHG',  # 贵州茅台
        '600276.XSHG',  # 恒瑞医药
        '600887.XSHG',  # 伊利股份
        '600585.XSHG',  # 海螺水泥
        '600309.XSHG',  # 万华化学
        '600104.XSHG',  # 上汽集团
        '600690.XSHG',  # 海尔智家
        '600009.XSHG',  # 上海机场
        
        # 沪市科创板（将被排除）
        '688001.XSHG',  # 华兴源创
        '688002.XSHG',  # 睿创微纳
        '688003.XSHG',  # 天准科技
        '688005.XSHG',  # 容百科技
        '688008.XSHG',  # 澜起科技
        '688009.XSHG',  # 中国通号
        '688010.XSHG',  # 福光股份
        '688011.XSHG',  # 新光光电
        '688012.XSHG',  # 中微公司
        '688015.XSHG',  # 交控科技
    ]
    
    print(f"✅ 准备 {len(sample_stocks)} 只示例股票（包含将被排除的科创板股票）")
    
    # 4. 执行高级复合选股
    print("\n4. 执行高级复合选股策略...")
    try:
        results = advanced_screener.screen_by_advanced_conditions(
            sample_stocks,
            min_price=5.0,
            max_price=200.0
        )
        
        if results:
            print(f"✅ 找到 {len(results)} 只符合条件的股票:")
            print("\n" + "="*80)
            print(f"{'排名':<4} {'代码':<12} {'名称':<12} {'价格':<8} {'周KDJ':<15} {'周MACD':<15} {'日MACD':<15} {'成交量比':<8}")
            print("="*80)
            
            for i, stock in enumerate(results, 1):
                print(f"{i:<4} {stock['code']:<12} {stock['name']:<12} {stock['price']:<8.2f} "
                      f"K:{stock['weekly_kdj_k']:<4.1f}D:{stock['weekly_kdj_d']:<4.1f}J:{stock['weekly_kdj_j']:<4.1f} "
                      f"{stock['weekly_macd']:<7.3f} {stock['weekly_macd_signal']:<7.3f} "
                      f"{stock['daily_macd']:<7.3f} {stock['daily_macd_signal']:<7.3f} "
                      f"{stock['volume_ratio']:<8.2f}")
            
            print("="*80)
            
            # 显示详细信息
            print(f"\n🏆 最佳股票: {results[0]['code']} - {results[0]['name']}")
            print(f"   价格: {results[0]['price']:.2f}元")
            print(f"   周线KDJ: K={results[0]['weekly_kdj_k']:.1f}, D={results[0]['weekly_kdj_d']:.1f}, J={results[0]['weekly_kdj_j']:.1f}")
            print(f"   周线MACD: {results[0]['weekly_macd']:.3f} (信号线: {results[0]['weekly_macd_signal']:.3f})")
            print(f"   日线MACD: {results[0]['daily_macd']:.3f} (信号线: {results[0]['daily_macd_signal']:.3f})")
            print(f"   成交量比: {results[0]['volume_ratio']:.2f}")
            
        else:
            print("⚠️ 未找到符合条件的股票")
            print("\n可能的原因:")
            print("1. 当前市场环境下，同时满足所有条件的股票较少")
            print("2. 部分条件过于严格，需要适当放宽")
            print("3. 数据时间范围限制，影响指标计算")
            
    except Exception as e:
        print(f"❌ 高级选股失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 5. 策略分析
    print("\n5. 策略分析...")
    print("本策略的优势:")
    print("✅ 多维度筛选，提高选股质量")
    print("✅ 技术指标共振，增强信号可靠性")
    print("✅ 排除高风险板块，降低投资风险")
    print("✅ 成交量确认，提高趋势可信度")
    
    print("\n注意事项:")
    print("⚠️ 条件过于严格可能导致选股数量较少")
    print("⚠️ 需要定期调整参数以适应市场变化")
    print("⚠️ 建议结合基本面分析进行最终决策")
    
    # 6. 清理资源
    print("\n6. 清理资源...")
    try:
        data_provider.disconnect()
        print("✅ 聚宽连接已断开")
    except Exception as e:
        print(f"❌ 断开连接异常: {e}")
    
    print("\n=== 高级复合选股策略示例运行完成 ===")

if __name__ == "__main__":
    main()
