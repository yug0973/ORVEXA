import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Application Settings loader using Pydantic Settings v2.
    Loads configurations from environment variables or a local .env file.
    """
    DATABASE_URL: str = "sqlite+aiosqlite:///ORVEXA.db"
    
    # Allow extra configuration variables to be ignored
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )

settings = Settings()
