import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

load_dotenv()


llm = ChatOpenAI(model=os.getenv("local_model_name"), temperature=float(os.getenv("local_model_temperature")), base_url=os.getenv("local_model_url"), api_key="not-needed")

prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个乐于助人的 AI 助手。"),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{question}"),
])

chain = prompt | llm

store = {}

def get_session_history(session_id: str) -> BaseChatMessageHistory:
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]

with_message_history = RunnableWithMessageHistory(chain,get_session_history,input_messages_key="question",history_messages_key="history")


print("--- 已进入 DeepSeek 聊天模式 (输入 'exit' 退出) ---")
session_config = {"configurable": {"session_id": "user1_001"}}

while True:
    user_input = input("用户: ")
    if user_input.lower() in ["exit", "quit", "退出"]:
        break
    result = with_message_history.invoke({"question": user_input}, config=session_config)
    
    print(f"AI: {result.content}\n")



