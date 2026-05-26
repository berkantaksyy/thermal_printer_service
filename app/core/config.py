"""
Central application configuration via pydantic-settings.
All values are read from environment variables / .env file.
"""

from functools import lru_cache
from typing import Literal
from pydantic import field_validator
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

    # USB  (env vars may be decimal OR hex-string like "0x0456")
    usb_vendor_id: int = 0x0456
    usb_product_id: int = 0x0808

    @field_validator("usb_vendor_id", "usb_product_id", mode="before")
    @classmethod
    def parse_hex_int(cls, v: object) -> object:
        """Accept decimal strings ('1110') and hex strings ('0x0456') from .env."""
        if isinstance(v, str):
            return int(v, 0)   # int('0x0456', 0) → 1110; int('1110', 0) → 1110
        return v

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

    # ── LLM — Groq (optional) ────────────────────────────────────────────────
    # Set LLM_ENABLED=true and provide GROQ_API_KEY to activate.
    # Free models: llama3-8b-8192, llama3-70b-8192, mixtral-8x7b-32768
    # Get your free key at: https://console.groq.com
    llm_enabled: bool = False
    groq_api_key: str = ""
    groq_model: str = "llama3-8b-8192"
    groq_base_url: str = "https://api.groq.com/openai/v1"


@lru_cache
def get_settings() -> Settings:
    """Return cached Settings singleton."""
    return Settings()
