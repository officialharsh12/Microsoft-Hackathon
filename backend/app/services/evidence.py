from typing import List, Dict, Any, Optional
import numpy as np

def build_evidence_chain(
    issue_info: Dict[str, Any],
    cluster_reviews: List[Dict[str, Any]],
    cluster_embeddings: Optional[np.ndarray] = None,
    limit: int = 10
) -> Dict[str, Any]:
    """
    Constructs the complete evidence chain and explanation for why an issue was flagged.
    """
    total_reviews = len(cluster_reviews)
    if total_reviews == 0:
        return {
            "issue_id": issue_info.get("id"),
            "theme": issue_info.get("theme"),
            "detection_rationale": "No reviews found for this issue.",
            "evidence_count": 0,
            "evidence_reviews": []
        }

    # Rank reviews by semantic centrality if embeddings available
    if cluster_embeddings is not None and len(cluster_embeddings) == total_reviews:
        centroid = np.mean(cluster_embeddings, axis=0)
        sims = np.dot(cluster_embeddings, centroid)
        ranked_indices = np.argsort(sims)[::-1]
        sorted_reviews = [cluster_reviews[i] for i in ranked_indices]
    else:
        # Otherwise sort by sentiment score descending (most severe negatives first)
        def sort_key(r):
            is_neg = 1 if r.get("sentiment") == "NEGATIVE" else 0
            score = r.get("sentiment_score") or 0.5
            return (is_neg, score)
        sorted_reviews = sorted(cluster_reviews, key=sort_key, reverse=True)

    evidence_reviews = sorted_reviews[:limit]

    # Generate explainable detection rationale
    theme = issue_info.get("theme", "Detected Issue")
    neg_pct = issue_info.get("negative_percentage", 0)
    rev_count = issue_info.get("review_count", total_reviews)
    dom_emotion = issue_info.get("dominant_emotion", "agitation")
    severity = issue_info.get("severity", "MEDIUM")
    trend = issue_info.get("trend", "N/A")
    severity_reason = issue_info.get("severity_reason", "")

    detection_rationale = {
        "summary": f"Detected recurring customer pain points centered around '{theme}'.",
        "review_volume": f"{rev_count} matching customer reviews grouped by semantic clustering.",
        "sentiment_signal": f"{neg_pct}% of related customer reviews expressed negative sentiment.",
        "emotional_resonance": f"Predominant customer emotion is '{dom_emotion}', driving user friction.",
        "severity_level": f"{severity} severity assigned based on: {severity_reason}",
        "trend_trajectory": f"Temporal trend is {trend}." if trend != "N/A" else "Temporal trend data unavailable (no dates in dataset)."
    }

    return {
        "issue_id": issue_info.get("id"),
        "theme": theme,
        "severity": severity,
        "severity_score": issue_info.get("severity_score"),
        "negative_percentage": neg_pct,
        "dominant_emotion": dom_emotion,
        "trend": trend,
        "detection_rationale": detection_rationale,
        "evidence_count": len(evidence_reviews),
        "total_related_reviews": total_reviews,
        "evidence_reviews": [
            {
                "id": r.get("id"),
                "original_id": r.get("original_id"),
                "text": r.get("raw_text") or r.get("cleaned_text"),
                "cleaned_text": r.get("cleaned_text"),
                "sentiment": r.get("sentiment"),
                "sentiment_score": r.get("sentiment_score"),
                "emotion": r.get("emotion"),
                "emotion_score": r.get("emotion_score"),
                "rating": r.get("rating"),
                "date": r.get("review_date"),
                "platform": r.get("platform"),
                "app_version": r.get("app_version"),
            }
            for r in evidence_reviews
        ]
    }
