import json
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from app.database import get_db_connection
from app.schemas.issue import IssueItem, IssueEvidenceResponse
from app.services.evidence import build_evidence_chain
from app.services.trends import calculate_issue_trend
from app.services.pm_brief import generate_pm_brief

router = APIRouter(prefix="/issues", tags=["Issues"])

@router.get("", response_model=List[IssueItem])
async def get_issues(
    dataset_id: Optional[int] = Query(None),
    severity: Optional[str] = Query(None),
    is_emerging: Optional[bool] = Query(None)
):
    """
    Retrieves aggregated product issues ordered by urgency:
    Emerging radar issues first, followed by Critical/High severity.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # If dataset_id not specified, find latest completed dataset
    if dataset_id is None:
        cursor.execute("SELECT id FROM datasets WHERE status = 'completed' ORDER BY id DESC LIMIT 1")
        row = cursor.fetchone()
        if row:
            dataset_id = row["id"]
        else:
            conn.close()
            return []

    query = "SELECT * FROM issues WHERE dataset_id = ?"
    params = [dataset_id]

    if severity is not None:
        query += " AND UPPER(severity) = UPPER(?)"
        params.append(severity)
    if is_emerging is not None:
        query += " AND is_emerging = ?"
        params.append(1 if is_emerging else 0)

    query += " ORDER BY is_emerging DESC, severity_score DESC, review_count DESC"
    cursor.execute(query, params)
    rows = cursor.fetchall()

    results = []
    for r in rows:
        item = dict(r)
        item["is_emerging"] = bool(item["is_emerging"])
        item["sample_quotes"] = json.loads(item["sample_quotes"]) if item.get("sample_quotes") else []
        results.append(item)

    conn.close()
    return results

@router.get("/{issue_id}", response_model=IssueItem)
async def get_issue_by_id(issue_id: int):
    """Retrieves issue details by ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM issues WHERE id = ?", (issue_id,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Issue not found")

    issue = dict(row)
    issue["is_emerging"] = bool(issue["is_emerging"])
    issue["sample_quotes"] = json.loads(issue["sample_quotes"]) if issue.get("sample_quotes") else []

    # Retrieve reviews to attach timeline
    cursor.execute(
        "SELECT review_date FROM reviews WHERE dataset_id = ? AND cluster_id = ?",
        (issue["dataset_id"], issue["cluster_id"])
    )
    rev_rows = cursor.fetchall()
    conn.close()

    trend_calc = calculate_issue_trend([dict(r) for r in rev_rows])
    issue["timeline"] = trend_calc.get("timeline", [])

    return issue

@router.get("/{issue_id}/evidence", response_model=IssueEvidenceResponse)
async def get_issue_evidence(issue_id: int, limit: int = Query(15, ge=1, le=100)):
    """
    Returns authentic evidence reviews supporting the detected issue,
    along with the explainable diagnostic rationale.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM issues WHERE id = ?", (issue_id,))
    issue_row = cursor.fetchone()
    if not issue_row:
        conn.close()
        raise HTTPException(status_code=404, detail="Issue not found")

    issue = dict(issue_row)

    # Retrieve all reviews belonging to this cluster
    cursor.execute(
        """
        SELECT id, original_id, raw_text, cleaned_text, review_date, rating, platform,
               app_version, sentiment, sentiment_score, emotion, emotion_score
        FROM reviews
        WHERE dataset_id = ? AND cluster_id = ?
        """,
        (issue["dataset_id"], issue["cluster_id"])
    )
    rev_rows = cursor.fetchall()
    cluster_reviews = [dict(r) for r in rev_rows]
    conn.close()

    evidence_result = build_evidence_chain(issue, cluster_reviews, limit=limit)
    return evidence_result

@router.get("/{issue_id}/brief")
async def get_issue_pm_brief(issue_id: int):
    """
    Generates an executive PM Brief for the selected issue,
    synthesizing impact signals, customer statements, and technical investigation paths.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    if issue_id == 0:
        cursor.execute("SELECT id FROM datasets WHERE status = 'completed' ORDER BY id DESC LIMIT 1")
        ds_row = cursor.fetchone()
        issue_row = None
        if ds_row:
            cursor.execute("SELECT * FROM issues WHERE dataset_id = ? ORDER BY severity_score DESC LIMIT 1", (ds_row["id"],))
            issue_row = cursor.fetchone()
        if not issue_row:
            cursor.execute("SELECT * FROM issues ORDER BY severity_score DESC LIMIT 1")
            issue_row = cursor.fetchone()
    else:
        cursor.execute("SELECT * FROM issues WHERE id = ?", (issue_id,))
        issue_row = cursor.fetchone()

    if not issue_row:
        conn.close()
        raise HTTPException(status_code=404, detail="No issue found to generate Executive Brief.")

    issue = dict(issue_row)

    cursor.execute(
        """
        SELECT id, original_id, raw_text, cleaned_text, review_date, rating, platform,
               app_version, sentiment, sentiment_score, emotion, emotion_score
        FROM reviews
        WHERE dataset_id = ? AND cluster_id = ?
        ORDER BY sentiment_score DESC
        LIMIT 10
        """,
        (issue["dataset_id"], issue["cluster_id"])
    )
    rev_rows = [dict(r) for r in cursor.fetchall()]
    conn.close()

    brief = generate_pm_brief(issue, rev_rows)
    return brief
