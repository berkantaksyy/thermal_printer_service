"""
Print endpoints — two clear options:

  ── Option 1 (Standard — no external dependencies) ───────────────────────────
  POST /print/text    — formatted text lines
  POST /print/image   — base64 PNG/JPEG
  POST /print/qr      — QR code with optional label

  ── Option 2 (LLM-assisted — requires LLM_ENABLED=true in .env) ─────────────
  POST /print/smart   — send structured JSON, LLM formats it as a receipt
"""

from fastapi import APIRouter, Depends

from app.api.deps import verify_token
from app.core.error_handler import PrinterError, printer_error_to_http
from app.models.requests import (
    PrintTextRequest,
    PrintImageRequest,
    PrintQRRequest,
    SmartPrintRequest,
)
from app.models.responses import JobResponse
from app.services.print_service import get_print_service

# ── Option 1: Standard print endpoints (no LLM, no external dependency) ──────
router = APIRouter(
    prefix="/print",
    tags=["🖨️ Print — Option 1 (Standard)"],
)

# ── Option 2: LLM-assisted endpoint (separate router + separate Swagger tag) ──
llm_router = APIRouter(
    prefix="/print",
    tags=["🤖 Print — Option 2 (LLM, optional)"],
)


@router.post(
    "/text",
    response_model=JobResponse,
    dependencies=[Depends(verify_token)],
    summary="Print text lines",
)
async def print_text(req: PrintTextRequest):
    """
    **Option 1 — Standard (no external dependency)**

    Print one or more formatted text lines.
    Supports bold, underline, alignment (left/center/right), and font sizes.
    Assign a `job_id` for idempotency — re-sending the same ID is a no-op.
    """
    try:
        return await get_print_service().print_text(req)
    except PrinterError as err:
        raise printer_error_to_http(err)


@router.post(
    "/image",
    response_model=JobResponse,
    dependencies=[Depends(verify_token)],
    summary="Print base64 image",
)
async def print_image(req: PrintImageRequest):
    """
    **Option 1 — Standard (no external dependency)**

    Print a PNG or JPEG image supplied as a base64 string.
    Image is auto-scaled to the printer's paper width (576px @ 203dpi).
    """
    try:
        return await get_print_service().print_image(req)
    except PrinterError as err:
        raise printer_error_to_http(err)


@router.post(
    "/qr",
    response_model=JobResponse,
    dependencies=[Depends(verify_token)],
    summary="Print QR code",
)
async def print_qr(req: PrintQRRequest):
    """
    **Option 1 — Standard (no external dependency)**

    Print a QR code using the printer's native ESC/POS GS(k command.
    Optional `label` text is printed below the QR.
    """
    try:
        return await get_print_service().print_qr(req)
    except PrinterError as err:
        raise printer_error_to_http(err)


@llm_router.post(
    "/smart",
    response_model=JobResponse,
    dependencies=[Depends(verify_token)],
    summary="LLM-assisted receipt from JSON data",
)
async def print_smart(req: SmartPrintRequest):
    """
    **Option 2 — LLM-assisted (requires `LLM_ENABLED=true` in docker-compose.yml)**

    Send arbitrary structured JSON data and let the LLM format it as a
    human-readable receipt in the requested language.

    Configuration (all via `docker-compose.yml` environment section):
    - `LLM_ENABLED=true`
    - `OPENROUTER_API_KEY=sk-or-...`
    - `OPENROUTER_MODEL=mistralai/mistral-7b-instruct:free`

    **When LLM is disabled:** falls back automatically to a simple key-value
    receipt format — the endpoint always works, just without AI formatting.

    > ⚠️ This feature uses an external API (OpenRouter). Disabled by default.
    > Task note: *"Dış servis/anahtar gerektiren ücretli SDK kullanmayınız
    > (gerekirse açıkça not ediniz)"* — documented here as required.
    """
    try:
        return await get_print_service().print_smart(req)
    except PrinterError as err:
        raise printer_error_to_http(err)
