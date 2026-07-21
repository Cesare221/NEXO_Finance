from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    environment: str = "development"
    database_url: str = "postgresql://postgres:fin123@localhost:5432/fin"
    secret_key: str = "change-me-to-a-random-secret-at-least-32-chars"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    allowed_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    database_pool_size: int = 5
    database_max_overflow: int = 10
    database_pool_timeout: int = 30
    database_pool_recycle: int = 1800

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]

    def validate_runtime(self) -> None:
        if self.environment.lower() != "production":
            return
        if self.secret_key.startswith("change-me-") or len(self.secret_key) < 64:
            raise RuntimeError("SECRET_KEY must be a random value with at least 64 characters")
        if "localhost" in self.database_url or "127.0.0.1" in self.database_url:
            raise RuntimeError("DATABASE_URL must not use development credentials in production")
        if not self.cors_origins or any(
            origin == "*" or not origin.startswith("https://")
            for origin in self.cors_origins
        ):
            raise RuntimeError("ALLOWED_ORIGINS must contain only explicit HTTPS origins in production")


settings = Settings()
