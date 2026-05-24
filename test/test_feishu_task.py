#!/usr/bin/env python
"""飞书任务功能测试 — 测试定时发送消息、会议预定、会议纪要功能。"""
import sys
import os
import time
import pytest
import inspect
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestIntentRecognition:
    """1. 意图识别测试 (NLU)"""

    def test_feishu_task_intent_exists(self):
        """测试feishu_task意图是否存在于intend_map中"""
        from src.agent.intend import intend_map
        assert "feishu_task" in intend_map, "intend_map中缺少feishu_task意图"

    def test_feishu_task_intent_description(self):
        """测试feishu_task意图的描述"""
        from src.agent.intend import intend_map
        feishu_task_intent = intend_map.get("feishu_task")
        assert feishu_task_intent is not None
        assert "description" in feishu_task_intent
        assert len(feishu_task_intent["description"]) > 0


class TestToolFunctionSignatures:
    """5. 工具函数签名测试"""

    def test_schedule_message_signature(self):
        """测试schedule_message函数签名"""
        from src.agent.Tools.feishu_task_tool import schedule_message
        func = schedule_message.func if hasattr(schedule_message, 'func') else schedule_message
        sig = inspect.signature(func)
        params = list(sig.parameters.keys())
        assert "receive_id" in params
        assert "content" in params

    def test_create_meeting_signature(self):
        """测试create_meeting函数签名"""
        from src.agent.Tools.feishu_task_tool import create_meeting
        func = create_meeting.func if hasattr(create_meeting, 'func') else create_meeting
        sig = inspect.signature(func)
        params = list(sig.parameters.keys())
        assert "summary" in params
        assert "start_time" in params
        assert "end_time" in params

    def test_create_meeting_minutes_signature(self):
        """测试create_meeting_minutes函数签名"""
        from src.agent.Tools.feishu_task_tool import create_meeting_minutes
        func = create_meeting_minutes.func if hasattr(create_meeting_minutes, 'func') else create_meeting_minutes
        sig = inspect.signature(func)
        params = list(sig.parameters.keys())
        assert "event_id" in params
        assert "title" in params
        assert "content" in params

    def test_feishu_task_tools_list(self):
        """测试feishu_task_tools列表"""
        from src.agent.Tools.feishu_task_tool import feishu_task_tools
        assert isinstance(feishu_task_tools, list)
        assert len(feishu_task_tools) >= 3

    def test_task_tool_list_exists(self):
        """测试task_tool_list列表是否存在"""
        from src.agent.Tools.tool import task_tool_list
        assert isinstance(task_tool_list, list)


class TestScheduledMessageQueue:
    """2. 定时消息队列测试"""

    def test_schedule_message_valid(self):
        """测试定时消息设置"""
        from src.agent.Tools.feishu_task_tool import schedule_message

        future_time = int(time.time()) + 3600

        with patch("src.agent.Tools.feishu_task_tool.get_feishu_client") as mock_client:
            mock_response = MagicMock()
            mock_response.success.return_value = True
            mock_response.data = MagicMock()
            mock_response.data.message_id = "test_msg_id"
            mock_response.data.schedule_time = future_time
            mock_response.data.status = "sent"

            mock_client.return_value.im.v1.message.create.return_value = mock_response

            result = schedule_message.invoke(
                {"receive_id": "test_chat_id", "content": "测试消息", "schedule_time": future_time},
                {}
            )

        assert "消息已安排发送" in result or "message_id" in result

    def test_schedule_message_immediate(self):
        """测试立即发送消息"""
        from src.agent.Tools.feishu_task_tool import schedule_message

        with patch("src.agent.Tools.feishu_task_tool.get_feishu_client") as mock_client:
            mock_response = MagicMock()
            mock_response.success.return_value = True
            mock_response.data = MagicMock()
            mock_response.data.message_id = "test_msg_id"
            mock_response.data.schedule_time = int(time.time()) + 60
            mock_response.data.status = "sent"

            mock_client.return_value.im.v1.message.create.return_value = mock_response

            result = schedule_message.invoke(
                {"receive_id": "test_chat_id", "content": "立即发送测试"},
                {}
            )

        assert "消息已安排发送" in result or "message_id" in result


class TestFeishuTaskAgent:
    """3. FeishuTaskAgent初始化测试"""

    def test_feishu_task_agent_exists(self):
        """测试FeishuTaskAgent类是否存在"""
        from src.agent.agent_feishu_task import FeishuTaskAgent
        assert FeishuTaskAgent is not None

    def test_feishu_task_agent_is_singleton(self):
        """测试FeishuTaskAgent是单例"""
        from src.agent.agent_feishu_task import FeishuTaskAgent
        instance1 = FeishuTaskAgent()
        instance2 = FeishuTaskAgent()
        assert instance1 is instance2

    def test_feishu_task_agent_has_invoke(self):
        """测试FeishuTaskAgent有invoke方法"""
        from src.agent.agent_feishu_task import FeishuTaskAgent
        agent = FeishuTaskAgent()
        assert hasattr(agent, "invoke")
        assert callable(agent.invoke)


