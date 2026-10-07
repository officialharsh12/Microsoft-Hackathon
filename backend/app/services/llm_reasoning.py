"""
LLM Reasoning Layer — Higher-order intelligence for Review Intelligence.

This module sits ON TOP of the existing ML pipeline (sentiment, emotion, clustering,
severity, trends) and uses an LLM for higher-level reasoning:

  Reviews → Sentiment/Emotion Model → Theme/Issue Detection → Severity/Trend
    → LLM Reasoning → Product Recommendation

The LLM does NOT replace the existing ML models. Instead, it synthesizes
structured pipeline outputs into:
  - Executive summary
  - Root-cause hypothesis
  - Recommended product action
  - Why the issue matters
  - Suggested priority
  - Natural-language insights

Every LLM-generated insight is traceable to the underlying review/theme evidence.
No unnecessary PII is sent to the LLM — only aggregated metrics and anonymized quotes.
"""

import json
from typing import Any, Dict, List, Optional

from app.config import settings
from app.database import get_db_connection
from app.services.llm import GroundedLLM


def _anonymize_text(text: str) -> str:
    """Strip potential PII patterns from review text before sending to LLM."""
    import re
    # Remove emails
    text = re.sub(r'[\w.-]+@[\w.-]+\.\w+', '[EMAIL]', text)
    # Remove phone numbers (various formats)
    text = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE]', text)
    # Remove names that look like proper nouns at start (basic heuristic)
    text = re.sub(r'\b(?:Mr|Mrs|Ms|Dr)\.\s+\w+', '[NAME]', text)
    return text


