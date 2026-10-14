import os
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from src.config import settings


def load_and_chunk_knowledge_base(
    chunk_size: int = 700,
    chunk_overlap: int = 100,
) -> list[Document]:
    kb_path = os.path.join(settings.MEDIA_DIR, "knowledge_base")
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
    )

    all_chunks = []
    for category in ("security", "architecture", "performance"):
        category_path = os.path.join(kb_path, category)
        if not os.path.isdir(category_path):
            continue

        for filename in os.listdir(category_path):
            if not filename.endswith(".md"):
                continue

            filepath = os.path.join(category_path, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                text = f.read()

            docs = splitter.create_documents(
                texts=[text],
                metadatas=[{
                    "source": filename,
                    "category": category,
                }],
            )
            for i, doc in enumerate(docs):
                doc.metadata["chunk_index"] = i

            all_chunks.extend(docs)

    return all_chunks