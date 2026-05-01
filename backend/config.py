"""
config.py — Central settings loader using Pydantic BaseSettings.
All configuration comes from environment variables / .env file.
"""
from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    # ── OpenAI / NVIDIA (OpenAI-compatible) ────────────────
    openai_api_key: str
    openai_base_url: str = "https://api.openai.com/v1"
    model_name: str = "gpt-4o-mini"
    embedding_model: str = "nvidia/nv-embedqa-e5-v5"

    # ── Memory ──────────────────────────────────────────────
    max_short_term_messages: int = 10

    # ── Database / OneDrive ─────────────────────────────────
    # The SQLite file lives inside OneDrive → auto-syncs to cloud for free
    onedrive_path: str = str(Path.home() / "OneDrive" / "PersonalAI")

    @property
    def database_url(self) -> str:
        db_dir = Path(self.onedrive_path)
        db_dir.mkdir(parents=True, exist_ok=True)
        db_path = db_dir / "personal_ai.db"
        return f"sqlite+aiosqlite:///{db_path}"

    # ── ngrok (phone access) ─────────────────────────────────
    enable_ngrok: bool = False
    ngrok_auth_token: str = ""

    # ── Server ───────────────────────────────────────────────
    host: str = "0.0.0.0"
    port: int = 8000

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
