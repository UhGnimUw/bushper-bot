#!/usr/bin/env python
"""
飞书 Stream 机器人
"""
import argparse
import logging
import os
import json
import threading
import time
from collections import deque
from dotenv import load_dotenv
import lark_oapi as lark
from lark_oapi.api.im.v1 import *

from src.agent.agent import get_agent
from src.agent.agmem import session_store

load_dotenv()

processed_messages: deque = deque(maxlen=200)
_recent_inputs: deque = deque(maxlen=100)  # (chat_id, input_hash, timestamp)

# chat_id -> (last_input_hash, last_input_time, last_chat_id)
# 30分钟内同一chat_id下用户输入内容不变则认为对话结束
_last_input_info: dict = {}
_INPUT_TIMEOUT = 30 * 60  # 30 minutes in seconds


def _session_timeout_checker():
    """后台线程：每5分钟检查一次，30分钟无新输入则换session_id重新开始记录."""
    while True:
        time.sleep(5 * 60)
        now = time.time()
        to_clear = []
        for chat_id, (h, t, _) in list(_last_input_info.items()):
            if now - t >= _INPUT_TIMEOUT:
                to_clear.append(chat_id)
        for chat_id in to_clear:
            session_store.clear_session(chat_id)
            del _last_input_info[chat_id]


_thread = threading.Thread(target=_session_timeout_checker, daemon=True)
_thread.start()


def setup_logger():
    logger = logging.getLogger()
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter('%(asctime)s %(name)-8s %(levelname)-8s %(message)s [%(filename)s:%(lineno)d]'))
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger


def define_options():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--app_id', dest='app_id',
        default=os.getenv('FEISHU_APP_ID', 'cli_a97d8246ff38dcd2'),
        help='App ID from Feishu open platform')
    parser.add_argument(
        '--app_secret', dest='app_secret',
        default=os.getenv('FEISHU_APP_SECRET', 'h8vsRaBgt8AvSF8ndvEQsgv5Ly5yl7dl'),
        help='App Secret from Feishu open platform')
    return parser.parse_args()


def agent_response(user_input: str, chat_id: str, logger) -> str:
    if user_input.strip().lower() in ["清除历史", "reset", "clear"]:
        session_store.clear_session(chat_id)
        _last_input_info.pop(chat_id, None)
        return "已清除会话历史"

    input_hash = hash(user_input.strip())
    now = time.time()

    # 检测30分钟超时：同chat_id+同输入 → 换session重启
    if chat_id in _last_input_info:
        prev_hash, prev_time, prev_chat_id = _last_input_info[chat_id]
        if input_hash == prev_hash and now - prev_time < _INPUT_TIMEOUT:
            # 内容重复且未超时，沿用原session
            session_id = chat_id
        elif now - prev_time >= _INPUT_TIMEOUT:
            # 超时：清除历史，用原chat_id作为新session
            session_store.clear_session(chat_id)
            session_id = chat_id
        else:
            # 内容变化，正常继续
            session_id = chat_id
    else:
        session_id = chat_id

    _last_input_info[chat_id] = (input_hash, now, chat_id)

    try:
        agent = get_agent(user_input, session_id)
        if agent is None:
            return "无法理解您的意图，请重试。"
        return agent.invoke(user_input, session_id)
    except Exception as e:
        logger.error('Agent调用出错: %s', str(e))
        return f"抱歉，处理出错了：{str(e)}"


def do_p2_im_message_receive_v1(data: P2ImMessageReceiveV1) -> None:
    logger = logging.getLogger(__name__)
    try:
        msg_id = getattr(getattr(data.event, "message", None), "message_id", None)
        if not msg_id:
            logger.warning("缺少 message_id，跳过消息")
            return

        if msg_id in processed_messages:
            logger.warning(f"重复消息已跳过: {msg_id}")
            return
        processed_messages.append(msg_id)

        sender = getattr(getattr(data.event, "sender", None), "sender_type", None)
        if sender == "bot":
            logger.info("机器人自身消息，跳过")
            return

        chat_id = getattr(getattr(data.event, "message", None), "chat_id", "unknown-chat")
        raw_content = getattr(getattr(data.event, "message", None), "content", "")

        user_input = raw_content
        try:
            content_json = json.loads(raw_content)
            if 'text' in content_json:
                user_input = content_json['text']
        except Exception:
            pass

        # 5秒内同chat_id+同内容去重
        input_hash = hash((chat_id, user_input.strip()))
        now = time.time()
        for cid, inh, ts in _recent_inputs:
            if cid == chat_id and inh == input_hash and now - ts < 5:
                logger.warning(f"5秒内重复输入已跳过: {user_input[:30]}")
                return
        _recent_inputs.append((chat_id, input_hash, now))

        logger.info('收到用户消息 [%s]: %s', chat_id, user_input)
        response = agent_response(user_input, chat_id, logger)
        logger.info('Agent回复 [%s]: %s', chat_id, response)

        api_client = (
            lark.Client.builder()
            .app_id(os.getenv('FEISHU_APP_ID', 'cli_a97d8246ff38dcd2'))
            .app_secret(os.getenv('FEISHU_APP_SECRET', 'h8vsRaBgt8AvSF8ndvEQsgv5Ly5yl7dl'))
            .domain(lark.FEISHU_DOMAIN)
            .log_level(lark.LogLevel.DEBUG)
            .build()
        )

        reply_req = (
            ReplyMessageRequest.builder()
            .message_id(msg_id)
            .request_body({
                "msg_type": "text",
                "content": json.dumps({"text": response}),
            })
            .build()
        )
        reply_res = api_client.im.v1.message.reply(reply_req)

        if not reply_res.success():
            logger.error('发送消息失败: %s', getattr(reply_res, "msg", "unknown error"))
        else:
            logger.info('发送成功 [%s]', chat_id)

    except Exception as e:
        logger.error('处理消息异常: %s', str(e), exc_info=True)


def main():
    logger = setup_logger()
    options = define_options()

    event_handler = (
        lark.EventDispatcherHandler.builder("", "")
        .register_p2_im_message_receive_v1(do_p2_im_message_receive_v1)
        .build()
    )

    ws_client = lark.ws.Client(
        app_id=options.app_id,
        app_secret=options.app_secret,
        event_handler=event_handler,
        log_level=lark.LogLevel.INFO,
    )

    try:
        logger.info('WebSocket 连接启动...')
        ws_client.start()
    except KeyboardInterrupt:
        logger.info('WebSocket 连接关闭...')


if __name__ == '__main__':
    main()
