"""
Optional LLM service via Groq (OpenAI-compatible API).

IMPORTANT NOTE (per task requirement):
  This is an OPTIONAL bonus feature. It requires an external API key (Groq).
  The task specifies: "Dış servis/anahtar gerektiren ücretli SDK kullanmayınız
  (gerekirse açıkça not ediniz)."

  LLM is disabled by default (LLM_ENABLED=false in .env).
  When disabled, the service works 100% without any external dependency.
  When enabled, the user must supply their own GROQ_API_KEY.

  Groq offers free-tier access with models like llama3-8b-8192.
  Uses the OpenAI-compatible endpoint: https://api.groq.com/openai/v1
"""

import json
import logging
from typing import Any, Optional

from openai import OpenAI

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class LlmService:
    """
    Groq LLM client (OpenAI-compatible).
    Disabled when settings.llm_enabled is False or GROQ_API_KEY is empty.
    """

    def __init__(self):
        settings = get_settings()
        self._enabled = settings.llm_enabled
        self._api_key = settings.groq_api_key
        self._model = settings.groq_model
        self._base_url = settings.groq_base_url
        self._client: Optional[OpenAI] = None

    def _get_client(self) -> OpenAI:
        if self._client is None:
            self._client = OpenAI(
                base_url=self._base_url,
                api_key=self._api_key,
            )
        return self._client

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
            response_text = self._chat(prompt)
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
            return self._chat(prompt)
        except Exception:
            return None

    def _chat(self, prompt: str, max_tokens: int = 512) -> str:
        """Send a single chat message to Groq and return the response text."""
        client = self._get_client()
        response = client.chat.completions.create(
            model=self._model,
            messages=[
                {
                    "role": "system",
                    "content": "Sen kısa ve öz cevaplar veren bir asistansın.",
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content.strip()

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
