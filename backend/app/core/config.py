from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "GlobalPay FinTech Solutions"
    environment: str = "development"
    debug: bool = True
    api_v1_prefix: str = "/api/v1"

    database_url: str = "postgresql+psycopg://globalpay:globalpay@postgres:5432/globalpay"
    redis_url: str = "redis://redis:6379/0"

    jwt_secret: str = Field(min_length=16, default="replace-this-development-secret")
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 120
    pii_encryption_key: str = "AAECAwQFBgcICQoLDA0ODxAREhMUFRYXGBkaGxwdHh8="

    cors_origins: str = "http://localhost:3000,http://localhost:5173"
    fraud_model_path: str = "/app/model_data/fraud_model.joblib"
    fraud_dataset_path: str = "/app/datasets/transactions.csv"

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]

    @property
    def model_path(self) -> Path:
        return Path(self.fraud_model_path)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
