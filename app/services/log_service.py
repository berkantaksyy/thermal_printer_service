"""
Structured logging service.

Log schema (from task spec):
  {ts, op, conn, jobId, status, error:{code, detail}}

Writes to JSON lines file. Supports CSV export.
"""

import asyncio
import csv
import io
import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from app.core.config import get_settings
from app.models.responses import LogEntry, ErrorDetail

logger = logging.getLogger(__name__)

_OPERATIONS = {
    "connect": "connect",
    "disconnect": "disconnect",
    "print_text": "print_text",
    "print_image": "print_image",
    "print_qr": "print_qr",
    "print_smart": "print_smart",
    "reprint": "reprint",
    "status": "status",
    "health": "health",
}


class LogService:
    def __init__(self):
        settings = get_settings()
        self._log_dir = Path(settings.log_dir)
        self._log_dir.mkdir(parents=True, exist_ok=True)
        self._log_file = self._log_dir / "printer_service.jsonl"
        self._lock = asyncio.Lock()

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _entry(
        self,
        op: str,
        status: str,
        conn: Optional[str] = None,
        job_id: Optional[str] = None,
        error_code: Optional[str] = None,
        error_detail: Optional[str] = None,
    ) -> dict:
        entry: dict = {
            "ts":     self._now_iso(),
            "op":     op,
            "conn":   conn,
            "jobId":  job_id,
            "status": status,
            "error":  None,
        }
        if error_code:
            entry["error"] = {"code": error_code, "detail": error_detail or ""}
        return entry

    async def log(
        self,
        op: str,
        status: str,
        conn: Optional[str] = None,
        job_id: Optional[str] = None,
        error_code: Optional[str] = None,
        error_detail: Optional[str] = None,
    ) -> None:
        entry = self._entry(op, status, conn, job_id, error_code, error_detail)
        async with self._lock:
            try:
                with open(self._log_file, "a", encoding="utf-8") as f:
                    f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            except Exception as exc:
                logger.warning(f"Failed to write log entry: {exc}")

    async def get_entries(
        self,
        page: int = 1,
        page_size: int = 100,
        status_filter: Optional[str] = None,
        op_filter: Optional[str] = None,
    ) -> tuple[int, list[LogEntry]]:
        entries: list[dict] = []
        if self._log_file.exists():
            with open(self._log_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass

        # Apply filters
        if status_filter:
            entries = [e for e in entries if e.get("status") == status_filter]
        if op_filter:
            entries = [e for e in entries if e.get("op") == op_filter]

        total = len(entries)
        start = (page - 1) * page_size
        end = start + page_size
        page_entries = entries[start:end]

        result: list[LogEntry] = []
        for e in page_entries:
            err = None
            if e.get("error"):
                err = ErrorDetail(code=e["error"]["code"], detail=e["error"]["detail"])
            result.append(LogEntry(
                ts=e.get("ts", ""),
                op=e.get("op", ""),
                conn=e.get("conn"),
                job_id=e.get("jobId"),
                status=e.get("status", ""),
                error=err,
            ))
        return total, result

    async def export_csv(self) -> str:
        """Return log entries as CSV string."""
        _total, entries = await self.get_entries(page=1, page_size=100_000)
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["ts", "op", "conn", "jobId", "status", "error_code", "error_detail"])
        for e in entries:
            writer.writerow([
                e.ts,
                e.op,
                e.conn or "",
                e.job_id or "",
                e.status,
                e.error.code if e.error else "",
                e.error.detail if e.error else "",
            ])
        return output.getvalue()

    async def clear_old_logs(self) -> None:
        """Remove log files older than LOG_KEEP_DAYS."""
        settings = get_settings()
        cutoff = time.time() - settings.log_keep_days * 86400
        for f in self._log_dir.glob("*.jsonl"):
            if f.stat().st_mtime < cutoff:
                f.unlink(missing_ok=True)


# Module-level singleton
_log_service: Optional[LogService] = None


def get_log_service() -> LogService:
    global _log_service
    if _log_service is None:
        _log_service = LogService()
    return _log_service
