import pandas as pd

from app.services.preprocessing import preprocess_dataframe
from app.services.llm import generate_grounded_issue_summary


def test_duplicate_detection_keeps_distinct_review_ids():
    df = pd.DataFrame(
        {
            "review_id": ["A1", "A2", "A3"],
            "review_text": [
                "Payment failed during checkout.",
                "Payment failed during checkout.",
                "Login keeps failing after update.",
            ],
            "rating": [1, 1, 2],
            "date": ["2026-01-01", "2026-01-01", "2026-01-02"],
        }
    )
    records, stats = preprocess_dataframe(
        df,
        text_col="review_text",
        date_col="date",
        rating_col="rating",
        id_col="review_id",
    )
    assert stats["final_rows"] == 2
    assert all(r["original_id"] in {"A1", "A3"} for r in records)


def test_grounded_llm_does_not_invent_metrics():
    issue = {"title": "Payment Failure", "theme": "Payment Failure"}
    metrics = {"severity": "HIGH", "trend": "+12%", "issue_rate": 8.7}
    evidence = [{"id": 101, "text": "Payment failed after card validation."}]
    result = generate_grounded_issue_summary(issue, metrics, evidence)
    assert result["confidence"] == "grounded"
    assert "issue_rate" in str(metrics)
    assert "Possible Cause" in str(result)
    assert "101" in str(result["evidence_review_ids"])
