from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    environment: str = "development"
    database_url: str = "postgresql://postgres:fin123@localhost:5432/fin"
    secret_key: str = "change-me-to-a-random-secret-at-least-32-chars"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    allowed_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    allowed_hosts: str = "localhost,127.0.0.1,testserver"
    database_pool_size: int = 5
    database_max_overflow: int = 10
    database_pool_timeout: int = 30
    database_pool_recycle: int = 1800
    fin_ai_provider: str = "rules"
    fin_ai_model: str = "openai/gpt-oss-20b"
    fin_ai_timeout_seconds: float = 12.0
    fin_ai_max_tool_rounds: int = 3
    fin_ai_messages_per_minute: int = 12
    fin_ai_messages_per_day: int = 200
    groq_api_key: str | None = None
    groq_base_url: str = "https://api.groq.com/openai/v1"
    redis_url: str | None = None
    trusted_proxy_ips: str = ""

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]

    @property
    def proxy_ips(self) -> set[str]:
        return {value.strip() for value in self.trusted_proxy_ips.split(",") if value.strip()}

    @property
    def host_allowlist(self) -> list[str]:
        return [value.strip() for value in self.allowed_hosts.split(",") if value.strip()]

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
        if not self.redis_url:
            raise RuntimeError("REDIS_URL is required for distributed rate limiting in production")
        if not self.host_allowlist or "*" in self.host_allowlist:
            raise RuntimeError("ALLOWED_HOSTS must contain only explicit hostnames in production")
        if self.fin_ai_provider == "groq" and not self.groq_api_key:
            raise RuntimeError("GROQ_API_KEY is required when FIN_AI_PROVIDER=groq")
        if self.fin_ai_provider not in {"rules", "groq"}:
            raise RuntimeError("FIN_AI_PROVIDER must be rules or groq")


settings = Settings()
