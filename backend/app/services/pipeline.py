import logging
from datetime import datetime
from typing import Any

from app.services.s3 import upload_pdf
from app.services.textract import extract_from_s3
from app.services.embeddings import index_report
from app.services.analyzer import analyze_report

logger = logging.getLogger("mediclear")


def process_report(file_bytes: bytes, filename: str) -> dict[str, Any]:
    logger.info("Starting full pipeline for %s", filename)

    upload_result = upload_pdf(file_bytes, filename)
    report_id = upload_result["report_id"]
    s3_key = upload_result["s3_key"]

    logger.info("Report uploaded with id %s", report_id)

    extraction_result = extract_from_s3(s3_key, fallback_bytes=file_bytes)
    raw_text = extraction_result["raw_text"]
    extraction_source = extraction_result["source"]

    logger.info("Extraction complete via %s", extraction_source)

    chunk_count = index_report(report_id, raw_text)
    logger.info("Indexed %d chunks for report %s", chunk_count, report_id)

    analysis_result = analyze_report(report_id, raw_text)
    logger.info("Analysis complete for report %s", report_id)

    return {
        "report_id": report_id,
        "filename": filename,
        "extraction_source": extraction_source,
        "chunk_count": chunk_count,
        "biomarkers": analysis_result["biomarkers"],
        "questions_for_doctor": analysis_result["questions_for_doctor"],
        "analyzed_at": analysis_result["analyzed_at"],
    }