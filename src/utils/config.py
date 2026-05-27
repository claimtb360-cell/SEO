"""Application configuration using pydantic-settings."""

from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Global application settings loaded from .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # App
    app_name: str = "SEO Tool"
    app_env: str = "development"
    app_debug: bool = True
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    # Database
    database_url: str = "sqlite+aiosqlite:///./data/seo_tool.db"

    # Google APIs
    google_api_key: Optional[str] = None
    google_cse_id: Optional[str] = None
    pagespeed_api_key: Optional[str] = None

    # Moz API
    moz_access_id: Optional[str] = None
    moz_secret_key: Optional[str] = None

    # Ahrefs API
    ahrefs_api_key: Optional[str] = None

    # AI Provider API Keys
    openai_api_key: Optional[str] = None
    openai_base_url: Optional[str] = None  # Custom endpoint (e.g., Azure OpenAI)
    anthropic_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None
    groq_api_key: Optional[str] = None
    mistral_api_key: Optional[str] = None
    cohere_api_key: Optional[str] = None

    # AI defaults
    ai_default_provider: str = "openai"
    ai_default_model: str = "gpt-4o-mini"
    ai_max_tokens: int = 4096
    ai_temperature: float = 0.7

    # Crawling
    max_concurrent_requests: int = 10
    request_timeout: int = 30
    user_agent: str = "SEOTool/1.0 (+https://github.com/claimtb360-cell/SEO)"
    crawl_delay: float = 1.0

    # Rate Limiting
    rate_limit_requests: int = 100
    rate_limit_period: int = 60

    # Reports
    report_output_dir: str = "./reports"
    report_format: str = "html"

    # Scheduling
    rank_check_schedule: str = "0 6 * * *"

    @property
    def base_dir(self) -> Path:
        """Project base directory."""
        return Path(__file__).resolve().parent.parent.parent

    @property
    def data_dir(self) -> Path:
        """Data directory for database and exports."""
        path = self.base_dir / "data"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def reports_dir(self) -> Path:
        """Reports output directory."""
        path = Path(self.report_output_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path


settings = Settings()
