import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.rag.retriever import KnowledgeRetriever


def main():
    retriever = KnowledgeRetriever()

    print("--- Security query: 'SQL injection' ---")
    for doc in retriever.retrieve_for_security("SQL injection"):
        print(f"  [{doc.metadata['source']}] chunk {doc.metadata['chunk_index']}")

    print("\n--- Architecture query: 'god class tight coupling' ---")
    for doc in retriever.retrieve_for_architecture("god class tight coupling"):
        print(f"  [{doc.metadata['source']}] chunk {doc.metadata['chunk_index']}")

    print("\n--- Performance query: 'N+1 query problem' ---")
    for doc in retriever.retrieve_for_performance("N+1 query problem"):
        print(f"  [{doc.metadata['source']}] chunk {doc.metadata['chunk_index']}")

    print("\nRetriever works!")


if __name__ == "__main__":
    main()
