from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class BiomarkerStatus(str, Enum):
    normal = "normal"
    borderline = "borderline"
    abnormal = "abnormal"


class Biomarker(BaseModel):
    name: str
    value: float
    unit: str
    reference_range: str
    status: BiomarkerStatus


class ReportUploadResponse(BaseModel):
    report_id: str
    filename: str
    uploaded_at: datetime
    message: str


class ExtractionResponse(BaseModel):
    report_id: str
    raw_text: str
    tables: list[list[list[str]]]
    extracted_at: datetime


class ReportAnalysisResponse(BaseModel):
    report_id: str
    biomarkers: list[Biomarker]
    summary: str
    questions_for_doctor: list[str]
    analyzed_at: datetime