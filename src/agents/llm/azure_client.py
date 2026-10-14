import truststore
truststore.inject_into_ssl()

from langchain_openai import AzureChatOpenAI
from langchain_huggingface import HuggingFaceEmbeddings
from src.config import settings

def get_llm() -> AzureChatOpenAI:
    return AzureChatOpenAI(
        api_key=settings.AZURE_OPENAI_API_KEY.get_secret_value(),
        azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
        api_version=settings.AZURE_OPENAI_API_VERSION,
        azure_deployment=settings.AZURE_OPENAI_DEPLOYMENT_NAME,
    )

def get_embedding() -> HuggingFaceEmbeddings:
    return HuggingFaceEmbeddings(
        model_name=settings.EMBEDDING_MODEL_NAME,
    )
