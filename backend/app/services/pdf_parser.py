import logging
from typing import Any

import fitz

logger = logging.getLogger("mediclear")


def extract_from_bytes(file_bytes: bytes) -> dict[str, Any]:
    raw_text, tables = "", []

    with fitz.open(stream=file_bytes, filetype="pdf") as doc:
        for page in doc:
            raw_text += page.get_text()
            tables.extend(_extract_tables_from_page(page))

    logger.info("PyMuPDF extracted %d characters and %d tables", len(raw_text), len(tables))

    return {
        "raw_text": raw_text.strip(),
        "tables": tables,
    }


def _extract_tables_from_page(page: fitz.Page) -> list[list[list[str]]]:
    tables = []

    for table in page.find_tables():
        grid = []
        for row in table.extract():
            cleaned = [cell.strip() if cell else "" for cell in row]
            grid.append(cleaned)
        if grid:
            tables.append(grid)

    return tables