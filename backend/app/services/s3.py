import logging
import uuid
from datetime import datetime

import boto3
from botocore.exceptions import ClientError

from app.core.config import settings

logger = logging.getLogger("mediclear")

s3_client = boto3.client(
    "s3",
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name=settings.AWS_REGION,
)


def upload_pdf(file_bytes: bytes, filename: str) -> dict:
    report_id = str(uuid.uuid4())
    key = f"reports/{report_id}/{filename}"

    try:
        s3_client.put_object(
            Bucket=settings.S3_BUCKET_NAME,
            Key=key,
            Body=file_bytes,
            ContentType="application/pdf",
            ServerSideEncryption="AES256",
        )
        logger.info("Uploaded %s to S3 key %s", filename, key)
    except ClientError as e:
        logger.error("S3 upload failed: %s", e)
        raise

    return {
        "report_id": report_id,
        "s3_key": key,
        "filename": filename,
        "uploaded_at": datetime.utcnow(),
    }


def get_presigned_url(s3_key: str, expires_in: int = 3600) -> str:
    try:
        url = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": settings.S3_BUCKET_NAME, "Key": s3_key},
            ExpiresIn=expires_in,
        )
        return url
    except ClientError as e:
        logger.error("Failed to generate presigned URL: %s", e)
        raise


def delete_object(s3_key: str) -> None:
    try:
        s3_client.delete_object(Bucket=settings.S3_BUCKET_NAME, Key=s3_key)
        logger.info("Deleted S3 object %s", s3_key)
    except ClientError as e:
        logger.error("S3 delete failed: %s", e)
        raise