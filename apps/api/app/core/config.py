from urllib.parse import urlparse

from cryptography.fernet import Fernet
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
    mail_provider: str = "console"
    resend_api_key: str | None = None
    email_from: str = "Nexo <no-reply@example.com>"
    public_web_url: str = "http://localhost:3000"
    email_verification_ttl_minutes: int = 30
    password_reset_ttl_minutes: int = 20
    mfa_challenge_ttl_minutes: int = 5
    mfa_encryption_keys: str = ""
    mfa_active_key_version: str = "v1"

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

    @property
    def mfa_keyring(self) -> dict[str, str]:
        return dict(item.split(":", 1) for item in self.mfa_encryption_keys.split(",") if ":" in item)

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
        if self.mail_provider != "resend":
            raise RuntimeError("MAIL_PROVIDER must be resend in production")
        if not self.resend_api_key:
            raise RuntimeError("RESEND_API_KEY is required when MAIL_PROVIDER=resend")
        public_web_url = urlparse(self.public_web_url)
        if public_web_url.scheme != "https" or not public_web_url.hostname:
            raise RuntimeError("PUBLIC_WEB_URL must use HTTPS in production")
        if not self.email_from or self.email_from == "Nexo <no-reply@example.com>":
            raise RuntimeError("EMAIL_FROM must be explicitly configured in production")
        if self.mfa_active_key_version not in self.mfa_keyring:
            raise RuntimeError("MFA_ACTIVE_KEY_VERSION must be present in MFA_ENCRYPTION_KEYS")
        try:
            for key in self.mfa_keyring.values():
                Fernet(key)
        except (TypeError, ValueError):
            raise RuntimeError("MFA_ENCRYPTION_KEYS must contain valid Fernet keys") from None


settings = Settings()
