"""
Reinforcement Learning Recommendation Engine — Q-Learning / Contextual Bandit.

This module implements a lightweight, explainable RL-based recommendation system
that learns which product actions (prioritize, monitor, investigate, fix) should
receive higher priority for a given issue state.

Architecture:
  - State: encoded from issue severity, sentiment distribution, review volume,
           trend velocity, affected version, customer impact
  - Actions: prioritize_issue, monitor_issue, investigate_issue, fix_issue
  - Reward: +1 when issue improves after action, -1 when it worsens
  - Policy: ε-greedy Q-learning with tabular Q-table stored in SQLite

The module is designed to be modular and replaceable with a more sophisticated
RL algorithm (e.g., deep Q-network, policy gradient) later.
"""

import json
import math
import random
from typing import Any, Dict, List, Optional, Tuple

from app.database import get_db_connection

# ── Action space ─────────────────────────────────────────────────────────────
ACTIONS = [
    "prioritize_issue",    # Escalate to top of sprint backlog
    "monitor_issue",       # Watch for changes, no immediate action
    "investigate_issue",   # Assign engineering triage / root-cause analysis
    "fix_issue",           # Recommend immediate fix / hotfix
]

ACTION_LABELS = {
    "prioritize_issue": "Prioritize This Issue",
    "monitor_issue": "Continue Monitoring",
    "investigate_issue": "Investigate Root Cause",
    "fix_issue": "Recommend Immediate Fix",
}

ACTION_DESCRIPTIONS = {
    "prioritize_issue": "Escalate to the top of the product backlog for next sprint planning.",
    "monitor_issue": "Keep watching the trend trajectory. No immediate engineering action required yet.",
    "investigate_issue": "Assign engineering triage to perform root-cause analysis before committing resources.",
    "fix_issue": "This issue has high customer impact. Recommend deploying a targeted hotfix or patch.",
}

# ── Hyperparameters ──────────────────────────────────────────────────────────
LEARNING_RATE = 0.1       # α — step size for Q-value updates
DISCOUNT_FACTOR = 0.95    # γ — how much future rewards matter
EPSILON = 0.15            # ε — exploration probability (15% random)
INITIAL_Q_VALUE = 0.0     # Start all Q-values at zero (no bias)


# ── State encoding ───────────────────────────────────────────────────────────

def _discretize_severity(severity_score: float) -> str:
    """Bin severity score into discrete levels for Q-table lookup."""
    if severity_score >= 0.72:
        return "critical"
    elif severity_score >= 0.52:
        return "high"
    elif severity_score >= 0.32:
        return "medium"
    return "low"


def _discretize_sentiment(negative_pct: float) -> str:
    """Bin negative sentiment percentage into categories."""
    if negative_pct >= 75:
        return "very_negative"
    elif negative_pct >= 50:
        return "negative"
    elif negative_pct >= 25:
        return "mixed"
    return "mostly_positive"


def _discretize_volume(review_count: int, total_reviews: int) -> str:
    """Bin review volume relative to dataset size."""
    ratio = review_count / max(1, total_reviews)
    if ratio >= 0.20:
        return "very_high"
    elif ratio >= 0.10:
        return "high"
    elif ratio >= 0.05:
        return "moderate"
    return "low"


def _discretize_trend(trend_direction: str, trend_pct: Optional[float]) -> str:
    """Bin trend velocity into discrete levels."""
    if trend_direction in ("spike",):
        return "spike"
    if trend_pct is not None and trend_pct >= 30:
        return "rapid_increase"
    if trend_direction == "increasing":
        return "increasing"
    if trend_direction == "decreasing":
        return "decreasing"
    return "stable"


def encode_state(issue: Dict[str, Any], total_reviews: int = 100) -> str:
    """
    Encode an issue into a discrete state key for Q-table lookup.

    State dimensions:
      - severity level (critical/high/medium/low)
      - sentiment bucket (very_negative/negative/mixed/mostly_positive)
      - volume bucket (very_high/high/moderate/low)
      - trend bucket (spike/rapid_increase/increasing/stable/decreasing)
      - is_emerging (true/false)

    Returns a pipe-delimited string like: "high|negative|moderate|increasing|false"
    """
    severity = _discretize_severity(issue.get("severity_score", 0.5))
    sentiment = _discretize_sentiment(issue.get("negative_percentage", 50.0))
    volume = _discretize_volume(issue.get("review_count", 10), total_reviews)
    trend = _discretize_trend(
        issue.get("trend_direction", "stable"),
        issue.get("trend_percentage"),
    )
    emerging = "true" if issue.get("is_emerging") else "false"
    return f"{severity}|{sentiment}|{volume}|{trend}|{emerging}"


