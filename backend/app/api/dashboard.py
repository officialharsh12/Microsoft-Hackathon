import json
from typing import Optional, Dict, Any, List
from collections import Counter
from fastapi import APIRouter, Query, HTTPException
from app.database import get_db_connection
from app.schemas.issue import DashboardStats, IssueItem

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("", response_model=DashboardStats)
async def get_dashboard_metrics(dataset_id: Optional[int] = Query(None)):
    """
    Returns aggregated dashboard metrics, sentiment breakdown, emotion breakdown,
    severity distributions, and emerging issues for the active dataset.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # If no dataset_id, pick the latest completed dataset
    if dataset_id is None:
        cursor.execute("SELECT * FROM datasets WHERE status = 'completed' ORDER BY id DESC LIMIT 1")
        dataset_row = cursor.fetchone()
        if not dataset_row:
            # Check if any dataset exists
            cursor.execute("SELECT * FROM datasets ORDER BY id DESC LIMIT 1")
            dataset_row = cursor.fetchone()
    else:
        cursor.execute("SELECT * FROM datasets WHERE id = ?", (dataset_id,))
        dataset_row = cursor.fetchone()

    if not dataset_row:
        conn.close()
        # Return empty state
        return DashboardStats(
            dataset_id=None,
            dataset_filename=None,
            total_reviews=0,
            positive_percentage=0.0,
            negative_percentage=0.0,
            high_severity_count=0,
            emerging_issues_count=0,
            sentiment_distribution=[],
            emotion_distribution=[],
            severity_distribution=[],
            top_issues=[],
            emerging_issues=[],
            trend_timeline=[]
        )

    ds_id = dataset_row["id"]
    filename = dataset_row["filename"]

    # 1. Fetch reviews metrics
    cursor.execute(
        "SELECT sentiment, emotion, review_date FROM reviews WHERE dataset_id = ?",
        (ds_id,)
    )
    rev_rows = cursor.fetchall()
    total_reviews = len(rev_rows)

    sentiments = [r["sentiment"].upper() for r in rev_rows if r["sentiment"]]
    pos_count = sum(1 for s in sentiments if s == "POSITIVE")
    neg_count = sum(1 for s in sentiments if s == "NEGATIVE")

    pos_pct = round((pos_count / max(1, total_reviews)) * 100, 1)
    neg_pct = round((neg_count / max(1, total_reviews)) * 100, 1)

    sentiment_dist = [
        {"name": "Positive", "count": pos_count, "percentage": pos_pct, "color": "#10b981"},
        {"name": "Negative", "count": neg_count, "percentage": neg_pct, "color": "#ef4444"},
    ]

    # Emotion breakdown
    emotions = [r["emotion"].lower() for r in rev_rows if r["emotion"]]
    emotion_counts = Counter(emotions).most_common(8)
    emotion_dist = [
        {
            "name": emo.title(),
            "count": count,
            "percentage": round((count / max(1, total_reviews)) * 100, 1)
        }
        for emo, count in emotion_counts
    ]

    # Timeline counts
    date_counts = Counter([r["review_date"] for r in rev_rows if r["review_date"]])
    trend_timeline = [
        {"date": d, "count": date_counts[d]}
        for d in sorted(date_counts.keys())
    ]

    # 2. Fetch issues
    cursor.execute("SELECT * FROM issues WHERE dataset_id = ? ORDER BY severity_score DESC", (ds_id,))
    issue_rows = cursor.fetchall()

    issues_list: List[IssueItem] = []
    emerging_list: List[IssueItem] = []
    sev_counter = Counter()

    for r in issue_rows:
        item = dict(r)
        item["is_emerging"] = bool(item["is_emerging"])
        item["sample_quotes"] = json.loads(item["sample_quotes"]) if item.get("sample_quotes") else []
        issue_obj = IssueItem(**item)
        issues_list.append(issue_obj)
        sev_counter[item["severity"]] += 1
        if item["is_emerging"]:
            emerging_list.append(issue_obj)

    high_sev_count = sev_counter.get("CRITICAL", 0) + sev_counter.get("HIGH", 0)

    severity_dist = [
        {"severity": "CRITICAL", "count": sev_counter.get("CRITICAL", 0), "color": "#ef4444"},
        {"severity": "HIGH", "count": sev_counter.get("HIGH", 0), "color": "#f97316"},
        {"severity": "MEDIUM", "count": sev_counter.get("MEDIUM", 0), "color": "#eab308"},
        {"severity": "LOW", "count": sev_counter.get("LOW", 0), "color": "#3b82f6"},
    ]

    conn.close()

    return DashboardStats(
        dataset_id=ds_id,
        dataset_filename=filename,
        total_reviews=total_reviews,
        positive_percentage=pos_pct,
        negative_percentage=neg_pct,
        high_severity_count=high_sev_count,
        emerging_issues_count=len(emerging_list),
        sentiment_distribution=sentiment_dist,
        emotion_distribution=emotion_dist,
        severity_distribution=severity_dist,
        top_issues=issues_list,
        emerging_issues=emerging_list,
        trend_timeline=trend_timeline
    )
