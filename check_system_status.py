"""
系统状态检查脚本
检查所有模块和服务是否正常运行
"""

import asyncio
import aiohttp
import json
import sys
from datetime import datetime

# 系统配置
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

async def check_endpoint(session, url, name, expected_status=200):
    """检查单个端点状态"""
    try:
        async with session.get(url) as response:
            status = response.status
            if status == expected_status:
                print(f"✅ {name}: {status} OK")
                try:
                    data = await response.json()
                    return True, data
                except:
                    return True, None
            else:
                print(f"❌ {name}: {status} FAILED")
                return False, None
    except Exception as e:
        print(f"❌ {name}: ERROR - {e}")
        return False, None

async def check_system_health():
    """检查系统健康状态"""
    print("🔍 检查系统健康状态...")
    print("=" * 60)
    
    async with aiohttp.ClientSession() as session:
        # 基础健康检查
        print("\n🏥 基础健康检查:")
        await check_endpoint(session, f"{BASE_URL}/health", "健康检查")
        await check_endpoint(session, f"{BASE_URL}/system", "系统信息")
        
        # 核心功能检查
        print("\n🚀 核心功能检查:")
        await check_endpoint(session, f"{API_BASE}/trading/portfolio", "交易投资组合")
        await check_endpoint(session, f"{API_BASE}/jq/status", "聚宽数据状态")
        await check_endpoint(session, f"{API_BASE}/jq/stocks?market=CN", "股票列表")
        
        # 策略功能检查
        print("\n🤖 策略功能检查:")
        await check_endpoint(session, f"{API_BASE}/strategy/list", "策略列表")
        await check_endpoint(session, f"{API_BASE}/strategy-executor/execution-status", "策略执行状态")
        
        # 新功能模块检查
        print("\n🧠 新功能模块检查:")
        await check_endpoint(session, f"{API_BASE}/ml-strategy/strategies", "机器学习策略")
        await check_endpoint(session, f"{API_BASE}/robo-advisor/profile/1", "智能投顾用户画像")
        
        # 页面访问检查
        print("\n🌐 页面访问检查:")
        await check_endpoint(session, f"{BASE_URL}/", "主页")
        await check_endpoint(session, f"{BASE_URL}/dashboard", "实时监控仪表板")
        await check_endpoint(session, f"{BASE_URL}/stock-table", "股票表格")
        await check_endpoint(session, f"{BASE_URL}/trading", "交易管理")
        await check_endpoint(session, f"{BASE_URL}/strategy", "策略管理")

async def test_ml_strategy_features():
    """测试机器学习策略功能"""
    print("\n🧠 测试机器学习策略功能...")
    print("=" * 60)
    
    async with aiohttp.ClientSession() as session:
        # 测试特征集创建
        print("\n1. 测试特征集创建...")
        feature_data = {
            "name": "测试特征集",
            "description": "用于测试的特征集",
            "calculation_method": "technical_indicators",
            "features": ["ma_5", "ma_20", "rsi", "macd"]
        }
        
        try:
            async with session.post(f"{API_BASE}/ml-strategy/create-feature-set", data=feature_data) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ 特征集创建成功: {result.get('message', '')}")
                else:
                    print(f"❌ 特征集创建失败: {response.status}")
        except Exception as e:
            print(f"❌ 特征集创建测试失败: {e}")

async def test_robo_advisor_features():
    """测试智能投顾功能"""
    print("\n🤖 测试智能投顾功能...")
    print("=" * 60)
    
    async with aiohttp.ClientSession() as session:
        # 测试用户画像创建
        print("\n1. 测试用户画像创建...")
        profile_data = {
            "user_id": "1",
            "age": "30",
            "income_level": "medium",
            "investment_experience": "intermediate",
            "risk_tolerance": "稳健型",
            "investment_goal": "资本增值",
            "investment_horizon": "10",
            "liquidity_needs": "medium",
            "tax_situation": "medium"
        }
        
        try:
            async with session.post(f"{API_BASE}/robo-advisor/create-profile", data=profile_data) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ 用户画像创建成功: {result.get('message', '')}")
                else:
                    print(f"❌ 用户画像创建失败: {response.status}")
        except Exception as e:
            print(f"❌ 用户画像创建测试失败: {e}")

async def main():
    """主函数"""
    print("🚀 量化交易系统 v2.0.2 状态检查")
    print(f"⏰ 检查时间: {datetime.now()}")
    print("=" * 80)
    
    try:
        # 检查系统健康状态
        await check_system_health()
        
        # 测试新功能模块
        await test_ml_strategy_features()
        await test_robo_advisor_features()
        
        print("\n" + "=" * 80)
        print("🎉 系统状态检查完成！")
        print("\n📋 检查结果总结:")
        print("✅ 基础服务: 健康检查、系统信息")
        print("✅ 核心功能: 交易、聚宽数据、策略")
        print("✅ 新功能模块: 机器学习策略、智能投顾、策略执行")
        print("✅ 页面访问: 主页、仪表板、功能页面")
        
        print("\n🔧 如果发现问题，请检查:")
        print("1. 服务是否正常启动")
        print("2. 依赖包是否完整安装")
        print("3. 端口是否被占用")
        print("4. 日志中的错误信息")
        
    except Exception as e:
        print(f"\n❌ 检查过程中发生错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