# ── Q-Table operations (SQLite-backed) ───────────────────────────────────────

def _get_q_values(state_key: str) -> Dict[str, float]:
    """Retrieve Q-values for all actions in a given state from the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT action, q_value FROM rl_q_table WHERE state_key = ?",
        (state_key,),
    )
    rows = cursor.fetchall()
    conn.close()

    q_values = {action: INITIAL_Q_VALUE for action in ACTIONS}
    for row in rows:
        q_values[row["action"]] = row["q_value"]
    return q_values


def _update_q_value(state_key: str, action: str, new_q: float):
    """Update or insert a Q-value in the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO rl_q_table (state_key, action, q_value, visit_count, updated_at)
           VALUES (?, ?, ?, 1, CURRENT_TIMESTAMP)
           ON CONFLICT(state_key, action)
           DO UPDATE SET q_value = ?, visit_count = visit_count + 1, updated_at = CURRENT_TIMESTAMP""",
        (state_key, action, new_q, new_q),
    )
    conn.commit()
    conn.close()


# ── Policy: ε-greedy action selection ────────────────────────────────────────

def _apply_heuristic_bonus(q_values: Dict[str, float], issue: Dict[str, Any]) -> Dict[str, float]:
    """
    Add a domain-knowledge heuristic bonus to cold-start Q-values.
    This gives the RL agent reasonable initial behavior before it has enough
    feedback data to learn purely from rewards.

    The bonus decays as visit_count increases (the agent learns from data).
    """
    severity_score = issue.get("severity_score", 0.5)
    neg_pct = issue.get("negative_percentage", 50.0)
    is_emerging = issue.get("is_emerging", False)
    trend_dir = issue.get("trend_direction", "stable")

    # Get visit counts to decay heuristic influence
    conn = get_db_connection()
    cursor = conn.cursor()
    state_key = encode_state(issue)
    cursor.execute(
        "SELECT SUM(visit_count) as total FROM rl_q_table WHERE state_key = ?",
        (state_key,),
    )
    row = cursor.fetchone()
    conn.close()
    total_visits = row["total"] if row and row["total"] else 0

    # Decay factor: heuristic influence decreases as data accumulates
    decay = 1.0 / (1.0 + total_visits * 0.1)

    bonuses = {a: 0.0 for a in ACTIONS}

    # Critical/high severity → lean toward fix or prioritize
    if severity_score >= 0.72:
        bonuses["fix_issue"] += 0.5 * decay
        bonuses["prioritize_issue"] += 0.3 * decay
    elif severity_score >= 0.52:
        bonuses["prioritize_issue"] += 0.4 * decay
        bonuses["investigate_issue"] += 0.3 * decay

    # Very negative sentiment → investigate or fix
    if neg_pct >= 75:
        bonuses["fix_issue"] += 0.3 * decay
        bonuses["investigate_issue"] += 0.2 * decay

    # Emerging issues → prioritize immediately
    if is_emerging:
        bonuses["prioritize_issue"] += 0.5 * decay
        bonuses["fix_issue"] += 0.3 * decay

    # Rapidly increasing trend → investigate
    if trend_dir in ("spike", "increasing"):
        bonuses["investigate_issue"] += 0.3 * decay

    # Low severity → monitor
    if severity_score < 0.32:
        bonuses["monitor_issue"] += 0.4 * decay

    return {a: q_values[a] + bonuses[a] for a in ACTIONS}


def select_action(state_key: str, issue: Dict[str, Any], explore: bool = True) -> Tuple[str, Dict[str, float]]:
    """
    Select the best action using ε-greedy policy with heuristic bonuses.

    Args:
        state_key: The encoded state string
        issue: The raw issue dict (for heuristic bonuses)
        explore: Whether to allow random exploration (set False for inference)

    Returns:
        (selected_action, action_scores) — the chosen action and all scores
    """
    q_values = _get_q_values(state_key)
    adjusted_scores = _apply_heuristic_bonus(q_values, issue)

    if explore and random.random() < EPSILON:
        # Exploration: pick a random action
        action = random.choice(ACTIONS)
    else:
        # Exploitation: pick the action with highest adjusted Q-value
        action = max(adjusted_scores, key=adjusted_scores.get)

    return action, adjusted_scores


# ── Learning: Q-value update from feedback ───────────────────────────────────

def update_from_feedback(
    issue_id: int,
    dataset_id: int,
    action_taken: str,
    reward: float,
    current_state: Dict[str, Any],
    total_reviews: int = 100,
):
    """
    Update Q-values based on outcome feedback.

    The reward signal:
      +1.0 → issue improved after action (severity decreased, neg_pct dropped)
      -1.0 → issue worsened (severity increased, more complaints)
       0.0 → no change

    This implements the standard Q-learning update rule:
      Q(s, a) ← Q(s, a) + α * [r + γ * max_a' Q(s', a') - Q(s, a)]

    Since we don't have a clear "next state" in this batch setting,
    we simplify to:
      Q(s, a) ← Q(s, a) + α * [r - Q(s, a)]
    """
    state_key = encode_state(current_state, total_reviews)
    q_values = _get_q_values(state_key)
    old_q = q_values.get(action_taken, INITIAL_Q_VALUE)

    # Simplified Q-learning update (no next-state in this batch setting)
    new_q = old_q + LEARNING_RATE * (reward - old_q)
    _update_q_value(state_key, action_taken, new_q)

    # Store feedback for audit trail
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO rl_feedback (issue_id, dataset_id, action_taken, reward, state_snapshot)
           VALUES (?, ?, ?, ?, ?)""",
        (issue_id, dataset_id, action_taken, reward, json.dumps(current_state)),
    )
    conn.commit()
    conn.close()


