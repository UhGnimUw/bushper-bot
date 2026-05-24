import os
import dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.runnables import RunnablePassthrough
from langchain_core.embeddings import Embeddings
import httpx
import numpy as np


class CustomEmbeddings(Embeddings):
    def __init__(self, base_url: str, model: str):
        self.base_url = base_url.rstrip("/")
        self.model = model

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        headers = {"Content-Type": "application/json"}
        payload = {"model": self.model, "input": texts}
        with httpx.Client() as client:
            response = client.post(f"{self.base_url}/v1/embeddings", json=payload, timeout=30.0)
            response.raise_for_status()
            result = response.json()
            if isinstance(result, list):
                return result
            return [item["embedding"] for item in result["data"]]

    def embed_query(self, text: str) -> list[float]:
        return self.embed_documents([text])[0]


from langchain_community.vectorstores import Chroma





dotenv.load_dotenv()

import yaml


with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

llm = ChatOpenAI(model=config["local_model_name"], temperature=config["local_model_temperature"], base_url=config["local_model_url"], api_key="not-needed")

embedding_model = CustomEmbeddings(base_url=config["embedding_url"], model=config["embedding_model_name"])


# --- 1. 准备知识文档 ---
# 实际项目中，这些文档可以从文件、网页、数据库等加载
documents = [
    "LangChain 是一个用于构建大语言模型应用的开源框架，由 Harrison Chase 于 2022 年创建。",
    "LangChain 的核心组件包括：模型接口、提示词模板、链、记忆、检索和代理。",
    "LCEL（LangChain Expression Language）是 LangChain 的新一代链构建语法，使用管道符 | 连接各组件。",
    "RAG（检索增强生成）通过在生成前检索相关文档，让 LLM 能回答训练数据之外的问题。",
    "LangGraph 是 LangChain 团队推出的新框架，专门用于构建复杂的多步骤 AI 代理工作流。",
    "LangSmith 是 LangChain 的可观测性平台，用于调试、测试和监控 LLM 应用。",
    "OpenAI 于 2015 年由 Sam Altman、Elon Musk 等人创立，是人工智能研究领域的领军企业。",
    "GPT（Generative Pre-trained Transformer）是 OpenAI 开发的大型语言模型系列，采用 Transformer 架构。",
    "ChatGPT 于 2022 年 11 月发布，迅速成为历史上增长最快的消费级应用之一。",
    "GPT-4 是 OpenAI 发布的多模态大语言模型，支持文本和图像输入，具备更强的推理能力。",
    "OpenAI API 允许开发者通过简单的接口调用 GPT 模型，集成到自己的应用程序中。",
    "微调（Fine-tuning）是指在预训练模型的基础上，使用特定领域数据进一步训练以优化性能。",
    "提示工程（Prompt Engineering）是设计和优化输入提示以获得更好模型输出的技术和实践。",
    "向量数据库专门用于存储和检索高维向量，是 RAG 系统的核心组件之一。",
    "Hugging Face 是一个机器学习社区和平台，提供大量开源模型和数据集以及 Transformers 库。",
    "LoRA（Low-Rank Adaptation）是一种高效的模型微调方法，通过低秩矩阵减少训练参数。",
]


text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=100,
    chunk_overlap=20,
)

text = text_splitter.create_documents(documents)


chromadb = Chroma.from_documents(text, embedding_model, persist_directory="./chroma_db", collection_name="rag_collection")

retval = chromadb.as_retriever(search_type="similarity", search_kwargs={"k": 3})

rag_prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个知识助手。根据以下检索到的上下文来回答问题。如果上下文中没有答案，就说你不知道。\n <retval_content> 上下文：{context} </retval_content>"),
    ("human", "{input}")
])

def format_documents(documents):
    return "\n".join([doc.page_content for doc in documents])

rag_chain = (
    {"context": retval | format_documents, "input": RunnablePassthrough()}
    | rag_prompt
    | llm 
    | StrOutputParser()
)
# input = "LangChain 的核心组件有哪些？"
input = "暗夜只狼是什么"
print(f"问题：{input}")
print(f"回答：{rag_chain.invoke(input)}")
