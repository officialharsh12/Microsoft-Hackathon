from typing import Dict, Any, List, Optional

# Keywords that indicate severe real-world product friction or financial/data loss
HIGH_IMPACT_KEYWORDS = {
    "crash", "crashes", "freeze", "freezes", "black screen", "unusable",
    "payment", "charged", "billing", "refund", "money", "deducted", "stolen",
    "locked out", "login failed", "lost data", "security", "exploit", "hack",
    "cannot open", "wont open", "brick"
}

# Emotion risk weights
EMOTION_WEIGHTS = {
    "anger": 1.0,
    "annoyance": 0.8,
    "disappointment": 0.75,
    "disapproval": 0.7,
    "fear": 0.9,
    "sadness": 0.6,
    "confusion": 0.5,
    "neutral": 0.3,
    "joy": 0.05,
    "admiration": 0.05,
    "gratitude": 0.05,
    "love": 0.05,
}

def calculate_severity(
    review_count: int,
    total_dataset_reviews: int,
    negative_percentage: float,
    dominant_emotion: str,
    avg_rating: Optional[float] = None,
    representative_texts: Optional[List[str]] = None,
    trend_percentage: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Calculates an explainable severity level and score based on:
    1. Negative sentiment ratio (0.0 to 1.0) - weight: 0.35
    2. Emotion risk weight (0.0 to 1.0) - weight: 0.20
    3. Issue frequency / volume ratio - weight: 0.15
    4. Average star rating if available - weight: 0.15
    5. High-impact keyword triggers (crash/payment/data loss) - weight: 0.15
    + Trend bonus for rapidly rising issues.
    """
    reasons = []

    # 1. Negative Sentiment Signal (weight: 0.35)
    neg_ratio = max(0.0, min(1.0, negative_percentage / 100.0))
    neg_score = neg_ratio * 0.35
    if negative_percentage >= 75:
        reasons.append(f"Heavily negative feedback ({negative_percentage:.0f}% negative)")
    elif negative_percentage >= 50:
        reasons.append(f"Majority negative feedback ({negative_percentage:.0f}% negative)")

    # 2. Emotion Risk (weight: 0.20)
    emotion_risk = EMOTION_WEIGHTS.get(dominant_emotion.lower(), 0.4)
    emotion_score = emotion_risk * 0.20
    if emotion_risk >= 0.75:
        reasons.append(f"High customer agitation (dominant emotion: '{dominant_emotion}')")

    # 3. Frequency Signal (weight: 0.15)
    freq_ratio = (review_count / max(1, total_dataset_reviews))
    # Normalized frequency: 20% of dataset is already high volume
    norm_freq = min(1.0, freq_ratio * 5.0)
    freq_score = norm_freq * 0.15
    if freq_ratio >= 0.15:
        reasons.append(f"High volume impact ({review_count} reviews, {freq_ratio*100:.1f}% of total)")

    # 4. Rating Signal (weight: 0.15)
    if avg_rating is not None and avg_rating > 0:
        # Rating 1.0 -> 1.0 score, Rating 5.0 -> 0.0 score
        rating_risk = max(0.0, min(1.0, (5.0 - avg_rating) / 4.0))
        rating_score = rating_risk * 0.15
        if avg_rating <= 2.0:
            reasons.append(f"Very low average rating ({avg_rating:.1f}/5.0)")
    else:
        # If no rating, distribute evenly to sentiment and emotion
        rating_score = (neg_ratio * 0.08) + (emotion_risk * 0.07)

    # 5. High-Impact Keyword Presence (weight: 0.15)
    keyword_hits = set()
    if representative_texts:
        combined_text = " ".join(representative_texts).lower()
        for kw in HIGH_IMPACT_KEYWORDS:
            if kw in combined_text:
                keyword_hits.add(kw)
    
    keyword_score = min(1.0, len(keyword_hits) * 0.5) * 0.15
    if keyword_hits:
        sample_hits = list(keyword_hits)[:3]
        reasons.append(f"Affects critical workflows: {', '.join(sample_hits)}")

    # 6. Trend multiplier/bonus for rising spikes (+0.05 to +0.10)
    trend_bonus = 0.0
    if trend_percentage is not None and trend_percentage > 25.0:
        trend_bonus = min(0.10, (trend_percentage / 100.0) * 0.08)
        reasons.append(f"Rapidly escalating issue (+{trend_percentage:.0f}% growth)")

    total_score = min(1.0, neg_score + emotion_score + freq_score + rating_score + keyword_score + trend_bonus)
    total_score = round(total_score, 3)

    # Determine Severity Level
    if total_score >= 0.72:
        level = "CRITICAL"
    elif total_score >= 0.52:
        level = "HIGH"
    elif total_score >= 0.32:
        level = "MEDIUM"
    else:
        level = "LOW"

    if not reasons:
        reasons.append("Standard issue frequency and sentiment baseline")

    reason_text = ". ".join(reasons) + "."

    return {
        "severity": level,
        "severity_score": total_score,
        "reason": reason_text
    }
