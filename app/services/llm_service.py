"""
Optional LLM service via OpenRouter.

IMPORTANT NOTE (per task requirement):
  This is an OPTIONAL bonus feature. It requires an external API key (OpenRouter).
  The task specifies: "Dış servis/anahtar gerektiren ücretli SDK kullanmayınız
  (gerekirse açıkça not ediniz)."

  LLM is disabled by default (LLM_ENABLED=false in .env).
  When disabled, the service works 100% without any external dependency.
  When enabled, the user must supply their own OPENROUTER_API_KEY.
  The free model (mistralai/mistral-7b-instruct:free) is used by default.

Uses: httpx (async HTTP, already in requirements.txt)
"""

import json
import logging
from typing import Any, Optional

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class LlmService:
    """
    Async OpenRouter LLM client.
    Disabled when settings.llm_enabled is False.
    """

    def __init__(self):
        settings = get_settings()
        self._enabled = settings.llm_enabled
        self._api_key = settings.openrouter_api_key
        self._model = settings.openrouter_model
        self._base_url = settings.openrouter_base_url

    @property
    def enabled(self) -> bool:
        return self._enabled and bool(self._api_key)

    async def generate_receipt_lines(
        self,
        data: dict[str, Any],
        language: str = "en",
        template_hint: Optional[str] = None,
    ) -> list[dict]:
        """
        Ask LLM to convert structured data into receipt line dicts.
        Returns list of {text, bold, align, font_size} dicts.
        Falls back to simple key-value formatting if LLM unavailable.
        """
        if not self.enabled:
            return self._fallback_format(data)

        prompt = self._build_receipt_prompt(data, language, template_hint)
        try:
            response_text = await self._chat(prompt)
            lines = self._parse_llm_receipt(response_text)
            return lines if lines else self._fallback_format(data)
        except Exception as exc:
            logger.warning(f"LLM receipt generation failed: {exc}. Using fallback.")
            return self._fallback_format(data)

    async def translate_error(self, error_key: str, language: str = "en") -> Optional[str]:
        """
        Use LLM to generate a friendly error message if i18n key missing.
        Not recommended for production — i18n JSON files cover all cases.
        """
        if not self.enabled:
            return None
        prompt = (
            f"Write a short, friendly printer error message for '{error_key}' in {language}. "
            "Max 1 sentence. No extra commentary."
        )
        try:
            return await self._chat(prompt)
        except Exception:
            return None

    async def _chat(self, prompt: str, max_tokens: int = 512) -> str:
        """Send a single chat message to OpenRouter and return the response text."""
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:8000",
            "X-Title": "Thermal Printer Service",
        }
        payload = {
            "model": self._model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                f"{self._base_url}/chat/completions",
                headers=headers,
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"].strip()

    def _build_receipt_prompt(
        self,
        data: dict,
        language: str,
        hint: Optional[str],
    ) -> str:
        hint_str = f" The receipt type is: {hint}." if hint else ""
        lang_map = {"tr": "Turkish", "en": "English", "de": "German", "fr": "French"}
        lang_name = lang_map.get(language, "English")
        return (
            f"Convert the following data into a thermal printer receipt in {lang_name}.{hint_str}\n"
            f"Data: {json.dumps(data, ensure_ascii=False)}\n\n"
            "Return a JSON array of line objects. Each object has:\n"
            '  "text": string\n'
            '  "bold": boolean\n'
            '  "align": "left"|"center"|"right"\n'
            '  "font_size": "normal"|"double_height"|"double_width"|"double"\n\n'
            "Include a header, content rows, and a footer. Return ONLY the JSON array."
        )

    def _parse_llm_receipt(self, text: str) -> list[dict]:
        """Extract JSON array from LLM response."""
        # Try to find JSON array in response
        start = text.find("[")
        end = text.rfind("]") + 1
        if start == -1 or end == 0:
            return []
        try:
            lines = json.loads(text[start:end])
            return [
                {
                    "text": str(l.get("text", "")),
                    "bold": bool(l.get("bold", False)),
                    "align": l.get("align", "left"),
                    "font_size": l.get("font_size", "normal"),
                }
                for l in lines
                if isinstance(l, dict)
            ]
        except (json.JSONDecodeError, KeyError):
            return []

    def _fallback_format(self, data: dict) -> list[dict]:
        """Simple key-value formatter when LLM is unavailable."""
        lines = [{"text": "=== RECEIPT ===", "bold": True, "align": "center", "font_size": "normal"}]
        for k, v in data.items():
            lines.append({"text": f"{k}: {v}", "bold": False, "align": "left", "font_size": "normal"})
        lines.append({"text": "===============", "bold": False, "align": "center", "font_size": "normal"})
        return lines


# Module-level singleton
_llm_service: Optional[LlmService] = None


def get_llm_service() -> LlmService:
    global _llm_service
    if _llm_service is None:
        _llm_service = LlmService()
    return _llm_service
