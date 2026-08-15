from functools import lru_cache

from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    COGNODB_URI: str
    COGNODB_USER: str
    COGNODB_PASSWORD: str
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_TTL_MINUTES: int = 60

    # Deployment
    # ENVIRONMENT controls CORS origin and cookie security.
    # Set to "production" on the hosting platform; leave as "development" locally.
    ENVIRONMENT: str = "development"
    # Comma-separated list of allowed CORS origins.
    # In production set this to your actual frontend URL, e.g.:
    #   FRONTEND_URL=https://pernet.vercel.app
    FRONTEND_URL: str = "http://localhost:3000"

    @property
    def cors_origins(self) -> list[str]:
        """Return allowed CORS origins as a list (supports comma-separated values)."""
        return [o.strip() for o in self.FRONTEND_URL.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance. Use this everywhere instead of Settings()."""
    return Settings()
