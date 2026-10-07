import json
from typing import List, Dict, Any, Optional
import numpy as np
from app.services.theme_discovery import discover_themes
from app.services.severity import calculate_severity
from app.services.trends import calculate_issue_trend
from app.services.evidence import build_evidence_chain

def aggregate_issues(
    reviews: List[Dict[str, Any]],
    embeddings: np.ndarray,
    cluster_labels: np.ndarray
) -> List[Dict[str, Any]]:
    """
    Transforms review clusters into prioritized product issues with severity, trends, and evidence.
    """
    total_dataset_reviews = len(reviews)
    if total_dataset_reviews == 0:
        return []

    # 1. Discover cluster themes and representative items
    themes = discover_themes(reviews, embeddings, cluster_labels)
    all_dates = [r["review_date"] for r in reviews if r.get("review_date")]

    issues = []
    for theme_data in themes:
        cluster_id = theme_data["cluster_id"]
        review_indices = theme_data["review_indices"]
        cluster_revs = [reviews[i] for i in review_indices]
        cluster_embs = embeddings[review_indices]
        rev_count = theme_data["review_count"]
        neg_pct = theme_data["negative_percentage"]
        dominant_emotion = theme_data["dominant_emotion"]

        # Calculate average rating for this cluster if available
        ratings = [r["rating"] for r in cluster_revs if r.get("rating") is not None]
        avg_rating = (sum(ratings) / len(ratings)) if ratings else None

        # 2. Trend calculation
        trend_info = calculate_issue_trend(cluster_revs, all_dates)
        trend_pct = trend_info.get("trend_percentage")

        # 3. Severity calculation
        severity_info = calculate_severity(
            review_count=rev_count,
            total_dataset_reviews=total_dataset_reviews,
            negative_percentage=neg_pct,
            dominant_emotion=dominant_emotion,
            avg_rating=avg_rating,
            representative_texts=theme_data["representative_reviews"],
            trend_percentage=trend_pct
        )

        # 4. Emerging Issue Radar check:
        # Rapidly increasing, frequent, strongly negative, and severe
        is_emerging = False
        if trend_info.get("trend_direction") in ["increasing", "spike"] or (trend_pct is not None and trend_pct >= 20.0):
            freq_condition = rev_count >= 3 and (rev_count / total_dataset_reviews) >= 0.04
            neg_condition = neg_pct >= 60.0
            sev_condition = severity_info["severity"] in ["CRITICAL", "HIGH"]
            if freq_condition and neg_condition and sev_condition:
                is_emerging = True

        issue_record = {
            "cluster_id": cluster_id,
            "theme": theme_data["theme"],
            "keywords": theme_data["keywords"],
            "review_count": rev_count,
            "positive_count": theme_data["positive_count"],
            "negative_count": theme_data["negative_count"],
            "negative_percentage": neg_pct,
            "dominant_emotion": dominant_emotion,
            "severity": severity_info["severity"],
            "severity_score": severity_info["severity_score"],
            "severity_reason": severity_info["reason"],
            "trend": trend_info["trend"],
            "trend_direction": trend_info["trend_direction"],
            "trend_percentage": trend_pct,
            "trend_reason": trend_info["reason"],
            "timeline": trend_info["timeline"],
            "is_emerging": is_emerging,
            "sample_quotes": theme_data["representative_reviews"][:3],
            "representative_review_ids": theme_data["representative_review_ids"],
            "review_indices": review_indices,
        }
        issues.append(issue_record)

    # Sort: Emerging first, then Critical/High severity, then review volume
    def sort_order(issue):
        sev_rank = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}.get(issue["severity"], 0)
        return (
            1 if issue["is_emerging"] else 0,
            sev_rank,
            issue["severity_score"],
            issue["review_count"]
        )

    issues.sort(key=sort_order, reverse=True)
    return issues
