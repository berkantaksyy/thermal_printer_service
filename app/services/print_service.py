"""
Print service — orchestrates job execution, idempotency, and error recovery.
"""

import asyncio
import base64
import logging
import time
from datetime import datetime, timezone
from typing import Optional, Any

from app.core.escpos_engine import engine as escpos
from app.core.printer import require_printer
from app.core.error_handler import PrinterError, PrinterErrorCode
from app.models.requests import PrintTextRequest, PrintImageRequest, PrintQRRequest, SmartPrintRequest
from app.models.responses import JobResponse
from app.services.log_service import get_log_service
from app.services.queue_service import get_queue_service, JobRecord
from app.services.llm_service import get_llm_service
from app.services.i18n_service import get_i18n_service

logger = logging.getLogger(__name__)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _check_printer_status(status: dict, language: Optional[str] = None) -> None:
    """
    Status dict'indeki değerleri kontrol et.
    Değer None ise (sorgu desteklenmiyor) hata fırlatma.
    Değer False ise seçili dilde PrinterError fırlat.
    """
    i18n = get_i18n_service()
    lang = language or "tr"
    if status.get("paper_ok") is False:
        raise PrinterError(PrinterErrorCode.PAPER_OUT, i18n.t("error.paper_out", lang=lang))
    if status.get("cover_ok") is False:
        raise PrinterError(PrinterErrorCode.COVER_OPEN, i18n.t("error.cover_open", lang=lang))
    if status.get("temperature_ok") is False:
        raise PrinterError(PrinterErrorCode.OVERHEAT, i18n.t("error.overheat", lang=lang))