class TestAgentRouting:
    """4. Agent路由测试"""

    def test_get_agent_returns_feishu_task(self):
        """测试get_agent对飞书任务意图返回FeishuTaskAgent"""
        from src.agent.agent import get_agent

        with patch("src.agent.agent.NLU") as mock_nlu:
            mock_result = MagicMock()
            mock_result.intend = "feishu_task"
            mock_nlu.return_value = mock_result

            agent = get_agent("帮我预定明天下午3点的会议", "test_session")
            assert agent is not None
            assert hasattr(agent, "invoke")

    def test_get_agent_feishu_task_invoke(self):
        """测试FeishuTaskAgent的invoke方法"""
        from src.agent.agent import get_agent

        with patch("src.agent.agent.NLU") as mock_nlu:
            mock_result = MagicMock()
            mock_result.intend = "feishu_task"
            mock_nlu.return_value = mock_result

            agent = get_agent("明天上午10点发送消息", "test_session")
            assert callable(agent.invoke)


class TestMeetingBooking:
    """会议预定功能测试"""

    def test_create_meeting_valid_times(self):
        """测试有效时间的会议预定"""
        from src.agent.Tools.feishu_task_tool import create_meeting

        start_ts = int(time.time()) + 3600
        end_ts = int(time.time()) + 7200

        with patch("src.agent.Tools.feishu_task_tool.get_feishu_client") as mock_client:
            mock_response = MagicMock()
            mock_response.success.return_value = True
            mock_response.data = MagicMock()
            mock_response.data.event = MagicMock()
            mock_response.data.event.event_id = "test_event_id"
            mock_response.data.event.summary = "测试会议"
            mock_response.data.event.start_time = MagicMock()
            mock_response.data.event.start_time.timestamp = str(start_ts)
            mock_response.data.event.end_time = MagicMock()
            mock_response.data.event.end_time.timestamp = str(end_ts)
            mock_response.data.event.meeting_minute_enable = True

            mock_client.return_value.calendar.v4.calendar.event.create.return_value = mock_response

            result = create_meeting.invoke(
                {
                    "summary": "测试会议",
                    "start_time": start_ts,
                    "end_time": end_ts,
                    "description": "测试描述"
                },
                {}
            )

        assert "会议创建成功" in result or "event_id" in result

    def test_create_meeting_default_times(self):
        """测试使用默认时间的会议预定"""
        from src.agent.Tools.feishu_task_tool import create_meeting

        with patch("src.agent.Tools.feishu_task_tool.get_feishu_client") as mock_client:
            mock_response = MagicMock()
            mock_response.success.return_value = True
            mock_response.data = MagicMock()
            mock_response.data.event = MagicMock()
            mock_response.data.event.event_id = "test_event_id"
            mock_response.data.event.summary = "测试会议"
            mock_response.data.event.start_time = MagicMock()
            mock_response.data.event.start_time.timestamp = str(int(time.time()) + 3600)
            mock_response.data.event.end_time = MagicMock()
            mock_response.data.event.end_time.timestamp = str(int(time.time()) + 7200)
            mock_response.data.event.meeting_minute_enable = True

            mock_client.return_value.calendar.v4.calendar.event.create.return_value = mock_response

            result = create_meeting.invoke(
                {"summary": "测试会议"},
                {}
            )

        assert "会议创建成功" in result or "event_id" in result


class TestMeetingNotesRecording:
    """会议纪要记录功能测试"""

    def test_create_meeting_minutes_basic(self):
        """测试基本会议纪要记录"""
        from src.agent.Tools.feishu_task_tool import create_meeting_minutes

        with patch("src.agent.Tools.feishu_task_tool.get_feishu_client") as mock_client:
            mock_response = MagicMock()
            mock_response.success.return_value = True
            mock_response.data = MagicMock()
            mock_response.data.meeting_minute = MagicMock()
            mock_response.data.meeting_minute.note_id = "test_note_id"

            mock_client.return_value.calendar.v4.calendar.event.meeting_minute.create.return_value = mock_response

            content = [{"tag": "paragraph", "text": "测试内容"}]
            result = create_meeting_minutes.invoke(
                {
                    "event_id": "test_event_id",
                    "title": "测试会议纪要",
                    "content": content
                },
                {}
            )

        assert "会议纪要创建成功" in result or "note_id" in result

    def test_get_meeting_list(self):
        """测试获取会议列表"""
        from src.agent.Tools.feishu_task_tool import get_meeting_list

        with patch("src.agent.Tools.feishu_task_tool.get_feishu_client") as mock_client:
            mock_response = MagicMock()
            mock_response.success.return_value = True
            mock_response.data = MagicMock()
            mock_event = MagicMock()
            mock_event.summary = "会议1"
            mock_event.event_id = "event1"
            mock_event.start_time = MagicMock()
            mock_event.start_time.timestamp = str(int(time.time()))
            mock_response.data.items = [mock_event]

            mock_client.return_value.calendar.v4.calendar.event.list.return_value = mock_response

            result = get_meeting_list.invoke({}, {})

        assert "会议列表" in result or "暂无会议" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])