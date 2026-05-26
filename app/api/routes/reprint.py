"""
POST /reprint — Retry a failed print job by job ID
"""

from fastapi import APIRouter, Depends

from app.api.deps import verify_token
from app.core.error_handler import PrinterError, printer_error_to_http
from app.models.requests import ReprintRequest
from app.models.responses import JobResponse
from app.services.print_service import get_print_service

router = APIRouter(tags=["Reprint"])


@router.post("/reprint", response_model=JobResponse, dependencies=[Depends(verify_token)])
async def reprint(req: ReprintRequest):
    """
    Retry a previously failed print job.
    The job must exist in data/failed_jobs/ (saved automatically on failure).
    On success, the job is removed from the failed queue.
    """
    try:
        return await get_print_service().reprint(req.job_id)
    except PrinterError as err:
        raise printer_error_to_http(err)
