import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agents.llm.azure_client import get_llm, get_embedding

def test_chat():
    llm = get_llm()
    response = llm.invoke("Say hello in one sentence.")
    print("Chat response:", response)

def test_embeddings():
    embeddings = get_embedding()
    vector = embeddings.embed_query("SQL injection prevention")
    print("Embedding dimension:", len(vector))
    # print("Embedding vector:", vector)

if __name__ == "__main__":
    print("--- Testing Chat ---")
    test_chat()
    print("--- Testing Embeddings ---")
    test_embeddings()

