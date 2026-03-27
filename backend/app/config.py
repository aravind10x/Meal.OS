from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    APP_NAME: str = "Meal.OS"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "sqlite:///./meal_os.db"

    # CORS — allow frontend dev server
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ]

    # Azure OpenAI (Phase 1+)
    AZURE_OPENAI_ENDPOINT: str = ""
    AZURE_OPENAI_API_KEY: str = ""
    AZURE_OPENAI_DEPLOYMENT_NAME: str = ""
    AZURE_OPENAI_API_VERSION: str = "2024-12-01-preview"

    # Azure TTS (Phase 2+)
    AZURE_SPEECH_KEY: str = ""
    AZURE_SPEECH_REGION: str = ""

    # Startup behavior
    AUTO_SEED: bool = False  # Set to True to seed demo data on startup

    # Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    SEED_DIR: Path = Path(__file__).resolve().parent / "seed"
    AUDIO_DIR: Path = Path(__file__).resolve().parent.parent / "audio_files"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
