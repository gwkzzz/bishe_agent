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

    server_host: str = Field(default="0.0.0.0", alias="SERVER_HOST")
    server_port: int = Field(default=8000, alias="SERVER_PORT")
    server_secret_key: str = Field(default="change-me", alias="SERVER_SECRET_KEY")
    access_token_expire_minutes: int = Field(default=60 * 24, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    server_cors_origins: str = Field(
        default="http://localhost:5173,http://127.0.0.1:5173",
        alias="SERVER_CORS_ORIGINS",
    )

    algorithm_base_url: str = Field(default="http://localhost:8001", alias="ALGORITHM_BASE_URL")
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

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.server_cors_origins.split(",") if origin.strip()]

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
