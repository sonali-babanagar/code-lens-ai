from langchain_core.documents import Document
from src.rag.vector_store import load_index
from src.agents.llm.azure_client import get_embedding


class KnowledgeRetriever:
    def __init__(self):
        self._embeddings = get_embedding()
        self._index = load_index(self._embeddings)

    def retrieve(self, query: str, category: str | None = None, top_k: int = 5) -> list[Document]:
        results = self._index.similarity_search(query, k=top_k * 3 if category else top_k)
        if category:
            results = [r for r in results if r.metadata.get("category") == category]
            results = results[:top_k]
        return results

    def retrieve_for_security(self, query: str, top_k: int = 5) -> list[Document]:
        return self.retrieve(query, category="security", top_k=top_k)

    def retrieve_for_architecture(self, query: str, top_k: int = 5) -> list[Document]:
        return self.retrieve(query, category="architecture", top_k=top_k)

    def retrieve_for_performance(self, query: str, top_k: int = 5) -> list[Document]:
        return self.retrieve(query, category="performance", top_k=top_k)
