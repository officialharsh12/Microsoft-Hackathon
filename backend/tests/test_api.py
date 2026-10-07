import os
import io
import pytest
from starlette.testclient import TestClient
from app.main import app
from app.database import init_db
from app.config import settings

client = TestClient(app)

def setup_module():
    init_db()

def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "models" in data
    assert "sentiment" in data["models"]

def test_csv_upload_and_pipeline():
    # Read the demo CSV
    demo_csv_path = settings.DATA_DIR / "demo_reviews.csv"
    assert demo_csv_path.exists()

    with open(demo_csv_path, "rb") as f:
        file_bytes = f.read()

    # Test Upload
    response = client.post(
        "/api/reviews/upload",
        files={"file": ("demo_reviews.csv", file_bytes, "text/csv")}
    )
    assert response.status_code == 200
    upload_data = response.json()
    assert "dataset_id" in upload_data
    dataset_id = upload_data["dataset_id"]
    assert upload_data["total_rows"] == 100
    assert upload_data["detected_text_column"] == "review_text"

    # Test Analyze
    analyze_payload = {
        "dataset_id": dataset_id,
        "text_column": upload_data["detected_text_column"],
        "date_column": upload_data["detected_date_column"],
        "rating_column": upload_data["detected_rating_column"],
        "id_column": upload_data["detected_id_column"],
    }
    analyze_res = client.post("/api/reviews/analyze", json=analyze_payload)
    assert analyze_res.status_code == 200
    an_data = analyze_res.json()
    assert an_data["status"] == "completed"
    assert an_data["total_reviews_analyzed"] > 0
    assert an_data["issues_discovered"] > 0

    # Test Dashboard
    dash_res = client.get(f"/api/dashboard?dataset_id={dataset_id}")
    assert dash_res.status_code == 200
    dash_data = dash_res.json()
    assert dash_data["total_reviews"] > 0
    assert len(dash_data["sentiment_distribution"]) == 2
    assert len(dash_data["top_issues"]) > 0

    # Test Issues endpoint
    issues_res = client.get(f"/api/issues?dataset_id={dataset_id}")
    assert issues_res.status_code == 200
    issues = issues_res.json()
    assert len(issues) > 0
    first_issue_id = issues[0]["id"]

    # Test Evidence endpoint
    evidence_res = client.get(f"/api/issues/{first_issue_id}/evidence")
    assert evidence_res.status_code == 200
    evidence_data = evidence_res.json()
    assert "evidence_reviews" in evidence_data
    assert len(evidence_data["evidence_reviews"]) > 0
    assert "detection_rationale" in evidence_data

    # Test PM Brief endpoint
    brief_res = client.get(f"/api/issues/{first_issue_id}/brief")
    assert brief_res.status_code == 200
    brief_data = brief_res.json()
    assert "problem_statement" in brief_data
    assert "customer_statements" in brief_data
    assert len(brief_data["customer_statements"]) > 0
    assert "investigation_areas" in brief_data
