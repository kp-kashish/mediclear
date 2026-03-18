import logging
from typing import Any

import boto3
from botocore.exceptions import ClientError

from app.core.config import settings
from app.services.pdf_parser import extract_from_bytes

logger = logging.getLogger("mediclear")

textract_client = boto3.client(
    "textract",
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name=settings.AWS_REGION,
)


def extract_from_s3(s3_key: str, fallback_bytes: bytes | None = None) -> dict[str, Any]:
    try:
        response = textract_client.analyze_document(
            Document={
                "S3Object": {
                    "Bucket": settings.S3_BUCKET_NAME,
                    "Name": s3_key,
                }
            },
            FeatureTypes=["TABLES", "FORMS"],
        )
        raw_text = _extract_raw_text(response)
        tables = _extract_tables(response)
        logger.info("Textract extracted %d characters and %d tables from %s", len(raw_text), len(tables), s3_key)
        return {"raw_text": raw_text, "tables": tables, "source": "textract"}

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code in ("SubscriptionRequiredException", "AccessDeniedException") and fallback_bytes:
            logger.warning("Textract unavailable (%s), falling back to PyMuPDF", error_code)
            result = extract_from_bytes(fallback_bytes)
            result["source"] = "pymupdf"
            return result
        logger.error("Textract extraction failed for %s: %s", s3_key, e)
        raise


def _extract_raw_text(response: dict) -> str:
    blocks = response.get("Blocks", [])
    lines = [b["Text"] for b in blocks if b["BlockType"] == "LINE"]
    return "\n".join(lines)


def _extract_tables(response: dict) -> list[list[list[str]]]:
    blocks = response.get("Blocks", [])
    block_map = {b["Id"]: b for b in blocks}

    tables = []
    for block in blocks:
        if block["BlockType"] != "TABLE":
            continue

        table_rows: dict[int, dict[int, str]] = {}

        for rel in block.get("Relationships", []):
            if rel["Type"] != "CHILD":
                continue
            for cell_id in rel["Ids"]:
                cell = block_map.get(cell_id)
                if not cell or cell["BlockType"] != "CELL":
                    continue

                row = cell["RowIndex"]
                col = cell["ColumnIndex"]
                cell_text = ""

                for cell_rel in cell.get("Relationships", []):
                    if cell_rel["Type"] != "CHILD":
                        continue
                    for word_id in cell_rel["Ids"]:
                        word = block_map.get(word_id)
                        if word and word["BlockType"] == "WORD":
                            cell_text += word["Text"] + " "

                if row not in table_rows:
                    table_rows[row] = {}
                table_rows[row][col] = cell_text.strip()

        if table_rows:
            max_row = max(table_rows.keys())
            max_col = max(col for row in table_rows.values() for col in row.keys())
            grid = [
                [table_rows.get(r, {}).get(c, "") for c in range(1, max_col + 1)]
                for r in range(1, max_row + 1)
            ]
            tables.append(grid)

    return tables