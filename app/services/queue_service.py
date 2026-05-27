"""
Job queue and failed-job persistence service.

Failed jobs are saved as JSON files under data/failed_jobs/
so they can be retrieved and reprinted by job ID.
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

FAILED_JOBS_DIR = Path("./data/failed_jobs")


class JobRecord:
    __slots__ = ("job_id", "op", "payload", "created_at", "attempts", "last_error", "is_duplicate")

    def __init__(
        self,
        job_id: str,
        op: str,
        payload: dict,
        created_at: Optional[str] = None,
    ):
        self.job_id = job_id
        self.op = op
        self.payload = payload
        self.created_at = created_at or datetime.now(timezone.utc).isoformat()
        self.attempts: int = 0
        self.last_error: Optional[str] = None
        self.is_duplicate: bool = False

    def to_dict(self) -> dict:
        return {
            "job_id": self.job_id,
            "op": self.op,
            "payload": self.payload,
            "created_at": self.created_at,
            "attempts": self.attempts,
            "last_error": self.last_error,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "JobRecord":
        rec = cls(d["job_id"], d["op"], d["payload"], d.get("created_at"))
        rec.attempts = d.get("attempts", 0)
        rec.last_error = d.get("last_error")
        return rec


class QueueService:
    """
    In-memory print queue + persistent failed-job store.
    """

    def __init__(self):
        FAILED_JOBS_DIR.mkdir(parents=True, exist_ok=True)
        self._pending: asyncio.Queue[JobRecord] = asyncio.Queue()
        self._seen_ids: set[str] = set()  # idempotency guard
        self._lock = asyncio.Lock()

    def generate_job_id(self) -> str:
        return str(uuid.uuid4())

    async def enqueue(self, op: str, payload: dict, job_id: Optional[str] = None) -> JobRecord:
        """Kuyruğa iş ekle. job_id daha önce görüldüyse mevcut kaydı döndür (idempotency)."""
        if job_id is None:
            job_id = self.generate_job_id()

        async with self._lock:
            if job_id in self._seen_ids:
                # Idempotent: tekrar işaretçisi döndür — çağıran yürütmeyi atlamalı
                rec = JobRecord(job_id=job_id, op=op, payload=payload)
                rec.is_duplicate = True
                return rec
            self._seen_ids.add(job_id)

        rec = JobRecord(job_id=job_id, op=op, payload=payload)
        await self._pending.put(rec)
        return rec

    async def get_next(self, timeout: float = 0.1) -> Optional[JobRecord]:
        """Sıradaki işi kuyruktan çıkar (zaman aşımı ile bloklamayan)."""
        try:
            return await asyncio.wait_for(self._pending.get(), timeout=timeout)
        except asyncio.TimeoutError:
            return None

    def queue_size(self) -> int:
        return self._pending.qsize()

    # ── Başarısız iş kalıcılığı ─────────────────────────────────────────────

    async def save_failed(self, rec: JobRecord, error: str) -> None:
        """Başarısız işi daha sonra yeniden yazdırmak için diske kaydet."""
        rec.last_error = error
        rec.attempts += 1
        path = FAILED_JOBS_DIR / f"{rec.job_id}.json"
        try:
            path.write_text(json.dumps(rec.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
            logger.info(f"Başarısız iş kaydedildi: {rec.job_id}")
        except Exception as exc:
            logger.warning(f"Başarısız iş {rec.job_id} kalıcı hale getirilemedi: {exc}")

    async def get_failed(self, job_id: str) -> Optional[JobRecord]:
        """ID'ye göre başarısız işi yükle."""
        path = FAILED_JOBS_DIR / f"{job_id}.json"
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return JobRecord.from_dict(data)
        except Exception as exc:
            logger.warning(f"Başarısız iş {job_id} yüklenemedi: {exc}")
            return None

    async def delete_failed(self, job_id: str) -> bool:
        """Başarısız iş kaydını kaldır (başarılı yeniden yazdırmadan sonra çağır)."""
        path = FAILED_JOBS_DIR / f"{job_id}.json"
        if path.exists():
            path.unlink()
            return True
        return False

    async def list_failed(self) -> list[dict]:
        """Tüm başarısız işleri listele."""
        results = []
        for f in sorted(FAILED_JOBS_DIR.glob("*.json")):
            try:
                results.append(json.loads(f.read_text(encoding="utf-8")))
            except Exception:
                pass
        return results


# Modül seviyesi singleton
_queue_service: Optional[QueueService] = None


def get_queue_service() -> QueueService:
    global _queue_service
    if _queue_service is None:
        _queue_service = QueueService()
    return _queue_service
