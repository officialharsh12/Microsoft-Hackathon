"""
Intelligence API — Combined RL + LLM insight endpoints for the dashboard.

Provides:
  - GET /api/intelligence/{issue_id} — Full AI insight for a single issue
  - GET /api/intelligence/dashboard/{dataset_id} — Top insights for dashboard cards
  - POST /api/intelligence/feedback — RL feedback endpoint for PM actions
"""

import json
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.database import get_db_connection
from app.services.rl_engine import get_rl_recommendation, update_from_feedback, ACTION_LABELS
from app.services.llm_reasoning import get_or_create_insight

router = APIRouter(prefix="/intelligence", tags=["Intelligence"])


class FeedbackRequest(BaseModel):
    issue_id: int
    dataset_id: int
    action_taken: str
    reward: float  # +1.0 improved, -1.0 worsened, 0 no change


@router.get("/{issue_id}")
async def get_issue_intelligence(issue_id: int, force_refresh: bool = Query(False)):
    """
    Get the full AI intelligence report for a single issue.
    Combines:
      1. RL recommendation (what action to take)
      2. LLM reasoning (executive summary, root cause, why it matters)
      3. Evidence traceability (review IDs supporting the insight)
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch the issue
    cursor.execute("SELECT * FROM issues WHERE id = ?", (issue_id,))
    issue_row = cursor.fetchone()
    if not issue_row:
        conn.close()
        raise HTTPException(status_code=404, detail="Issue not found")
    issue = dict(issue_row)
    issue["is_emerging"] = bool(issue.get("is_emerging"))

    # Fetch evidence reviews
    cursor.execute(
        """SELECT id, original_id, raw_text, cleaned_text, review_date, rating, platform,
                  app_version, sentiment, sentiment_score, emotion, emotion_score
           FROM reviews WHERE dataset_id = ? AND cluster_id = ?
           ORDER BY sentiment_score DESC LIMIT 15""",
        (issue["dataset_id"], issue["cluster_id"]),
    )
    evidence = [dict(r) for r in cursor.fetchall()]

    # Get total reviews for RL state encoding
    cursor.execute("SELECT COUNT(*) as cnt FROM reviews WHERE dataset_id = ?", (issue["dataset_id"],))
    total_row = cursor.fetchone()
    total_reviews = total_row["cnt"] if total_row else 100

    conn.close()

    # Format evidence for LLM (using field names it expects)
    formatted_evidence = [
        {
            "id": r["id"],
            "review_id": r["id"],
            "text": r.get("raw_text") or r.get("cleaned_text", ""),
            "cleaned_text": r.get("cleaned_text", ""),
            "sentiment": r.get("sentiment"),
            "emotion": r.get("emotion"),
            "rating": r.get("rating"),
            "date": r.get("review_date"),
        }
        for r in evidence
    ]

    # 1. Get RL recommendation
    rl_result = get_rl_recommendation(issue, total_reviews)

    # 2. Get LLM insight (with RL context)
    llm_result = get_or_create_insight(
        issue_id=issue_id,
        issue=issue,
        evidence_reviews=formatted_evidence,
        rl_recommendation=rl_result,
        total_reviews=total_reviews,
        force_refresh=force_refresh,
    )

    # 3. Combine into unified response
    return {
        "issue_id": issue_id,
        "theme": issue.get("theme", ""),
        "severity": issue.get("severity", ""),
        "severity_score": issue.get("severity_score", 0),

        # LLM insights
        "executive_summary": llm_result.get("executive_summary", ""),
        "root_cause_hypothesis": llm_result.get("root_cause_hypothesis", ""),
        "recommended_action": llm_result.get("recommended_action", ""),
        "why_it_matters": llm_result.get("why_it_matters", ""),
        "priority_score": llm_result.get("priority_score", 0.5),
        "key_insights": llm_result.get("key_insights", []),
        "llm_confidence": llm_result.get("confidence", "grounded"),
        "llm_model": llm_result.get("model_name", "rule-based"),

        # RL recommendation
        "rl_recommendation": {
            "action": rl_result["recommended_action"],
            "label": rl_result["action_label"],
            "description": rl_result["action_description"],
            "confidence": rl_result["confidence"],
            "reasoning": rl_result["reasoning"],
            "all_scores": rl_result["all_action_scores"],
            "state": rl_result["state_dimensions"],
        },

        # Evidence traceability
        "evidence_review_ids": llm_result.get("evidence_review_ids", []),
        "evidence_count": len(evidence),

        # Source metadata
        "source": llm_result.get("source", "rule-based"),
    }


@router.get("/dashboard/{dataset_id}")
async def get_dashboard_intelligence(dataset_id: int):
    """
    Get AI intelligence summaries for all issues in a dataset.
    Returns the top insights for dashboard cards.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Verify dataset exists
    cursor.execute("SELECT id FROM datasets WHERE id = ?", (dataset_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Dataset not found")

    # Get all issues sorted by severity
    cursor.execute(
        "SELECT * FROM issues WHERE dataset_id = ? ORDER BY severity_score DESC LIMIT 10",
        (dataset_id,),
    )
    issue_rows = cursor.fetchall()

    # Get total reviews
    cursor.execute("SELECT COUNT(*) as cnt FROM reviews WHERE dataset_id = ?", (dataset_id,))
    total_row = cursor.fetchone()
    total_reviews = total_row["cnt"] if total_row else 100

    conn.close()

    insights = []
    for issue_row in issue_rows:
        issue = dict(issue_row)
        issue["is_emerging"] = bool(issue.get("is_emerging"))

        # Get RL recommendation
        rl_result = get_rl_recommendation(issue, total_reviews)

        # Get cached or generate LLM insight
        conn2 = get_db_connection()
        cursor2 = conn2.cursor()
        cursor2.execute(
            """SELECT id, original_id, cleaned_text, sentiment, emotion, rating, review_date
               FROM reviews WHERE dataset_id = ? AND cluster_id = ?
               ORDER BY sentiment_score DESC LIMIT 5""",
            (issue["dataset_id"], issue["cluster_id"]),
        )
        evidence = [
            {
                "id": r["id"],
                "text": r["cleaned_text"],
                "cleaned_text": r["cleaned_text"],
                "sentiment": r["sentiment"],
                "emotion": r["emotion"],
                "rating": r["rating"],
                "date": r["review_date"],
            }
            for r in cursor2.fetchall()
        ]
        conn2.close()

        llm_result = get_or_create_insight(
            issue_id=issue["id"],
            issue=issue,
            evidence_reviews=evidence,
            rl_recommendation=rl_result,
            total_reviews=total_reviews,
        )

        insights.append({
            "issue_id": issue["id"],
            "theme": issue.get("theme", ""),
            "severity": issue.get("severity", ""),
            "severity_score": issue.get("severity_score", 0),
            "is_emerging": issue.get("is_emerging", False),
            "review_count": issue.get("review_count", 0),
            "executive_summary": llm_result.get("executive_summary", ""),
            "recommended_action": llm_result.get("recommended_action", ""),
            "why_it_matters": llm_result.get("why_it_matters", ""),
            "priority_score": llm_result.get("priority_score", 0.5),
            "rl_action": rl_result["action_label"],
            "rl_confidence": rl_result["confidence"],
        })

    return {
        "dataset_id": dataset_id,
        "total_issues": len(insights),
        "insights": insights,
    }


@router.post("/feedback")
async def submit_rl_feedback(body: FeedbackRequest):
    """
    Submit feedback on an action taken for an issue.
    This updates the RL agent's Q-values so it learns which actions
    are effective for different issue states.

    Reward values:
      +1.0 → Issue improved after the action
      -1.0 → Issue worsened after the action
       0.0 → No observable change
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM issues WHERE id = ?", (body.issue_id,))
    issue_row = cursor.fetchone()
    if not issue_row:
        conn.close()
        raise HTTPException(status_code=404, detail="Issue not found")

    issue = dict(issue_row)
    issue["is_emerging"] = bool(issue.get("is_emerging"))

    cursor.execute("SELECT COUNT(*) as cnt FROM reviews WHERE dataset_id = ?", (body.dataset_id,))
    total_row = cursor.fetchone()
    total_reviews = total_row["cnt"] if total_row else 100

    conn.close()

    update_from_feedback(
        issue_id=body.issue_id,
        dataset_id=body.dataset_id,
        action_taken=body.action_taken,
        reward=body.reward,
        current_state=issue,
        total_reviews=total_reviews,
    )

    return {
        "status": "feedback_recorded",
        "issue_id": body.issue_id,
        "action": body.action_taken,
        "reward": body.reward,
        "message": f"RL agent updated. Action '{ACTION_LABELS.get(body.action_taken, body.action_taken)}' received reward {body.reward:+.1f}.",
    }
