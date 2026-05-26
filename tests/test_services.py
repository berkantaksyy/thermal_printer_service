"""
Unit tests for log, queue, and i18n services.
"""

import os
import asyncio
import pytest
import pytest_asyncio

os.environ.setdefault("LOG_DIR", "/tmp/thermal_test_logs")
os.environ.setdefault("API_BEARER_TOKEN", "test-token")
os.environ.setdefault("LLM_ENABLED", "false")


# ── Log service ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_log_write_and_read():
    from app.services.log_service import LogService
    import tempfile, pathlib
    with tempfile.TemporaryDirectory() as tmpdir:
        svc = LogService.__new__(LogService)
        svc._log_dir = pathlib.Path(tmpdir)
        svc._log_file = svc._log_dir / "test.jsonl"
        svc._lock = asyncio.Lock()

        await svc.log(op="print_text", status="done", conn="usb", job_id="test-001")
        await svc.log(op="print_text", status="failed", conn="usb", job_id="test-002",
                      error_code="PAPER_OUT", error_detail="Paper is out")

        total, entries = await svc.get_entries()
        assert total == 2
        assert entries[0].op == "print_text"
        assert entries[1].error is not None
        assert entries[1].error.code == "PAPER_OUT"


@pytest.mark.asyncio
async def test_log_csv_export():
    from app.services.log_service import LogService
    import tempfile, pathlib, asyncio
    with tempfile.TemporaryDirectory() as tmpdir:
        svc = LogService.__new__(LogService)
        svc._log_dir = pathlib.Path(tmpdir)
        svc._log_file = svc._log_dir / "test.jsonl"
        svc._lock = asyncio.Lock()
        await svc.log(op="connect", status="done", conn="lan")
        csv = await svc.export_csv()
        assert "ts,op,conn" in csv
        assert "connect" in csv


@pytest.mark.asyncio
async def test_log_filter_by_status():
    from app.services.log_service import LogService
    import tempfile, pathlib, asyncio
    with tempfile.TemporaryDirectory() as tmpdir:
        svc = LogService.__new__(LogService)
        svc._log_dir = pathlib.Path(tmpdir)
        svc._log_file = svc._log_dir / "test.jsonl"
        svc._lock = asyncio.Lock()
        await svc.log(op="print_text", status="done")
        await svc.log(op="print_text", status="failed", error_code="COMM_ERROR", error_detail="comm err")
        total, entries = await svc.get_entries(status_filter="failed")
        assert total == 1
        assert entries[0].status == "failed"


# ── Queue service ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_queue_enqueue_and_dequeue():
    from app.services.queue_service import QueueService
    svc = QueueService()
    rec = await svc.enqueue("print_text", {"lines": []}, job_id="q-001")
    assert rec.job_id == "q-001"
    assert svc.queue_size() == 1
    got = await svc.get_next(timeout=0.1)
    assert got is not None
    assert got.job_id == "q-001"
    assert svc.queue_size() == 0


@pytest.mark.asyncio
async def test_queue_idempotency():
    from app.services.queue_service import QueueService
    svc = QueueService()
    r1 = await svc.enqueue("print_text", {"lines": []}, job_id="idp-001")
    r2 = await svc.enqueue("print_text", {"lines": []}, job_id="idp-001")
    # Second enqueue should NOT add to queue
    assert r1.job_id == r2.job_id
    assert svc.queue_size() == 1  # only 1 item


@pytest.mark.asyncio
async def test_failed_job_persist_and_retrieve():
    from app.services.queue_service import QueueService
    import tempfile, pathlib
    with tempfile.TemporaryDirectory() as tmpdir:
        svc = QueueService.__new__(QueueService)
        svc._pending = asyncio.Queue()
        svc._seen_ids = set()
        svc._lock = asyncio.Lock()
        # Patch failed jobs dir
        import app.services.queue_service as qs_mod
        orig = qs_mod.FAILED_JOBS_DIR
        qs_mod.FAILED_JOBS_DIR = pathlib.Path(tmpdir)

        rec = await svc.enqueue("print_qr", {"data": "test"}, job_id="fail-001")
        await svc.save_failed(rec, "Paper out")
        loaded = await svc.get_failed("fail-001")
        assert loaded is not None
        assert loaded.job_id == "fail-001"
        assert loaded.last_error == "Paper out"
        await svc.delete_failed("fail-001")
        assert await svc.get_failed("fail-001") is None

        qs_mod.FAILED_JOBS_DIR = orig


# ── i18n service ──────────────────────────────────────────────────────────────

def test_i18n_english():
    from app.services.i18n_service import I18nService
    svc = I18nService()
    msg = svc.t("error.paper_out", lang="en")
    assert "paper" in msg.lower() or "Paper" in msg


def test_i18n_turkish():
    from app.services.i18n_service import I18nService
    svc = I18nService()
    msg = svc.t("error.paper_out", lang="tr")
    assert "Kağıt" in msg or "kağıt" in msg


def test_i18n_fallback_to_english():
    from app.services.i18n_service import I18nService
    svc = I18nService()
    # Non-existent key falls back to key itself
    result = svc.t("this.key.does.not.exist", lang="en")
    assert result == "this.key.does.not.exist"


def test_i18n_all_error_codes_have_translations():
    from app.services.i18n_service import I18nService
    from app.core.error_handler import PrinterErrorCode, ERROR_METADATA
    svc = I18nService()
    for code, (_, i18n_key, _) in ERROR_METADATA.items():
        for lang in ["en", "tr", "de", "fr"]:
            result = svc.t(i18n_key, lang=lang)
            # Should not fall back to key (all codes should be translated)
            assert result != i18n_key, f"Missing translation for {i18n_key} in {lang}"


# ── Error codes ───────────────────────────────────────────────────────────────

def test_all_error_codes_defined():
    from app.core.error_handler import PrinterErrorCode, ERROR_METADATA
    for code in PrinterErrorCode:
        assert code in ERROR_METADATA, f"{code} not in ERROR_METADATA"


def test_error_http_status():
    from app.core.error_handler import PrinterError, PrinterErrorCode
    err = PrinterError(PrinterErrorCode.PAPER_OUT)
    assert err.http_status == 503
    err2 = PrinterError(PrinterErrorCode.COMM_ERROR)
    assert err2.http_status == 502
    err3 = PrinterError(PrinterErrorCode.UNKNOWN_COMMAND)
    assert err3.http_status == 400
