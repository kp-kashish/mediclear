import logging
from datetime import datetime

import boto3
from botocore.exceptions import ClientError
from fastapi import APIRouter, File, HTTPException, UploadFile

from app.core.config import settings
from app.models.report import ExtractionResponse, ReportUploadResponse
from app.services.s3 import upload_pdf
from app.services.textract import extract_from_s3

logger = logging.getLogger("mediclear")

router = APIRouter()

MAX_FILE_SIZE = 10 * 1024 * 1024


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


@router.post("/extract/{report_id}", response_model=ExtractionResponse)
async def extract_report(report_id: str, filename: str) -> ExtractionResponse:
    s3_key = f"reports/{report_id}/{filename}"

    s3_client = boto3.client(
        "s3",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_REGION,
    )

    try:
        s3_response = s3_client.get_object(Bucket=settings.S3_BUCKET_NAME, Key=s3_key)
        file_bytes = s3_response["Body"].read()
    except ClientError as e:
        logger.error("Failed to fetch file from S3 %s: %s", s3_key, e)
        raise HTTPException(status_code=404, detail="Report not found in storage")

    try:
        result = extract_from_s3(s3_key, fallback_bytes=file_bytes)
    except Exception as e:
        logger.error("Extraction failed for report %s: %s", report_id, e)
        raise HTTPException(status_code=500, detail="Failed to extract text from report")

    return ExtractionResponse(
        report_id=report_id,
        raw_text=result["raw_text"],
        tables=result["tables"],
        extracted_at=datetime.utcnow(),
    )