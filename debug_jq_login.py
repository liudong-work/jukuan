#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
调试聚宽登录功能
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def debug_jq_login():
    """调试聚宽登录功能"""
    try:
        print("=== 调试聚宽登录功能 ===")
        
        # 1. 检查模块导入
        print("1. 检查模块导入...")
        from src.utils.joinquant_login import create_login_section, login_joinquant
        print("   ✅ 模块导入成功")
        
        # 2. 检查登录区域创建
        print("2. 检查登录区域创建...")
        login_section = create_login_section()
        print(f"   ✅ 登录区域创建成功，类型: {type(login_section)}")
        
        # 3. 检查组件ID - 使用更准确的方法
        print("3. 检查组件ID...")
        section_str = str(login_section)
        print(f"   组件字符串长度: {len(section_str)}")
        print(f"   组件字符串前500字符: {section_str[:500]}")
        
        # 检查关键ID
        ids_to_check = [
            "connect-jq",
            "jq-username", 
            "jq-password",
            "operation-status"
        ]
        
        for id_name in ids_to_check:
            if f'id="{id_name}"' in section_str:
                print(f"   ✅ {id_name} ID存在")
            elif f"id='{id_name}'" in section_str:
                print(f"   ✅ {id_name} ID存在 (单引号)")
            else:
                print(f"   ❌ {id_name} ID不存在")
                # 搜索包含该ID的字符串
                if id_name in section_str:
                    print(f"      ⚠️  {id_name} 在字符串中找到，但可能格式不对")
        
        # 4. 测试登录函数
        print("4. 测试登录函数...")
        success, message = login_joinquant("test_user", "test_password", False)
        print(f"   ✅ 登录函数测试成功: {success}, {message}")
        
        print("✅ 聚宽登录功能调试完成")
        
    except Exception as e:
        print(f"❌ 调试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_jq_login()
