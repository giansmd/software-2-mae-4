"""Application settings loaded from environment / .env file."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    project_name: str = "MAE-4 Gemelo Digital Hidrogeomorfológico"
    api_prefix: str = "/api"

    # Database
    database_url: str = "postgresql://postgres:postgres@db:5432/mae4"

    # Security
    jwt_secret: str = "dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24

    # Seed
    seed_on_startup: bool = True

    # CORS (comma separated list of allowed origins)
    cors_origins: str = "http://localhost:3000,http://frontend:3000"


settings = Settings()
