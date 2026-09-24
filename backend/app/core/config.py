from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# Anchor the .env path to this file's location, so it's found correctly
# regardless of what directory the app/script is run from.
ENV_FILE_PATH = Path(__file__).resolve().parents[2] / ".env"

class Settings(BaseSettings):
    """
    Centralized application settings.
    Values are loaded from environment variables (or a .env file in development).
    Every other part of the app should import `settings` from here instead of
    calling os.getenv() directly, so all configuration lives in one place.
    """

    app_env: str = "development"
    debug: bool = True

    # Database (used starting Phase 4 — placeholder default for now)
    database_url: str = "postgresql://user:password@localhost:5432/pulseiq"

    # Security (used starting Phase 14 — placeholder defaults for now)
    jwt_secret_key: str = "changeme"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    model_config = SettingsConfigDict(
        env_file=ENV_FILE_PATH,
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


# A single shared instance, imported everywhere else in the app.
settings = Settings()