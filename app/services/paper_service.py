"""
Paper roll usage tracker.

Estimates paper consumption per job (mm) and tracks remaining roll length.
State is persisted in logs/paper_state.json so it survives container restarts.

NOTE: All figures are ESTIMATES — the printer does not report remaining paper.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

STATE_FILE = Path("./logs/paper_state.json")
DEFAULT_ROLL_MM = 80_000.0   # 80 m — standard 80×80 mm roll
OVERHEAD_MM     = 18.0        # init + feed(3) + cut per job


# ── Estimation constants ───────────────────────────────────────────────────────

def _estimate_mm(op: str, payload: dict) -> float:
    """Return estimated paper use in mm for a completed job."""
    if op == "print_text":
        lines = payload.get("lines", [])
        line_mm = sum(
            8.0 if l.get("font_size", "normal") in ("double", "double_height") else 4.0
            for l in lines
        ) or 4.0
        return line_mm + OVERHEAD_MM

    elif op == "print_qr":
        size = max(1, int(payload.get("size", 6)))
        return size * 4.5 + OVERHEAD_MM

    elif op == "print_image":
        # Can't cheaply decode base64 here; use a conservative fixed estimate
        return 45.0 + OVERHEAD_MM

    elif op == "print_aco":
        return 90.0  # fixed: header + table + QR + margins

    elif op == "print_smart":
        return 55.0  # variable; use a reasonable default

    else:
        return 30.0 + OVERHEAD_MM


# ── Service ───────────────────────────────────────────────────────────────────

class PaperService:
    """Tracks estimated paper roll usage across container restarts."""

    def __init__(self):
        self._state: dict = self._load()

    # ── Persistence ───────────────────────────────────────────────────────────

    def _default(self) -> dict:
        return {
            "total_roll_mm": DEFAULT_ROLL_MM,
            "used_mm": 0.0,
            "print_count": 0,
            "last_reset": datetime.now(timezone.utc).isoformat(),
            "last_print": None,
        }

    def _load(self) -> dict:
        if STATE_FILE.exists():
            try:
                return json.loads(STATE_FILE.read_text(encoding="utf-8"))
            except Exception as exc:
                logger.warning(f"paper_state load error: {exc}")
        return self._default()

    def _save(self) -> None:
        try:
            STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
            STATE_FILE.write_text(
                json.dumps(self._state, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        except Exception as exc:
            logger.warning(f"paper_state save error: {exc}")

    # ── Public API ────────────────────────────────────────────────────────────

    def record_print(self, op: str, payload: dict) -> None:
        """Call after every successful print to update the usage estimate."""
        self._state["used_mm"] = self._state.get("used_mm", 0.0) + _estimate_mm(op, payload)
        self._state["print_count"] = self._state.get("print_count", 0) + 1
        self._state["last_print"] = datetime.now(timezone.utc).isoformat()
        self._save()

    def reset_roll(self, total_roll_mm: Optional[float] = None) -> None:
        """Call when a new roll is loaded."""
        if total_roll_mm and total_roll_mm > 0:
            self._state["total_roll_mm"] = float(total_roll_mm)
        self._state["used_mm"] = 0.0
        self._state["print_count"] = 0
        self._state["last_reset"] = datetime.now(timezone.utc).isoformat()
        self._state["last_print"] = None
        self._save()

    def get_stats(self) -> dict:
        total   = float(self._state.get("total_roll_mm", DEFAULT_ROLL_MM))
        used    = min(float(self._state.get("used_mm", 0.0)), total)
        remaining = max(0.0, total - used)
        pct     = round(remaining / total * 100, 1) if total > 0 else 0.0
        count   = int(self._state.get("print_count", 0))
        avg_mm  = round(used / count, 1) if count > 0 else 30.0
        prints_remaining = int(remaining / avg_mm) if avg_mm > 0 else 0

        return {
            "total_roll_mm":     round(total, 1),
            "used_mm":           round(used, 1),
            "remaining_mm":      round(remaining, 1),
            "remaining_m":       round(remaining / 1000, 2),
            "remaining_pct":     pct,
            "print_count":       count,
            "avg_mm_per_print":  avg_mm,
            "prints_remaining":  prints_remaining,
            "last_reset":        self._state.get("last_reset"),
            "last_print":        self._state.get("last_print"),
        }


# ── Singleton ─────────────────────────────────────────────────────────────────

_paper_service: Optional[PaperService] = None


def get_paper_service() -> PaperService:
    global _paper_service
    if _paper_service is None:
        _paper_service = PaperService()
    return _paper_service
