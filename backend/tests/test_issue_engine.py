import numpy as np
from app.services.clustering import cluster_embeddings
from app.services.theme_discovery import discover_themes
from app.services.severity import calculate_severity
from app.services.trends import calculate_issue_trend
from app.services.issue_engine import aggregate_issues
from app.services.evidence import build_evidence_chain

def test_severity_calculation():
    # High risk scenario
    sev = calculate_severity(
        review_count=50,
        total_dataset_reviews=100,
        negative_percentage=90.0,
        dominant_emotion="anger",
        avg_rating=1.2,
        representative_texts=["Checkout crashed and payment failed twice"],
        trend_percentage=45.0
    )
    assert sev["severity"] in ["CRITICAL", "HIGH"]
    assert sev["severity_score"] > 0.6
    assert "negative" in sev["reason"].lower() or "anger" in sev["reason"].lower()

def test_trend_calculation_with_dates():
    cluster_reviews = [
        {"review_date": "2026-03-01"},
        {"review_date": "2026-03-01"},
        {"review_date": "2026-03-10"},
        {"review_date": "2026-03-11"},
        {"review_date": "2026-03-12"},
        {"review_date": "2026-03-12"},
    ]
    trend = calculate_issue_trend(cluster_reviews)
    assert trend["trend_direction"] in ["increasing", "spike"]
    assert trend["trend_percentage"] is not None
    assert len(trend["timeline"]) > 0

def test_trend_calculation_without_dates():
    cluster_reviews = [
        {"raw_text": "Good app"},
        {"raw_text": "Slow app"}
    ]
    trend = calculate_issue_trend(cluster_reviews)
    assert trend["trend"] == "N/A"
    assert trend["trend_direction"] == "unavailable"
    assert trend["trend_percentage"] is None
    assert "no date information" in trend["reason"]

def test_aggregate_issues_and_evidence():
    # 6 mock reviews in 2 clusters
    mock_reviews = [
        {"id": 1, "cleaned_text": "Payment failed during checkout", "sentiment": "NEGATIVE", "sentiment_score": 0.95, "emotion": "anger", "rating": 1, "review_date": "2026-03-15"},
        {"id": 2, "cleaned_text": "Money was deducted but payment failed", "sentiment": "NEGATIVE", "sentiment_score": 0.92, "emotion": "anger", "rating": 1, "review_date": "2026-03-16"},
        {"id": 3, "cleaned_text": "Cannot complete credit card payment", "sentiment": "NEGATIVE", "sentiment_score": 0.88, "emotion": "annoyance", "rating": 2, "review_date": "2026-03-16"},
        {"id": 4, "cleaned_text": "Super fast app, great UI and design", "sentiment": "POSITIVE", "sentiment_score": 0.98, "emotion": "joy", "rating": 5, "review_date": "2026-03-01"},
        {"id": 5, "cleaned_text": "Love the clean layout and smooth gestures", "sentiment": "POSITIVE", "sentiment_score": 0.94, "emotion": "admiration", "rating": 5, "review_date": "2026-03-02"},
        {"id": 6, "cleaned_text": "Very clean user interface and easy to use", "sentiment": "POSITIVE", "sentiment_score": 0.91, "emotion": "joy", "rating": 5, "review_date": "2026-03-03"},
    ]
    
    # Synthetic mock embeddings: cluster 0 (first 3), cluster 1 (next 3)
    emb0 = np.array([1.0, 0.0, 0.0] + [0.0] * 381, dtype=np.float32)
    emb1 = np.array([0.0, 1.0, 0.0] + [0.0] * 381, dtype=np.float32)
    embeddings = np.array([
        emb0 + np.random.normal(0, 0.01, 384),
        emb0 + np.random.normal(0, 0.01, 384),
        emb0 + np.random.normal(0, 0.01, 384),
        emb1 + np.random.normal(0, 0.01, 384),
        emb1 + np.random.normal(0, 0.01, 384),
        emb1 + np.random.normal(0, 0.01, 384),
    ], dtype=np.float32)
    
    cluster_labels = np.array([0, 0, 0, 1, 1, 1])

    issues = aggregate_issues(mock_reviews, embeddings, cluster_labels)
    assert len(issues) == 2
    # The negative payment cluster should have higher severity than the positive UI cluster
    payment_issue = next(i for i in issues if "payment" in i["theme"].lower() or i["negative_percentage"] > 80)
    assert payment_issue["negative_percentage"] == 100.0
    assert payment_issue["severity"] in ["CRITICAL", "HIGH"]

    evidence = build_evidence_chain(payment_issue, [mock_reviews[0], mock_reviews[1], mock_reviews[2]])
    assert evidence["evidence_count"] == 3
    assert len(evidence["evidence_reviews"]) == 3
    assert "detection_rationale" in evidence
