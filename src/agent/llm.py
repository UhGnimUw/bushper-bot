from langchain_openai import ChatOpenAI
from langchain_core.embeddings import Embeddings
import os
import httpx
from dotenv import load_dotenv
load_dotenv()


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


# 创建基础模型
base_llm = ChatOpenAI(
    model=os.getenv("local_model_name", "qwen3.5"),
    temperature=float(os.getenv("local_model_temperature", 0.1)),
    base_url=os.getenv("local_model_url", "http://localhost:8989/v1"),
    api_key="not-needed",
    request_timeout=30,
)

# 创建高级模型
advanced_llm = ChatOpenAI(
    model=os.getenv("advanced_model_name", "minimax2.7"),
    temperature=float(os.getenv("advanced_model_temperature", 0.1)),
    base_url=os.getenv("advanced_model_url", ""),
    api_key=os.getenv("advanced_model_api_key", "not-needed"),
    request_timeout=30,
)

# 创建嵌入模型
embedding_model = CustomEmbeddings(
    base_url=os.getenv("embedding_url", "http://localhost:8988"),
    model=os.getenv("embedding_model_name", "bge-m3"),
)


class Reranker:
    """本地 rerank 模型客户端。"""

    def __init__(self, base_url: str, model: str, api_key: str = "not-needed"):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key

    def rerank(self, query: str, documents: list[str], top_n: int = 3) -> list[dict]:
        """调用 rerank API，返回重排序后的文档列表。"""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        payload = {
            "model": self.model,
            "query": query,
            "input": documents,
            "top_n": top_n,
        }
        with httpx.Client() as client:
            response = client.post(
                f"{self.base_url}/v1/rerank",
                json=payload,
                headers=headers,
                timeout=30.0,
            )
            response.raise_for_status()
            result = response.json()
            return result.get("results", result if isinstance(result, list) else [])


# 创建 rerank 模型
rerank_model = Reranker(
    base_url=os.getenv("rerank_url", "http://localhost:8987"),
    model=os.getenv("rerank_model_name", "bge-reranker"),
    api_key=os.getenv("rerank_api_key", "not-needed"),
)