def _build_enhanced_prompt(
    issue: Dict[str, Any],
    metrics: Dict[str, Any],
    evidence: List[Dict[str, Any]],
    rl_recommendation: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Build a comprehensive prompt for the LLM that includes all pipeline signals.
    This is the core of the LLM reasoning layer — it structures the ML pipeline
    outputs into a format the LLM can reason over.
    """
    # Anonymize evidence texts
    evidence_lines = []
    for i, row in enumerate(evidence[:5]):
        text = _anonymize_text(row.get("text") or row.get("cleaned_text") or "")
        sentiment = row.get("sentiment", "unknown")
        emotion = row.get("emotion", "unknown")
        rating = row.get("rating", "N/A")
        evidence_lines.append(
            f"  Review #{i+1} (sentiment: {sentiment}, emotion: {emotion}, rating: {rating}): \"{text[:200]}\""
        )
    evidence_block = "\n".join(evidence_lines) if evidence_lines else "  No evidence available"

    # RL context
    rl_block = ""
    if rl_recommendation:
        rl_block = f"""
RL Agent Recommendation: {rl_recommendation.get('action_label', 'N/A')}
RL Confidence: {rl_recommendation.get('confidence', 'N/A')}
RL Reasoning: {rl_recommendation.get('reasoning', 'N/A')}
"""

    prompt = f"""You are an expert Product Intelligence analyst. Analyze the following structured data from our
automated review intelligence pipeline and provide strategic product insights.

IMPORTANT RULES:
- Base ALL conclusions on the provided data only
- Label hypotheses as "Possible Cause" or "Hypothesis"
- Do not invent statistics or reviews not present in the data
- Keep recommendations actionable and specific

═══ ISSUE DATA ═══
Issue Theme: {issue.get('title') or issue.get('theme', 'Unknown')}
Keywords: {issue.get('keywords', 'N/A')}
Review Count: {metrics.get('review_count', 'N/A')}
Negative Sentiment: {metrics.get('negative_percentage', 'N/A')}%
Dominant Emotion: {metrics.get('dominant_emotion', 'N/A')}
Severity Level: {metrics.get('severity', 'N/A')} (score: {metrics.get('severity_score', 'N/A')})
Severity Rationale: {metrics.get('severity_reason', 'N/A')}

═══ TREND DATA ═══
Trend Direction: {metrics.get('trend_direction', 'stable')}
Trend Velocity: {metrics.get('trend_percentage', 'N/A')}%
Is Emerging: {metrics.get('is_emerging', False)}

═══ EVIDENCE (Anonymized Customer Reviews) ═══
{evidence_block}
{rl_block}
═══ REQUIRED OUTPUT ═══
Return a valid JSON object with exactly these keys:
{{
  "executive_summary": "2-3 sentence strategic summary for a PM or executive",
  "root_cause_hypothesis": "Most likely root cause based on the review patterns",
  "recommended_action": "Specific, actionable product recommendation",
  "why_it_matters": "Business impact explanation — why this should be prioritized",
  "priority_score": <float 0.0-1.0 based on severity, trend, and impact>,
  "key_insights": ["insight 1", "insight 2", "insight 3"],
  "confidence": "high|medium|low"
}}"""
    return prompt


def generate_llm_insight(
    issue: Dict[str, Any],
    evidence_reviews: List[Dict[str, Any]],
    rl_recommendation: Optional[Dict[str, Any]] = None,
    total_reviews: int = 100,
) -> Dict[str, Any]:
    """
    Generate higher-level LLM reasoning insight for an issue.

    This function:
    1. Collects all pipeline signals (severity, sentiment, emotion, trend)
    2. Anonymizes review evidence (removes PII)
    3. Sends structured context to the LLM
    4. Returns traceable, evidence-backed insights

    If no LLM API key is configured, falls back to a deterministic
    rule-based insight generator (same as existing GroundedLLM behavior).
    """
    # Build metrics context from issue data
    metrics = {
        "review_count": issue.get("review_count", 0),
        "negative_percentage": issue.get("negative_percentage", 0.0),
        "dominant_emotion": issue.get("dominant_emotion", "neutral"),
        "severity": issue.get("severity", "MEDIUM"),
        "severity_score": issue.get("severity_score", 0.5),
        "severity_reason": issue.get("severity_reason", ""),
        "trend": issue.get("trend", "N/A"),
        "trend_direction": issue.get("trend_direction", "stable"),
        "trend_percentage": issue.get("trend_percentage"),
        "is_emerging": issue.get("is_emerging", False),
    }

    # Extract evidence review IDs for traceability
    evidence_ids = [
        r.get("id") or r.get("review_id")
        for r in evidence_reviews[:10]
        if r.get("id") is not None or r.get("review_id") is not None
    ]

    # Try LLM provider first
    llm = GroundedLLM()
    if llm.should_use_provider():
        try:
            prompt = _build_enhanced_prompt(issue, metrics, evidence_reviews, rl_recommendation)
            # Use the existing LLM infrastructure
            import requests
            payload = {
                "model": llm.model,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are an expert Product Intelligence analyst. Return only valid JSON.",
                    },
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.2,
            }
            headers = {
                "Content-Type": "application/json",
                "api-key": llm.api_key,
            }
            response = requests.post(
                llm.endpoint, headers=headers, json=payload, timeout=30
            )
            response.raise_for_status()
            body = response.json()
            content = body.get("choices", [{}])[0].get("message", {}).get("content", "")
            try:
                parsed = json.loads(content)
            except Exception:
                # Try to extract JSON from markdown code block
                import re
                json_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', content)
                if json_match:
                    parsed = json.loads(json_match.group(1))
                else:
                    parsed = {"executive_summary": content.strip()}

            # Ensure all required keys exist
            result = {
                "executive_summary": parsed.get("executive_summary", ""),
                "root_cause_hypothesis": parsed.get("root_cause_hypothesis", ""),
                "recommended_action": parsed.get("recommended_action", ""),
                "why_it_matters": parsed.get("why_it_matters", ""),
                "priority_score": float(parsed.get("priority_score", metrics["severity_score"])),
                "key_insights": parsed.get("key_insights", []),
                "confidence": parsed.get("confidence", "medium"),
                "evidence_review_ids": evidence_ids,
                "model_name": llm.model,
                "source": "llm",
            }
            return result

        except Exception as e:
            # Fall through to rule-based fallback
            pass

    # ── Rule-based fallback (deterministic, no LLM needed) ───────────────────
    return _generate_rule_based_insight(issue, metrics, evidence_reviews, evidence_ids, rl_recommendation)


def _generate_rule_based_insight(
    issue: Dict[str, Any],
    metrics: Dict[str, Any],
    evidence_reviews: List[Dict[str, Any]],
    evidence_ids: List[int],
    rl_recommendation: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Generate a deterministic, rule-based insight when no LLM API is available.
    This ensures the system always produces useful output.
    """
    theme = issue.get("title") or issue.get("theme", "Product Issue")
    severity = metrics["severity"]
    severity_score = metrics["severity_score"]
    neg_pct = metrics["negative_percentage"]
    dominant_emotion = metrics["dominant_emotion"]
    review_count = metrics["review_count"]
    trend_dir = metrics["trend_direction"]
    is_emerging = metrics["is_emerging"]

    # Executive summary
    urgency = "🚨 CRITICAL" if severity == "CRITICAL" else ("⚠️ HIGH PRIORITY" if severity == "HIGH" else "📋 MODERATE")
    summary = (
        f"{urgency}: '{theme}' has accumulated {review_count} customer reports with "
        f"{neg_pct:.0f}% negative sentiment. The dominant customer emotion is '{dominant_emotion}'. "
    )
    if is_emerging:
        summary += "This is an emerging issue showing rapid escalation. "
    if trend_dir in ("increasing", "spike"):
        summary += f"The issue trend is {trend_dir}, indicating growing customer impact."
    else:
        summary += f"The issue trend is currently {trend_dir}."

    # Root cause hypothesis (based on keywords and theme)
    theme_lower = theme.lower()
    if any(kw in theme_lower for kw in ["payment", "checkout", "billing", "charge"]):
        root_cause = (
            "Hypothesis: Payment gateway integration issues or transaction timeout handling. "
            "Review patterns suggest intermittent failures during the checkout flow, "
            "possibly related to third-party payment processor reliability."
        )
    elif any(kw in theme_lower for kw in ["crash", "freeze", "startup", "performance"]):
        root_cause = (
            "Hypothesis: Application stability issue — likely a memory leak or unhandled exception "
            "during initialization. Customer reports suggest the issue may be device-specific or "
            "related to recent version updates."
        )
    elif any(kw in theme_lower for kw in ["login", "auth", "password", "otp"]):
        root_cause = (
            "Hypothesis: Authentication flow reliability issues — possibly related to "
            "OTP delivery delays, token refresh failures, or session management. "
            "Multiple customers report being unable to complete the sign-in process."
        )
    else:
        root_cause = (
            f"Hypothesis: The review patterns for '{theme}' suggest a recurring UX friction point. "
            "Root cause requires engineering investigation with telemetry correlation."
        )

    # Recommended action
    if severity in ("CRITICAL",) or is_emerging:
        action = f"Immediate triage required. Assign dedicated engineering team to investigate '{theme}'. Target resolution within current sprint."
    elif severity == "HIGH":
        action = f"Prioritize in next sprint planning. Schedule engineering deep-dive on '{theme}' with customer support cross-reference."
    else:
        action = f"Monitor '{theme}' trend over next 2 weeks. If negative sentiment exceeds 60%, escalate to sprint backlog."

    # Why it matters
    impact_text = f"This issue affects {review_count} customers"
    if neg_pct >= 70:
        impact_text += f" with an overwhelmingly negative reception ({neg_pct:.0f}% negative)"
    elif neg_pct >= 50:
        impact_text += f" with majority negative sentiment ({neg_pct:.0f}% negative)"
    impact_text += (
        f". The dominant emotion is '{dominant_emotion}', indicating "
        f"{'significant customer frustration' if dominant_emotion in ('anger', 'annoyance', 'disappointment') else 'notable customer concern'}. "
        f"Left unaddressed, this could lead to increased churn and negative store ratings."
    )

    # Key insights from evidence
    key_insights = []
    if evidence_reviews:
        negative_count = sum(1 for r in evidence_reviews if r.get("sentiment", "").upper() == "NEGATIVE")
        if negative_count > 0:
            key_insights.append(f"{negative_count} of {len(evidence_reviews)} evidence reviews are negative")

        emotions = [r.get("emotion", "").lower() for r in evidence_reviews if r.get("emotion")]
        if emotions:
            from collections import Counter
            top_emotions = Counter(emotions).most_common(2)
            key_insights.append(f"Top emotions: {', '.join(f'{e} ({c})' for e, c in top_emotions)}")

    if is_emerging:
        key_insights.append("Issue is flagged as EMERGING — showing rapid growth trajectory")
    if trend_dir in ("increasing", "spike"):
        pct = metrics.get("trend_percentage")
        key_insights.append(f"Trend velocity: {trend_dir}" + (f" (+{pct:.0f}%)" if pct else ""))

    if not key_insights:
        key_insights = ["Issue detected through automated theme clustering and severity scoring"]

    priority = severity_score
    if is_emerging:
        priority = min(1.0, priority + 0.15)
    if trend_dir in ("spike",):
        priority = min(1.0, priority + 0.10)

    return {
        "executive_summary": summary,
        "root_cause_hypothesis": root_cause,
        "recommended_action": action,
        "why_it_matters": impact_text,
        "priority_score": round(priority, 3),
        "key_insights": key_insights,
        "confidence": "grounded",
        "evidence_review_ids": evidence_ids,
        "model_name": "rule-based-enhanced-reasoning",
        "source": "rule-based",
    }


def get_or_create_insight(issue_id: int, issue: Dict[str, Any], evidence_reviews: List[Dict[str, Any]],
                          rl_recommendation: Optional[Dict[str, Any]] = None,
                          total_reviews: int = 100,
                          force_refresh: bool = False) -> Dict[str, Any]:
    """
    Get cached LLM insight or generate a new one.
    Caches insights in the llm_insights table for performance.
    """
    dataset_id = issue.get("dataset_id", 0)

    if not force_refresh:
        # Check cache
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM llm_insights WHERE issue_id = ? AND dataset_id = ? ORDER BY created_at DESC LIMIT 1",
            (issue_id, dataset_id),
        )
        row = cursor.fetchone()
        conn.close()

        if row:
            return {
                "executive_summary": row["executive_summary"],
                "root_cause_hypothesis": row["root_cause_hypothesis"],
                "recommended_action": row["recommended_action"],
                "why_it_matters": row["why_it_matters"],
                "priority_score": row["priority_score"],
                "evidence_review_ids": json.loads(row["evidence_review_ids"]) if row["evidence_review_ids"] else [],
                "model_name": row["model_name"],
                "source": "cached",
                "key_insights": [],
                "confidence": "grounded",
            }

    # Generate new insight
    insight = generate_llm_insight(issue, evidence_reviews, rl_recommendation, total_reviews)

    # Cache it
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO llm_insights (issue_id, dataset_id, executive_summary, root_cause_hypothesis,
           recommended_action, why_it_matters, priority_score, evidence_review_ids, model_name)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            issue_id,
            dataset_id,
            insight["executive_summary"],
            insight["root_cause_hypothesis"],
            insight["recommended_action"],
            insight["why_it_matters"],
            insight["priority_score"],
            json.dumps(insight.get("evidence_review_ids", [])),
            insight.get("model_name", "unknown"),
        ),
    )
    conn.commit()
    conn.close()

    return insight
