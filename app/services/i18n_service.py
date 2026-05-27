"""
Internationalization (i18n) service.

Loads JSON translation files from app/i18n/.
Supported: tr (Turkish), en (English), de (German), fr (French).
Falls back to English if a key is missing in the requested language.
"""

import json
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

I18N_DIR = Path(__file__).parent.parent / "i18n"
SUPPORTED_LANGUAGES = ["tr", "en", "de", "fr"]
DEFAULT_LANGUAGE = "tr"


class I18nService:
    def __init__(self):
        self._translations: dict[str, dict] = {}
        self._load_all()

    def _load_all(self) -> None:
        for lang in SUPPORTED_LANGUAGES:
            path = I18N_DIR / f"{lang}.json"
            if path.exists():
                try:
                    self._translations[lang] = json.loads(path.read_text(encoding="utf-8"))
                    logger.debug(f"Loaded i18n: {lang}")
                except Exception as exc:
                    logger.warning(f"Failed to load {lang}.json: {exc}")
                    self._translations[lang] = {}
            else:
                self._translations[lang] = {}

    def t(self, key: str, lang: Optional[str] = None, **kwargs) -> str:
        """
        Translate a dot-separated key.
        Example: t("error.paper_out", lang="tr")
        Falls back: requested lang → English → key itself
        """
        lang = lang or DEFAULT_LANGUAGE
        value = self._resolve(key, lang) or self._resolve(key, DEFAULT_LANGUAGE) or key
        if kwargs:
            try:
                value = value.format(**kwargs)
            except (KeyError, IndexError):
                pass
        return value

    def _resolve(self, key: str, lang: str) -> Optional[str]:
        d = self._translations.get(lang, {})
        parts = key.split(".")
        for part in parts:
            if isinstance(d, dict):
                d = d.get(part)
            else:
                return None
        return d if isinstance(d, str) else None

    def get_supported(self) -> list[str]:
        return SUPPORTED_LANGUAGES


# Module-level singleton
_i18n_service: Optional[I18nService] = None


def get_i18n_service() -> I18nService:
    global _i18n_service
    if _i18n_service is None:
        _i18n_service = I18nService()
    return _i18n_service
