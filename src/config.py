from pydantic_settings import BaseSettings
from pydantic import SecretStr

class Settings(BaseSettings):
    """Application settings."""

    app_name: str = "AI Code Reviewer"
    debug: bool = False
    
    AZURE_OPENAI_API_KEY: SecretStr
    AZURE_OPENAI_ENDPOINT: str
    AZURE_OPENAI_API_VERSION: str = "2024-10-21"
    AZURE_OPENAI_DEPLOYMENT_NAME: str

    EMBEDDING_MODEL_NAME: str = "./media/models/bge-small-en-v1.5"


    DATABASE_URL: str | None = None
    GITHUB_TOKEN: str | None = None
    MEDIA_DIR: str = "./media"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()