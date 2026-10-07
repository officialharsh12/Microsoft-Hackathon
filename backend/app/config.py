import os
from pathlib import Path
from pydantic import BaseModel
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


class Settings(BaseModel):
    # App
    PROJECT_NAME: str = "FeedbackPulse"
    VERSION: str = "2.0.0"
    API_V1_PREFIX: str = "/api"
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    CORS_ORIGINS: list = [
        origin.strip()
        for origin in os.getenv(
            "CORS_ORIGINS",
            "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173"
        ).split(",")
        if origin.strip()
    ]

    # ── Database (PostgreSQL) ─────────────────────────────────────────────────
    # Required: set DATABASE_URL in backend/.env
    # Example: postgresql://postgres:password@localhost:5432/reviews_db
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/reviews_db")

    # DATA_DIR: for uploaded CSV storage on disk
    DATA_DIR: Path = BASE_DIR / "data"

    @property
    def PG_DSN(self) -> str:
        """Returns a clean psycopg2-compatible DSN."""
        url = self.DATABASE_URL
        # Strip SQLAlchemy dialect prefix if present
        url = url.replace("postgresql+psycopg2://", "postgresql://")
        return url

    @property
    def DB_TYPE(self) -> str:
        """Always returns 'postgresql' — SQLite is not supported."""
        return "postgresql"

    # ── AI Models ─────────────────────────────────────────────────────────────
    SENTIMENT_MODEL_NAME: str = os.getenv(
        "SENTIMENT_MODEL_NAME",
        "distilbert-base-uncased-finetuned-sst-2-english"
    )
    EMOTION_MODEL_NAME: str = os.getenv(
        "EMOTION_MODEL_NAME",
        "SamLowe/roberta-base-go_emotions"
    )
    EMBEDDING_MODEL_NAME: str = os.getenv(
        "EMBEDDING_MODEL_NAME",
        "sentence-transformers/all-MiniLM-L6-v2"
    )

    # ── LLM (Azure OpenAI) ────────────────────────────────────────────────────
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "azure-openai")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4o-mini")
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
    AZURE_OPENAI_ENDPOINT: str = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    AZURE_OPENAI_DEPLOYMENT: str = os.getenv("AZURE_OPENAI_DEPLOYMENT", "")

    # ── Auth ─────────────────────────────────────────────────────────────────
    AUTH_SECRET: str = os.getenv("AUTH_SECRET", "feedbackpulse-secret-change-in-production-32ch")

    # ── Inference ─────────────────────────────────────────────────────────────
    # Increase BATCH_SIZE for GPU; decrease for CPU-only machines
    BATCH_SIZE: int = int(os.getenv("BATCH_SIZE", "32"))
    # MAX_REVIEWS: 0 = no limit (process all rows). Set >0 to cap (not recommended)
    MAX_REVIEWS: int = int(os.getenv("MAX_REVIEWS", "0"))
    DEVICE: str = os.getenv("DEVICE", "auto")

    def get_torch_device(self) -> str:
        if self.DEVICE != "auto":
            return self.DEVICE
        try:
            import torch
            if torch.cuda.is_available():
                return "cuda"
            if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                return "mps"
        except ImportError:
            pass
        return "cpu"


settings = Settings()
settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
