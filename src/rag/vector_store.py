import os
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from src.config import settings

INDEX_DIR = os.path.join(settings.MEDIA_DIR, "vector_store")


def build_index(documents: list[Document], embeddings: Embeddings) -> FAISS:
    index = FAISS.from_documents(documents, embeddings)
    return index


def save_index(index: FAISS, path: str = INDEX_DIR) -> None:
    os.makedirs(path, exist_ok=True)
    index.save_local(path)


def load_index(embeddings: Embeddings, path: str = INDEX_DIR) -> FAISS:
    return FAISS.load_local(path, embeddings, allow_dangerous_deserialization=True)