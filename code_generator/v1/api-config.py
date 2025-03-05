import os
from pydantic_settings import BaseSettings
from typing import List
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    # Application settings
    APP_NAME: str = "Multi-Agent Orchestration Platform"
    APP_ENV: str = os.getenv("APP_ENV", "development")
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"

    # API settings
    API_PREFIX: str = "/api"
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",  # React app default
        "http://localhost:8000",
        "http://localhost:8080",
    ]

    # LangGraph settings
    GENERATED_CODE_PATH: str = os.getenv(
        "GENERATED_CODE_PATH",
        os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "generated"
        ),
    )

    # Workflow execution settings
    MAX_CONCURRENT_WORKFLOWS: int = int(os.getenv("MAX_CONCURRENT_WORKFLOWS", "10"))
    WORKFLOW_TIMEOUT_SECONDS: int = int(os.getenv("WORKFLOW_TIMEOUT_SECONDS", "300"))

    # Logging settings
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE: str = os.getenv("LOG_FILE", "app.log")

    # Key vault integration
    USE_KEY_VAULT: bool = os.getenv("USE_KEY_VAULT", "False").lower() == "true"
    KEY_VAULT_URL: str = os.getenv("KEY_VAULT_URL", "")

    class Config:
        env_file = ".env"


settings = Settings()
