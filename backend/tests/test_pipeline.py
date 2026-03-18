import os

os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("OPENAI_API_KEY", "fake")
os.environ.setdefault("AWS_ACCESS_KEY_ID", "fake")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "fake")
os.environ.setdefault("AWS_REGION", "eu-central-1")
os.environ.setdefault("S3_BUCKET_NAME", "fake")
os.environ.setdefault("DATABASE_URL", "postgresql://mediclear:mediclear@localhost:5432/mediclear_test")
os.environ.setdefault("MLFLOW_TRACKING_URI", "http://localhost:5000")

from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_upload_rejects_non_pdf():
    response = client.post(
        "/api/v1/reports/upload",
        files={"file": ("test.txt", b"not a pdf", "text/plain")},
    )
    assert response.status_code == 400
    assert "PDF" in response.json()["detail"]


def test_upload_rejects_large_file():
    large_bytes = b"%PDF-1.4" + b"0" * (11 * 1024 * 1024)
    response = client.post(
        "/api/v1/reports/upload",
        files={"file": ("large.pdf", large_bytes, "application/pdf")},
    )
    assert response.status_code == 400
    assert "10MB" in response.json()["detail"]


@patch("app.services.s3.s3_client")
def test_upload_success(mock_s3):
    mock_s3.put_object.return_value = {}

    pdf_bytes = b"%PDF-1.4 test content"
    response = client.post(
        "/api/v1/reports/upload",
        files={"file": ("Blood report.pdf", pdf_bytes, "application/pdf")},
    )
    assert response.status_code == 200
    data = response.json()
    assert "report_id" in data
    assert data["filename"] == "Blood report.pdf"
    assert "uploaded_at" in data


@patch("app.services.pipeline.upload_pdf")
@patch("app.services.pipeline.extract_from_s3")
@patch("app.services.pipeline.index_report")
@patch("app.services.pipeline.analyze_report")
def test_process_endpoint(
    mock_analyze, mock_index, mock_extract, mock_upload
):
    from datetime import datetime

    mock_upload.return_value = {
        "report_id": "test-id-123",
        "s3_key": "reports/test-id-123/Blood report.pdf",
        "filename": "Blood report.pdf",
        "uploaded_at": datetime.utcnow(),
    }
    mock_extract.return_value = {
        "raw_text": "Hemoglobin (Hb) 12.5 Low 13.0 - 17.0 g/dL",
        "tables": [],
        "source": "pymupdf",
    }
    mock_index.return_value = 3
    mock_analyze.return_value = {
        "report_id": "test-id-123",
        "biomarkers": [
            {
                "name": "Hemoglobin (Hb)",
                "value": 12.5,
                "unit": "g/dL",
                "reference_range": "13.0 - 17.0",
                "status": "abnormal",
                "explanation": "Your hemoglobin is slightly low.",
            }
        ],
        "questions_for_doctor": ["What does low hemoglobin mean for me?"],
        "analyzed_at": datetime.utcnow(),
    }

    pdf_bytes = b"%PDF-1.4 test content"
    response = client.post(
        "/api/v1/reports/process",
        files={"file": ("Blood report.pdf", pdf_bytes, "application/pdf")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["report_id"] == "test-id-123"
    assert data["extraction_source"] == "pymupdf"
    assert data["chunk_count"] == 3
    assert len(data["biomarkers"]) == 1
    assert data["biomarkers"][0]["status"] == "abnormal"
    assert len(data["questions_for_doctor"]) == 1