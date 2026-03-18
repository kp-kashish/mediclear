import logging
from typing import Any

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from app.core.config import settings

logger = logging.getLogger("mediclear")

llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
    api_key=settings.OPENAI_API_KEY,
)

EXTRACTION_PROMPT = ChatPromptTemplate.from_template("""
You are a medical data extraction assistant. Extract all biomarkers from the lab report text below.

For each biomarker return a JSON array with this exact structure:
{{
  "biomarkers": [
    {{
      "name": "biomarker name",
      "value": numeric value as float,
      "unit": "unit of measurement",
      "reference_range": "min - max",
      "status": "normal" or "borderline" or "abnormal"
    }}
  ]
}}

Rules:
- status is "abnormal" if the report says Low or High
- status is "borderline" if the report says Borderline
- status is "normal" if the value is within the reference range
- value must always be a float, never a string
- Return only valid JSON, nothing else

Lab report text:
{raw_text}
""")

EXPLANATION_PROMPT = ChatPromptTemplate.from_template("""
You are a friendly medical assistant explaining lab results to a patient with no medical background.

Biomarker: {name}
Value: {value} {unit}
Reference range: {reference_range}
Status: {status}

Medical reference:
{medline_context}

Write 2-3 sentences in plain English explaining:
1. What this biomarker measures
2. What the patient's result means
3. If abnormal or borderline, what it might indicate

Be reassuring but honest. Do not diagnose. Do not use medical jargon.
""")

QUESTIONS_PROMPT = ChatPromptTemplate.from_template("""
You are helping a patient prepare for a doctor's appointment.

Based on these abnormal or borderline lab results:
{abnormal_biomarkers}

Generate 5 clear, specific questions the patient should ask their doctor.
Return a JSON array of strings like this:
{{"questions": ["question 1", "question 2", "question 3", "question 4", "question 5"]}}

Return only valid JSON, nothing else.
""")

extraction_chain = EXTRACTION_PROMPT | llm | JsonOutputParser()
questions_chain = QUESTIONS_PROMPT | llm | JsonOutputParser()


def extract_biomarkers(raw_text: str) -> list[dict[str, Any]]:
    logger.info("Extracting biomarkers from raw text")
    result = extraction_chain.invoke({"raw_text": raw_text})
    biomarkers = result.get("biomarkers", [])
    logger.info("Extracted %d biomarkers", len(biomarkers))
    return biomarkers


def explain_biomarker(biomarker: dict[str, Any], medline_context: str) -> str:
    chain = EXPLANATION_PROMPT | llm
    response = chain.invoke({
        "name": biomarker["name"],
        "value": biomarker["value"],
        "unit": biomarker["unit"],
        "reference_range": biomarker["reference_range"],
        "status": biomarker["status"],
        "medline_context": medline_context,
    })
    return response.content


def generate_doctor_questions(abnormal_biomarkers: list[dict[str, Any]]) -> list[str]:
    if not abnormal_biomarkers:
        return []

    formatted = "\n".join(
        f"- {b['name']}: {b['value']} {b['unit']} ({b['status']})"
        for b in abnormal_biomarkers
    )

    logger.info("Generating doctor questions for %d abnormal biomarkers", len(abnormal_biomarkers))
    result = questions_chain.invoke({"abnormal_biomarkers": formatted})
    return result.get("questions", [])