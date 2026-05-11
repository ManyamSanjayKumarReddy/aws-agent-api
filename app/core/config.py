from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # OpenAI
    openai_api_key: str

    # PostgreSQL
    postgres_user: str = "awsagent"
    postgres_password: str = "awsagent_pass"
    postgres_db: str = "awsagent_db"
    postgres_host: str = "postgres"
    postgres_port: int = 5432

    # AWS
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_default_region: str = "us-east-1"

    # App
    app_env: str = "development"
    log_level: str = "INFO"

    @property
    def database_url(self) -> str:
        return (
            f"postgres://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()