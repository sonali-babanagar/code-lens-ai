import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.rag.chunker import load_and_chunk_knowledge_base
from src.rag.vector_store import build_index, save_index
from src.agents.llm.azure_client import get_embedding


def main():
    print("Loading and chunking knowledge base...")
    chunks = load_and_chunk_knowledge_base()
    print(f"Created {len(chunks)} chunks from knowledge base")

    if not chunks:
        print("No chunks found. Add .md files to media/knowledge_base/")
        return

    categories = {}
    for chunk in chunks:
        cat = chunk.metadata["category"]
        categories[cat] = categories.get(cat, 0) + 1
    for cat, count in sorted(categories.items()):
        print(f"  {cat}: {count} chunks")

    print("\nGenerating embeddings and building FAISS index...")
    embeddings = get_embedding()
    index = build_index(chunks, embeddings)

    print("Saving index to media/vector_store/")
    save_index(index)
    print("Done!")


if __name__ == "__main__":
    main()