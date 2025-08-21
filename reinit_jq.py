#!/usr/bin/env python3
"""
重新初始化聚宽服务
"""

import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def reinit_jq_service():
    """重新初始化聚宽服务"""
    try:
        print("=" * 50)
        print("🔄 重新初始化聚宽服务")
        print("=" * 50)
        
        # 检查环境变量
        username = os.getenv('JQ_USERNAME')
        password = os.getenv('JQ_PASSWORD')
        
        print(f"环境变量 - 用户名: {username}")
        print(f"环境变量 - 密码: {password[:3]}***{password[-3:] if password else 'None'}")
        
        # 重新初始化聚宽服务
        print("\n🔄 重新初始化聚宽服务...")
        from services.jq_service import reinitialize_jq_service
        
        new_jq_service = reinitialize_jq_service()
        
        print("✅ 聚宽服务重新初始化成功")
        print(f"📊 连接状态: {new_jq_service.connection_status}")
        print(f"🔗 是否连接: {new_jq_service.is_connected}")
        
        # 测试连接
        print("\n🔗 测试连接...")
        import asyncio
        
        async def test_connection():
            status = await new_jq_service.get_connection_status()
            print(f"📊 连接状态: {status}")
            return status['is_connected']
        
        is_connected = asyncio.run(test_connection())
        
        if is_connected:
            print("🎉 聚宽服务重新初始化成功！")
            return True
        else:
            print("❌ 聚宽服务连接失败")
            return False
            
    except Exception as e:
        print(f"❌ 重新初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = reinit_jq_service()
    print("\n" + "=" * 50)
    if success:
        print("🎉 聚宽服务重新初始化成功！")
    else:
        print("💥 聚宽服务重新初始化失败！")
    print("=" * 50)
