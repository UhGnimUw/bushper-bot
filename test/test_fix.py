#!/usr/bin/env python3
"""测试修复后的飞书API调用"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """测试是否可以正确导入所需的类"""
    print("=== 测试导入 ===")
    try:
        from lark_oapi.api.calendar.v4 import (
            CreateCalendarEventRequest,
            CreateCalendarEventRequestBody,
            EventTime,
            Attendee,
            Reminder,
            CreateCalendarEventAttendeeRequest,
            CreateCalendarEventAttendeeRequestBody,
            CreateCalendarEventMeetingMinuteRequest,
            CreateCalendarEventMeetingMinuteRequestBody,
            Note,
            ListCalendarEventRequest,
        )
        print("✅ 所有导入成功")
        return True
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_client():
    """测试创建客户端和访问API结构"""
    print("\n=== 测试客户端和API结构 ===")
    try:
        import lark_oapi as lark
        
        client = lark.Client.builder() \
            .app_id(os.getenv("FEISHU_APP_ID", "cli_a97d8246ff38dcd2")) \
            .app_secret(os.getenv("FEISHU_APP_SECRET", "h8vsRaBgt8AvSF8ndvEQsgv5Ly5yl7dl")) \
            .domain(lark.FEISHU_DOMAIN) \
            .log_level(lark.LogLevel.INFO) \
            .build()
        
        # 检查是否有正确的API结构
        assert hasattr(client, 'calendar'), "客户端没有 calendar 属性"
        assert hasattr(client.calendar, 'v4'), "calendar 没有 v4 属性"
        assert hasattr(client.calendar.v4, 'calendar_event'), "v4 没有 calendar_event 属性"
        assert hasattr(client.calendar.v4, 'calendar_event_attendee'), "v4 没有 calendar_event_attendee 属性"
        assert hasattr(client.calendar.v4, 'calendar_event_meeting_minute'), "v4 没有 calendar_event_meeting_minute 属性"
        
        print("✅ 客户端和API结构正确")
        return True
    except Exception as e:
        print(f"❌ 客户端测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success1 = test_imports()
    success2 = test_client()
    
    if success1 and success2:
        print("\n🎉 所有测试通过！修复应该是正确的。")
    else:
        print("\n❌ 部分测试失败")
        sys.exit(1)