class PrintService:
    """
    Handles all print operations.
    - Assigns / validates job IDs (idempotency)
    - Sends ESC/POS bytes to printer
    - Logs every outcome
    - Saves failed jobs for reprint
    """

    async def print_text(self, req: PrintTextRequest) -> JobResponse:
        queue = get_queue_service()
        log = get_log_service()
        printer = require_printer()

        lines_payload = [l.model_dump() for l in req.lines]
        rec = await queue.enqueue(
            op="print_text",
            payload={"lines": lines_payload, "cut": req.cut},
            job_id=req.job_id,
        )
        if rec.is_duplicate:
            return JobResponse(job_id=rec.job_id, status="done",
                               message="Duplicate job — already processed.",
                               timestamp=datetime.now(timezone.utc))

        return await self._execute(
            rec=rec,
            printer=printer,
            data=escpos.build_receipt(lines_payload, cut=req.cut),
            log=log,
            conn=printer.connection_type(),
            language=req.language,
        )

    async def print_image(self, req: PrintImageRequest) -> JobResponse:
        queue = get_queue_service()
        log = get_log_service()
        printer = require_printer()

        try:
            image_bytes = base64.b64decode(req.image_base64)
        except Exception:
            raise PrinterError(PrinterErrorCode.UNKNOWN_COMMAND, "Invalid base64 image data.")

        img_data = escpos.image(image_bytes, align=req.align)
        cut_data = escpos.cut() if req.cut else b""

        rec = await queue.enqueue(
            op="print_image",
            payload={"align": req.align, "cut": req.cut},
            job_id=req.job_id,
        )
        if rec.is_duplicate:
            return JobResponse(job_id=rec.job_id, status="done",
                               message="Duplicate job — already processed.",
                               timestamp=datetime.now(timezone.utc))
        return await self._execute(
            rec=rec,
            printer=printer,
            data=escpos.init() + img_data + (escpos.feed_lines(3) if req.cut else b"") + cut_data,
            log=log,
            conn=printer.connection_type(),
            language=req.language,
        )

    async def print_qr(self, req: PrintQRRequest) -> JobResponse:
        queue = get_queue_service()
        log = get_log_service()
        printer = require_printer()

        qr_data = escpos.qr_code(
            data=req.data,
            size=req.size,
            error_correction=req.error_correction,
            align=req.align,
            label=req.label,
        )
        cut_data = escpos.cut() if req.cut else b""

        rec = await queue.enqueue(
            op="print_qr",
            payload={"data": req.data, "size": req.size, "align": req.align, "cut": req.cut},
            job_id=req.job_id,
        )
        if rec.is_duplicate:
            return JobResponse(job_id=rec.job_id, status="done",
                               message="Duplicate job — already processed.",
                               timestamp=datetime.now(timezone.utc))
        return await self._execute(
            rec=rec,
            printer=printer,
            data=escpos.init() + qr_data + (escpos.feed_lines(3) if req.cut else b"") + cut_data,
            log=log,
            conn=printer.connection_type(),
            language=req.language,
        )

    async def print_smart(self, req: SmartPrintRequest) -> JobResponse:
        """LLM-assisted smart receipt printing."""
        queue = get_queue_service()
        log = get_log_service()
        printer = require_printer()
        llm = get_llm_service()

        lang = req.language or "en"
        lines = await llm.generate_receipt_lines(req.data, language=lang, template_hint=req.template_hint)

        rec = await queue.enqueue(
            op="print_smart",
            payload={"data": req.data, "language": lang},
            job_id=req.job_id,
        )
        return await self._execute(
            rec=rec,
            printer=printer,
            data=escpos.build_receipt(lines, cut=req.cut),
            log=log,
            conn=printer.connection_type(),
        )

    async def reprint(self, job_id: str) -> JobResponse:
        """Retry a previously failed job."""
        queue = get_queue_service()
        log = get_log_service()
        printer = require_printer()

        rec = await queue.get_failed(job_id)
        if rec is None:
            raise PrinterError(
                PrinterErrorCode.UNKNOWN_COMMAND,
                f"Job ID '{job_id}' not found in failed queue.",
                job_id=job_id,
            )

        # Rebuild ESC/POS bytes from persisted payload
        data = self._rebuild_from_payload(rec.op, rec.payload)
        result = await self._execute(
            rec=rec,
            printer=printer,
            data=data,
            log=log,
            conn=printer.connection_type(),
        )
        if result.status == "done":
            await queue.delete_failed(job_id)
        return result

    async def _execute(
        self,
        rec: JobRecord,
        printer: Any,
        data: bytes,
        log: Any,
        conn: str,
    ) -> JobResponse:
        try:
            # ── Pre-flight: yazdırmadan önce yazıcı durumunu kontrol et ──────
            pre_status = await printer.get_status()
            _check_printer_status(pre_status)

            # ── Veriyi gönder ─────────────────────────────────────────────────
            await printer.write(data)

            # ── Post-print: yazıcının işlemi bitirmesi için kısa bekle ────────
            await asyncio.sleep(0.2)
            post_status = await printer.get_status()
            _check_printer_status(post_status)

            await log.log(op=rec.op, status="done", conn=conn, job_id=rec.job_id)
            return JobResponse(
                job_id=rec.job_id,
                status="done",
                message="Print job completed.",
                timestamp=datetime.now(timezone.utc),
            )
        except PrinterError as err:
            await log.log(
                op=rec.op,
                status="failed",
                conn=conn,
                job_id=rec.job_id,
                error_code=err.code.value,
                error_detail=err.detail,
            )
            await get_queue_service().save_failed(rec, err.detail)
            raise err

    def _rebuild_from_payload(self, op: str, payload: dict) -> bytes:
        """Reconstruct ESC/POS bytes from a persisted job payload."""
        if op == "print_text":
            return escpos.build_receipt(payload.get("lines", []), cut=payload.get("cut", True))
        elif op == "print_qr":
            return (
                escpos.init()
                + escpos.qr_code(
                    data=payload["data"],
                    size=payload.get("size", 6),
                    align=payload.get("align", "center"),
                )
                + (escpos.feed_lines(3) + escpos.cut() if payload.get("cut", True) else b"")
            )
        elif op == "print_smart":
            # Fallback: plain text dump of data
            lines = [{"text": f"{k}: {v}", "bold": False, "align": "left", "font_size": "normal"}
                     for k, v in payload.get("data", {}).items()]
            return escpos.build_receipt(lines)
        else:
            return b""


# Module-level singleton
_print_service: Optional[PrintService] = None


def get_print_service() -> PrintService:
    global _print_service
    if _print_service is None:
        _print_service = PrintService()
    return _print_service
