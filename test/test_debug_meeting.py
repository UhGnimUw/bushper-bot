#!/usr/bin/env python3
"""调试飞书会议预定功能的脚本"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta

def test_meeting_tool():
    """测试两个版本的会议工具"""
    print("=" * 60)
    print("测试飞书会议预定功能")
    print("=" * 60)
    
    # 测试 tool.py 中的版本
    print("\n1. 测试 src/agent/Tools/tool.py 中的 create_meeting")
    try:
        from src.agent.Tools.tool import create_meeting
        start_time = datetime.now() + timedelta(hours=1)
        end_time = start_time + timedelta(hours=1)
        result = create_meeting.invoke({
            "title": "测试会议",
            "start_time": start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "end_time": end_time.strftime("%Y-%m-%d %H:%M:%S"),
            "description": "测试会议描述",
            "location": "线上"
        }, {})
        print(f"结果: {result}")
    except Exception as e:
        print(f"错误: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    
    # 测试 feishu_task_tool.py 中的版本
    print("\n2. 测试 src/agent/Tools/feishu_task_tool.py 中的 create_meeting")
    try:
        from src.agent.Tools.feishu_task_tool import create_meeting
        import time
        start_time = int(time.time()) + 3600
        end_time = start_time + 3600
        result = create_meeting.invoke({
            "summary": "测试会议2",
            "start_time": start_time,
            "end_time": end_time,
            "description": "测试会议描述2",
            "location": "线上"
        }, {})
        print(f"结果: {result}")
    except Exception as e:
        print(f"错误: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

def test_lark_api():
    """直接测试飞书API调用"""
    print("\n" + "=" * 60)
    print("3. 直接测试飞书API调用")
    print("=" * 60)
    
    try:
        import lark_oapi as lark
        import os
        
        client = lark.Client.builder() \
            .app_id(os.getenv("FEISHU_APP_ID", "cli_a97d8246ff38dcd2")) \
            .app_secret(os.getenv("FEISHU_APP_SECRET", "h8vsRaBgt8AvSF8ndvEQsgv5Ly5yl7dl")) \
            .domain(lark.FEISHU_DOMAIN) \
            .log_level(lark.LogLevel.DEBUG) \
            .build()
        
        print("✅ 客户端创建成功")
        print(f"   客户端属性: {dir(client)}")
        
        # 检查 calendar 相关属性
        print("\n检查 calendar 相关属性:")
        if hasattr(client, 'calendar'):
            print(f"  有 calendar 属性")
            print(f"  calendar 属性: {dir(client.calendar)}")
            if hasattr(client.calendar, 'v4'):
                print(f"  有 v4 属性")
                print(f"  v4 属性: {dir(client.calendar.v4)}")
        else:
            print(f"  没有 calendar 属性")
        
    except Exception as e:
        print(f"错误: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_meeting_tool()
    test_lark_api()
