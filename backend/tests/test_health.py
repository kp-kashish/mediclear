import os

os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("OPENAI_API_KEY", "fake")
os.environ.setdefault("AWS_ACCESS_KEY_ID", "fake")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "fake")
os.environ.setdefault("AWS_REGION", "eu-central-1")
os.environ.setdefault("S3_BUCKET_NAME", "fake")
os.environ.setdefault("DATABASE_URL", "postgresql://mediclear:mediclear@localhost:5432/mediclear_test")
os.environ.setdefault("MLFLOW_TRACKING_URI", "http://localhost:5000")

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["version"] == "0.1.0"