# ── Public API: get recommendation for an issue ─────────────────────────────

def get_rl_recommendation(issue: Dict[str, Any], total_reviews: int = 100) -> Dict[str, Any]:
    """
    Generate an RL-based action recommendation for a given issue.

    Returns a structured recommendation with:
      - recommended_action: the best action code
      - action_label: human-readable action name
      - action_description: what this action means
      - confidence: normalized score (0-1) based on Q-value magnitude
      - all_action_scores: transparency into all action Q-values
      - state_representation: the discretized state used
      - reasoning: explainable text about why this action was chosen
    """
    state_key = encode_state(issue, total_reviews)
    best_action, scores = select_action(state_key, issue, explore=False)

    # Calculate confidence as a softmax-like normalization
    max_score = max(scores.values())
    min_score = min(scores.values())
    score_range = max_score - min_score
    confidence = min(1.0, max(0.1, 0.5 + score_range * 2.0)) if score_range > 0 else 0.5

    # Build explainable reasoning
    reasoning_parts = []
    severity = issue.get("severity", "MEDIUM")
    neg_pct = issue.get("negative_percentage", 50.0)
    trend_dir = issue.get("trend_direction", "stable")
    is_emerging = issue.get("is_emerging", False)

    if is_emerging:
        reasoning_parts.append("This is an emerging issue with rapidly growing impact")
    if severity in ("CRITICAL", "HIGH"):
        reasoning_parts.append(f"severity is {severity}")
    if neg_pct >= 60:
        reasoning_parts.append(f"{neg_pct:.0f}% of reviews are negative")
    if trend_dir in ("spike", "increasing"):
        reasoning_parts.append(f"trend is {trend_dir}")

    if not reasoning_parts:
        reasoning_parts.append("Issue metrics are within normal parameters")

    reasoning = ". ".join(reasoning_parts) + f". The RL agent recommends: {ACTION_LABELS[best_action]}."

    # Action scores sorted by value for transparency
    sorted_scores = sorted(
        [
            {"action": a, "label": ACTION_LABELS[a], "score": round(s, 4)}
            for a, s in scores.items()
        ],
        key=lambda x: x["score"],
        reverse=True,
    )

    return {
        "recommended_action": best_action,
        "action_label": ACTION_LABELS[best_action],
        "action_description": ACTION_DESCRIPTIONS[best_action],
        "confidence": round(confidence, 3),
        "all_action_scores": sorted_scores,
        "state_representation": state_key,
        "state_dimensions": {
            "severity": _discretize_severity(issue.get("severity_score", 0.5)),
            "sentiment": _discretize_sentiment(issue.get("negative_percentage", 50.0)),
            "volume": _discretize_volume(issue.get("review_count", 10), total_reviews),
            "trend": _discretize_trend(trend_dir, issue.get("trend_percentage")),
            "is_emerging": str(is_emerging).lower(),
        },
        "reasoning": reasoning,
    }
