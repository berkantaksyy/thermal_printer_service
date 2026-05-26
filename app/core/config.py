"""
Central application configuration via pydantic-settings.
All values are read from environment variables / .env file.
"""

from functools import lru_cache
from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ──────────────────────────────────────────────────────────
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_debug: bool = False
    app_title: str = "Thermal Printer Service"
    app_version: str = "1.0.0"

    # ── Security ─────────────────────────────────────────────────────────────
    api_bearer_token: str = "change-me-secret-token"

    # ── Printer connection ────────────────────────────────────────────────────
    default_connection_type: Literal["usb", "lan"] = "usb"

    # USB
    usb_vendor_id: int = 0x0456
    usb_product_id: int = 0x0808

    # LAN
    lan_host: str = "192.168.1.100"
    lan_port: int = 9100
    lan_timeout: float = 5.0

    # Reconnect / backoff
    reconnect_max_retries: int = 5
    reconnect_backoff_base: float = 2.0
    reconnect_backoff_max: float = 60.0

    # ── Logging ───────────────────────────────────────────────────────────────
    log_dir: str = "./logs"
    log_max_size_mb: int = 10
    log_keep_days: int = 30

    # ── i18n ─────────────────────────────────────────────────────────────────
    default_language: str = "en"

    # ── LLM (optional) ───────────────────────────────────────────────────────
    llm_enabled: bool = False
    openrouter_api_key: str = ""
    openrouter_model: str = "mistralai/mistral-7b-instruct:free"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"


@lru_cache
def get_settings() -> Settings:
    """Return cached Settings singleton."""
    return Settings()
