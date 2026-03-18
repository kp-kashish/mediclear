import logging
from datetime import datetime
from typing import Any

from app.services.llm import extract_biomarkers, explain_biomarker, generate_doctor_questions
from app.services.medline_indexer import query_medline

logger = logging.getLogger("mediclear")


def analyze_report(report_id: str, raw_text: str) -> dict[str, Any]:
    logger.info("Starting analysis for report %s", report_id)

    biomarkers = extract_biomarkers(raw_text)

    explained_biomarkers = []
    for biomarker in biomarkers:
        medline_context = "\n".join(query_medline(biomarker["name"], n_results=2))
        explanation = explain_biomarker(biomarker, medline_context)
        explained_biomarkers.append({**biomarker, "explanation": explanation})

    abnormal = [
        b for b in explained_biomarkers
        if b["status"] in ("abnormal", "borderline")
    ]

    questions = generate_doctor_questions(abnormal)

    logger.info(
        "Analysis complete for report %s — %d biomarkers, %d abnormal, %d questions",
        report_id, len(explained_biomarkers), len(abnormal), len(questions),
    )

    return {
        "report_id": report_id,
        "biomarkers": explained_biomarkers,
        "questions_for_doctor": questions,
        "analyzed_at": datetime.utcnow(),
    }