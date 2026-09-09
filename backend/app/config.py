"""Application settings loaded from environment / .env file."""
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# SEC-001: the app must not run with a known or weak JWT secret. The field
# default is deliberately empty; the validator below fails fast unless a strong
# secret is provided via environment or .env.
_KNOWN_WEAK_JWT_SECRETS = {
    "dev-secret-change-me",
    "change-me-in-production",
    "changeme",
    "change-me",
    "secret",
    "test-secret-key",
    "your-secret-key",
    "supersecret",
    "jwtsecret",
    "jwt-secret",
}
_MIN_JWT_SECRET_LENGTH = 32


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    project_name: str = "MAE-4 Gemelo Digital Hidrogeomorfológico"
    api_prefix: str = "/api"

    # Database
    database_url: str = "postgresql://postgres:postgres@db:5432/mae4"

    # Security
    jwt_secret: str = ""
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24

    # Seed
    seed_on_startup: bool = True

    # Rate limiting (SEC-004): per-IP budgets for authentication endpoints.
    # In-memory and per-process; adjust when scaling beyond one worker.
    login_rate_limit: int = 60
    login_rate_window_minutes: int = 15
    register_rate_limit: int = 20
    register_rate_window_minutes: int = 15
    # RATE-001: when the backend is reachable ONLY through a trusted reverse
    # proxy, enable this to key the limit by the client IP taken from
    # X-Forwarded-For. Keep False for direct connections: honoring the header
    # without a trusted proxy lets a client spoof it and bypass the per-IP
    # budget (the default is fail-safe).
    rate_limit_trust_proxy: bool = False

    # CORS (comma separated list of allowed origins)
    cors_origins: str = "http://localhost:3000,http://frontend:3000"

    @model_validator(mode="after")
    def _validate_jwt_secret(self) -> "Settings":
        secret = (self.jwt_secret or "").strip()
        lowered = secret.lower()
        is_known_default = lowered in _KNOWN_WEAK_JWT_SECRETS or (
            "dev-secret-change-me" in lowered or "change-me-in-production" in lowered
        )
        if is_known_default or len(secret) < _MIN_JWT_SECRET_LENGTH:
            raise ValueError(
                "JWT_SECRET debe ser un secreto aleatorio de al menos 32 caracteres "
                "y no puede conservar valores conocidos de desarrollo (SEC-001). "
                "Genera uno con: openssl rand -hex 32"
            )
        return self


settings = Settings()
