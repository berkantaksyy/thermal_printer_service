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
import re
from typing import Optional

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
        self._model = settings.groq_model  # openai/gpt-oss-120b
        self._base_url = settings.groq_base_url
        self._client: Optional[OpenAI] = None
        
        if self._enabled and self._api_key:
            logger.info(f"✅ LLM enabled with model: {self._model}")
        else:
            logger.info("ℹ️ LLM disabled (using fallback formatting)")

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
        prompt: str,
        language: str = "en",
    ) -> list[dict]:
        """
        Ask LLM to convert a free-text description into receipt line dicts.
        Returns list of {text, bold, align, font_size} dicts.
        Falls back to simple text formatting if LLM unavailable.
        """
        if not self.enabled:
            return self._fallback_format(prompt, language)

        receipt_prompt = self._build_receipt_prompt(prompt, language)
        try:
            response_text = self._chat(receipt_prompt)
            lines = self._parse_llm_receipt(response_text)
            return lines if lines else self._fallback_format(prompt, language)
        except Exception as exc:
            logger.warning(f"LLM receipt generation failed: {exc}. Using fallback.")
            return self._fallback_format(prompt, language)

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

    def _chat(self, prompt: str, max_tokens: int = 8192) -> str:
        """Send a chat message to the LLM with streaming and return the response text."""
        client = self._get_client()

        completion = client.chat.completions.create(
            model=self._model,
            messages=[
                {
                    "role": "system",
                    "content": self._system_prompt(),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=0.2,
            max_completion_tokens=max_tokens,
            top_p=1,
            stream=True,
            stop=None,
        )

        full_response = ""
        for chunk in completion:
            if chunk.choices[0].delta.content:
                full_response += chunk.choices[0].delta.content

        return full_response.strip()

    def _system_prompt(self) -> str:
        return (
            "You are a professional thermal receipt printer formatter.\n"
            "Your ONLY job: convert any free-text description into a beautifully formatted thermal receipt.\n\n"
            "Output ONLY a raw JSON array — no markdown fences (```), no explanation, no extra text.\n"
            "Each element must have exactly these fields:\n"
            '  "text"      : string — the line content\n'
            '  "bold"      : boolean\n'
            '  "align"     : "left" | "center" | "right"\n'
            '  "font_size" : "normal" | "double"\n\n'
            "Receipt design rules (follow strictly):\n"
            "  1. First line: bold centered title, font_size 'double'\n"
            "  2. Second line: separator — a row of '═' chars (32 wide), align center\n"
            "  3. Content rows: left-aligned, normal size. Use 'KEY          VALUE' padding style.\n"
            "  4. Important amounts/totals: bold, centered\n"
            "  5. Before footer: separator row of '─' chars (32 wide)\n"
            "  6. Last 1-2 lines: short centered thank-you or footer, normal size\n"
            "  7. ALL text must be in the language specified by the user\n"
            "  8. Return ONLY the JSON array, starting with '[' and ending with ']'"
        )

    def _build_receipt_prompt(self, user_prompt: str, language: str) -> str:
        lang_map = {"tr": "Turkish", "en": "English", "de": "German", "fr": "French"}
        lang_name = lang_map.get(language, "English")
        return (
            f"Language: {lang_name} ({language}). Write ALL text in {lang_name} ONLY.\n\n"
            f"Create a thermal printer receipt for the following:\n\n"
            f"{user_prompt}"
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

    def _fallback_format(self, prompt: str, language: str = "en") -> list[dict]:
        """
        Simple fallback formatter when LLM is unavailable.
        Turns the free-text prompt into a readable receipt layout.
        """
        _titles = {"tr": "FİŞ", "en": "RECEIPT", "de": "BELEG", "fr": "REÇU"}
        _footers = {
            "tr": "Teşekkür ederiz!",
            "en": "Thank you!",
            "de": "Vielen Dank!",
            "fr": "Merci!",
        }
        title = _titles.get(language, "RECEIPT")
        footer = _footers.get(language, "Thank you!")
        sep = "═" * 32
        sep2 = "─" * 32

        lines = [
            {"text": title, "bold": True, "align": "center", "font_size": "double"},
            {"text": sep, "bold": False, "align": "center", "font_size": "normal"},
        ]

        # Split prompt into sentences / clauses and render each as a row
        parts = re.split(r"[.,;،\n]+", prompt)
        for part in parts:
            part = part.strip()
            if part:
                lines.append({"text": part, "bold": False, "align": "left", "font_size": "normal"})

        lines.append({"text": sep2, "bold": False, "align": "center", "font_size": "normal"})
        lines.append({"text": footer, "bold": True, "align": "center", "font_size": "normal"})
        return lines


# Module-level singleton
_llm_service: Optional[LlmService] = None


def get_llm_service() -> LlmService:
    global _llm_service
    if _llm_service is None:
        _llm_service = LlmService()
    return _llm_service
