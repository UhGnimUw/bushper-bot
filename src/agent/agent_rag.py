"""RAG agent — knowledge base search with tiered ChromaDB vector store.

Tier permissions:
- T0: can query all collections (tier0, tier1, tier2, tier3)
- T1: can query tier1, tier2, tier3
- T2: can query tier2, tier3
- T3: can query tier3 only

Singleton: use get_rag_agent() from agent.py to get the instance.
"""
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.messages import HumanMessage
from langchain_chroma import Chroma
from src.agent.llm import embedding_model, base_llm
from src.agent.agmem import get_session_history
from src.agent.rag_permission import resolve_tier_from_prompt
import logging
logger = logging.getLogger(__name__)


# Tier → allowed collections (order matters for multi-collection retrieval)
TIER_COLLECTIONS = {
    "T0": ["tier0", "tier1", "tier2", "tier3"],
    "T1": ["tier1", "tier2", "tier3"],
    "T2": ["tier2", "tier3"],
    "T3": ["tier3"],
}


class RAGAgent:
    """Tiered knowledge-base RAG agent.

    Singleton — get instance via get_rag_agent() in agent.py.
    Chains are built lazily per collection on first invoke().
    """
    _instance = None

    def __init__(self, persist_directory="./chroma_db"):
        # Guard: if already fully initialized, skip
        if getattr(self, "_initialized", False):
            return
        self._persist_directory = persist_directory
        self._chains = {}   # collection_name -> rag_chain
        self._chromadb = {} # collection_name -> Chroma client
        self._initialized = True

    def _get_chroma(self, collection_name: str) -> Chroma:
        """Get or create Chroma client for a collection."""
        if collection_name not in self._chromadb:
            self._chromadb[collection_name] = Chroma(
                persist_directory=self._persist_directory,
                collection_name=collection_name,
                embedding_function=embedding_model,
            )
        return self._chromadb[collection_name]

    def _ensure_chain(self, collection_name: str):
        """Build RAG chain lazily for a collection."""
        if collection_name in self._chains:
            return

        chromadb = self._get_chroma(collection_name)
        retriever = chromadb.as_retriever(
            search_type="similarity", search_kwargs={"k": 3}
        )

        rag_prompt = ChatPromptTemplate.from_messages([
            ("system",
             "你是一个知识助手。根据以下检索到的上下文来回答问题。\n"
             "如果参考中没有答案，就说你不知道，不要编造。\n\n"
             "<context>：{context}</context>"),
            ("human", "{input}"),
        ])

        def _format(docs):
            return "\n".join(doc.page_content for doc in docs)

        self._chains[collection_name] = (
            {"context": retriever | _format, "input": RunnablePassthrough()}
            | rag_prompt
            | base_llm
            | StrOutputParser()
        )

    def retrieve(self, user_input: str, collections: list[str] = None) -> str:
        """Retrieve from one or more collections, return concatenated docs after rerank."""
        if collections is None:
            collections = ["tier0"]  # fallback
        results = []
        for col in collections:
            self._ensure_chain(col)
            chromadb = self._get_chroma(col)
            docs = chromadb.as_retriever(
                search_type="similarity", search_kwargs={"k": 5}
            ).invoke(user_input)
            results.extend(doc.page_content for doc in docs)

        # Rerank
        if results:
            from src.agent.llm import rerank_model
            reranked = rerank_model.rerank(user_input, results, top_n=3)
            results = [item["text"] if isinstance(item, dict) else item for item in reranked]

        return "\n".join(results) if results else ""

    def synthesize(self, user_input: str, context: str, session_id: str) -> str:
        """Synthesis with history."""
        history = get_session_history(session_id)
        history_messages = history.messages if hasattr(history, "messages") else []

        system_template = (
            "你是一个知识助手。根据以下检索到的上下文来回答问题。\n"
            "如果上下文中没有答案，就说你不知道，不要编造。\n"
            "回答的内容不要超出检索到的内容范围。\n\n"
            "<context>上下文：{context}</context>"
        )
        human_template = "{input}\n\n对话历史：{history}"

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_template),
            ("human", human_template),
        ])

        def _format_history(msgs):
            return "\n".join(
                f"{'用户' if isinstance(m, HumanMessage) else '助手'}: {m.content}"
                for m in history_messages
            )

        synthesis_chain = (
            {
                "context": lambda _: context,
                "input": lambda _: user_input,
                "history": lambda _: _format_history(history_messages),
            }
            | prompt
            | base_llm
            | StrOutputParser()
        )
        return synthesis_chain.invoke({})

    def invoke(self, user_input: str, session_id: str = None, tier: str = None) -> str:
        """Tier-aware invoke."""

        if tier is None:
            user_name, tier = resolve_tier_from_prompt(user_input)
            print(f"[RAG] user_name={user_name}, tier={tier}")

        collections = TIER_COLLECTIONS.get(tier, ["tier3"]) if tier else ["tier3"]
        print(f"[RAG] collections={collections}")
        context = self.retrieve(user_input, collections)
        print(f"[RAG] context_len={len(context)}")
        if not context:
            return "未检索到相关内容"
        return self.synthesize(user_input, context, session_id)

def load_tier_test_data(persist_directory="./chroma_db"):
    """Load test documents into tier0, tier1, tier2, tier3 collections."""
    tier_docs = {
        "tier0": [
            "【T0机密】公司战略规划：2026年目标实现营收100亿，进入世界500强。",
            "【T0机密】董事会决议：任命王刚为新任CEO，全面负责公司运营。",
            "【T0机密】并购计划：拟收购某新能源公司，交易金额50亿。",
        ],
        "tier1": [
            "【T1内部】部门季度汇报：研发部Q1完成3个核心模块开发。",
            "【T1内部】技术方案：新一代分布式架构设计文档已完成评审。",
            "【T1内部】人员调动：李明调入战略规划部，张伟接管研发组。",
        ],
        "tier2": [
            "【T2受限】项目进度：APP 3.0版本开发完成60%，预计6月上线。",
            "【T2受限】测试报告：上周自动化测试覆盖率提升至85%。",
            "【T2受限】上线清单：V3.0.1版本功能清单及回滚方案。",
        ],
        "tier3": [
            "【T3公开】用户指南：APP新版本功能介绍及使用方法。输入密码123654，即可登录。",
            "【T3公开】常见问题：FAQ - 如何注册、如何找回密码。",
            "【T3公开】版本更新：V3.0.1更新日志。",
        ],
    }

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=100, chunk_overlap=20)

    for collection_name, docs in tier_docs.items():
        texts = text_splitter.create_documents(docs)
        Chroma.from_documents(
            texts,
            embedding_model,
            persist_directory=persist_directory,
            collection_name=collection_name,
        )
        print(f"Loaded {len(docs)} docs into collection '{collection_name}'")


if __name__ == "__main__":
    import sys
    persist_dir = sys.argv[1] if len(sys.argv) > 1 else "./chroma_db"

    if len(sys.argv) > 2 and sys.argv[2] == "--load-data":
        load_tier_test_data(persist_dir)
    else:
        rag = RAGAgent(persist_dir)
        # T3 user test
        q = "我是刘洋，检索 APP新版本功能介绍"
        print(f"问题：{q}")
        print(f"回答：{rag.invoke(q)}")
