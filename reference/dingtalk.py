#!/usr/bin/env python
import argparse
import logging
import os
from dotenv import load_dotenv
from dingtalk_stream import AckMessage
import dingtalk_stream
from langchain.agents import initialize_agent, Tool
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferMemory

load_dotenv()

def setup_logger():
    logger = logging.getLogger()
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter('%(asctime)s %(name)-8s %(levelname)-8s %(message)s [%(filename)s:%(lineno)d]'))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger

def define_options():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--client_id', dest='client_id', 
        default=os.getenv('DINGTALK_CLIENT_ID', 'dingguarunyn2qx0nx2e'),
        help='app_key or suite_key from https://open-dev.digntalk.com'
    )
    parser.add_argument(
        '--client_secret', dest='client_secret', 
        default=os.getenv('DINGTALK_CLIENT_SECRET', 'mA3sXhIGZkn1tRZmaSHBqTj0S5a98LrghlfEJu4Moa3scYscv6SAQ6EPFUY4lOQ-'),
        help='app_secret or suite_secret from https://open-dev.digntalk.com'
    )
    options = parser.parse_args()
    return options

# 定义LangChain Agent
def create_agent():
    tools = [
        Tool(
            name="知识库查询",
            func=lambda q: f"模拟查询结果：关于'{q}'的信息",
            description="查询内部知识库"
        ),
        # 可以添加更多工具
    ]
    # 使用配置文件中的本地模型
    llm = ChatOpenAI(
        model=os.getenv("local_model_name", "qwen3.5"), 
        temperature=float(os.getenv("local_model_temperature", 0.1)), 
        base_url=os.getenv("local_model_url", "http://localhost:8989/v1"), 
        api_key="not-needed"
    )
    memory = ConversationBufferMemory(memory_key="chat_history")
    agent = initialize_agent(
        tools, llm, agent="conversational-react-description",
        memory=memory, verbose=True
    )
    return agent

agent = create_agent()

class LangChainBotHandler(dingtalk_stream.ChatbotHandler):
    def __init__(self, logger: logging.Logger = None):
        super(LangChainBotHandler, self).__init__()
        if logger:
            self.logger = logger

    async def process(self, callback: dingtalk_stream.CallbackMessage):
        incoming_message = dingtalk_stream.ChatbotMessage.from_dict(callback.data)
        user_input = incoming_message.text.content.strip()
        
        self.logger.info('收到用户消息: %s' % user_input)
        
        try:
            response = agent.run(user_input)
            self.logger.info('Agent回复: %s' % response)
            self.reply_text(response, incoming_message)
        except Exception as e:
            self.logger.error('处理消息出错: %s' % str(e))
            self.reply_text(f'抱歉，处理出错了：{str(e)}', incoming_message)

        return AckMessage.STATUS_OK, 'OK'

def main():
    logger = setup_logger()
    options = define_options()

    credential = dingtalk_stream.Credential(options.client_id, options.client_secret)
    client = dingtalk_stream.DingTalkStreamClient(credential)
    client.register_callback_handler(dingtalk_stream.chatbot.ChatbotMessage.TOPIC, LangChainBotHandler(logger))
    logger.info('钉钉Stream机器人已启动，等待消息...')
    client.start_forever()

if __name__ == '__main__':
    main()
