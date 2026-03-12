import logging

from fastapi import APIRouter, HTTPException, UploadFile, File
from datetime import datetime

from app.services.s3 import upload_pdf
from app.models.report import ReportUploadResponse

logger = logging.getLogger("mediclear")

router = APIRouter()

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


@router.post("/upload", response_model=ReportUploadResponse)
async def upload_report(file: UploadFile = File(...)) -> ReportUploadResponse:
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    file_bytes = await file.read()

    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File size exceeds 10MB limit")

    try:
        result = upload_pdf(file_bytes, file.filename)
    except Exception as e:
        logger.error("Upload failed: %s", e)
        raise HTTPException(status_code=500, detail="Failed to upload file")

    return ReportUploadResponse(
        report_id=result["report_id"],
        filename=result["filename"],
        uploaded_at=result["uploaded_at"],
        message="Report uploaded successfully. It will be deleted after 24 hours.",
    )