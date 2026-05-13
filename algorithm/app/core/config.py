from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


REPO_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(REPO_ROOT / ".env", ".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = Field(default="local", alias="APP_ENV")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    trace_header_name: str = Field(default="X-Trace-Id", alias="TRACE_HEADER_NAME")

    algorithm_host: str = Field(default="0.0.0.0", alias="ALGORITHM_HOST")
    algorithm_port: int = Field(default=8001, alias="ALGORITHM_PORT")
    algorithm_internal_token: str = Field(
        default="change-me-internal-token",
        alias="ALGORITHM_INTERNAL_TOKEN",
    )

    mysql_host: str = Field(default="localhost", alias="MYSQL_HOST")
    mysql_port: int = Field(default=3306, alias="MYSQL_PORT")
    mysql_database: str = Field(default="legal_assistant", alias="MYSQL_DATABASE")
    mysql_user: str = Field(default="legal_app", alias="MYSQL_USER")
    mysql_password: str = Field(default="legal_password", alias="MYSQL_PASSWORD")

    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    rabbitmq_url: str = Field(
        default="amqp://legal_app:legal_password@localhost:5672/",
        alias="RABBITMQ_URL",
    )

    minio_host: str = Field(default="localhost", alias="MINIO_HOST")
    minio_api_port: int = Field(default=9000, alias="MINIO_API_PORT")
    minio_root_user: str = Field(default="minioadmin", alias="MINIO_ROOT_USER")
    minio_root_password: str = Field(default="minioadmin", alias="MINIO_ROOT_PASSWORD")
    minio_bucket: str = Field(default="evidence", alias="MINIO_BUCKET")

    milvus_host: str = Field(default="localhost", alias="MILVUS_HOST")
    milvus_port: int = Field(default=19530, alias="MILVUS_PORT")
    rag_use_database: bool = Field(default=False, alias="RAG_USE_DATABASE")
    rag_vector_enabled: bool = Field(default=False, alias="RAG_VECTOR_ENABLED")
    rag_vector_dimension: int = Field(default=64, alias="RAG_VECTOR_DIMENSION")
    rag_min_relevance_score: float = Field(default=0.02, alias="RAG_MIN_RELEVANCE_SCORE")

    model_base_url: str = Field(default="http://localhost:11434/v1", alias="MODEL_BASE_URL")
    model_api_key: str = Field(default="change-me", alias="MODEL_API_KEY")
    chat_model: str = Field(default="placeholder-chat-model", alias="CHAT_MODEL")
    embedding_model: str = Field(
        default="placeholder-embedding-model",
        alias="EMBEDDING_MODEL",
    )
    rerank_model: str = Field(default="placeholder-rerank-model", alias="RERANK_MODEL")

    @property
    def mysql_url(self) -> str:
        return (
            f"mysql+pymysql://{self.mysql_user}:{self.mysql_password}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}?charset=utf8mb4"
        )

    @property
    def minio_endpoint(self) -> str:
        return f"{self.minio_host}:{self.minio_api_port}"


@lru_cache
def get_settings() -> Settings:
    return Settings()
