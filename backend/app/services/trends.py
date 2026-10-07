from typing import List, Dict, Any, Optional
from collections import Counter
import pandas as pd

def calculate_issue_trend(
    cluster_reviews: List[Dict[str, Any]],
    all_dataset_dates: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Calculates issue frequency over time and growth metric.
    Never invents trends if date information does not exist.
    """
    # Filter valid dates
    dates = [r["review_date"] for r in cluster_reviews if r.get("review_date")]

    if not dates:
        return {
            "trend": "N/A",
            "trend_direction": "unavailable",
            "trend_percentage": None,
            "reason": "Trend unavailable — no date information provided.",
            "timeline": []
        }

    # Aggregate daily counts
    date_counts = Counter(dates)
    sorted_dates = sorted(date_counts.keys())

    if len(sorted_dates) == 1:
        # Single date only
        return {
            "trend": "0%",
            "trend_direction": "stable",
            "trend_percentage": 0.0,
            "reason": f"Observed on single date ({sorted_dates[0]})",
            "timeline": [{"date": sorted_dates[0], "count": date_counts[sorted_dates[0]]}]
        }

    # Build continuous timeline
    timeline = [{"date": d, "count": date_counts[d]} for d in sorted_dates]

    # Parse dates to timestamps to find actual calendar time window
    try:
        dt_series = pd.to_datetime(sorted_dates)
        min_dt = dt_series.min()
        max_dt = dt_series.max()
        time_span = (max_dt - min_dt).total_seconds()

        if time_span == 0:
            # All reviews occurred on the exact same date
            return {
                "trend": "0%",
                "trend_direction": "stable",
                "trend_percentage": 0.0,
                "reason": f"Observed on single date ({sorted_dates[0]})",
                "timeline": [{"date": d, "count": date_counts[d]} for d in sorted_dates]
            }

        cutoff_dt = min_dt + (max_dt - min_dt) / 2

        baseline_count = sum(date_counts[d] for d in sorted_dates if pd.to_datetime(d) < cutoff_dt)
        recent_count = sum(date_counts[d] for d in sorted_dates if pd.to_datetime(d) >= cutoff_dt)

        if baseline_count == 0 and recent_count > 0:
            pct_change = 100.0
        elif baseline_count == 0 and recent_count == 0:
            pct_change = 0.0
        else:
            pct_change = round(((recent_count - baseline_count) / baseline_count) * 100, 1)

    except Exception:
        # Fallback to list partition
        midpoint = len(sorted_dates) // 2
        first_half_dates = set(sorted_dates[:midpoint])
        second_half_dates = set(sorted_dates[midpoint:])
        baseline_count = sum(date_counts[d] for d in first_half_dates)
        recent_count = sum(date_counts[d] for d in second_half_dates)
        pct_change = round(((recent_count - baseline_count) / max(1, baseline_count)) * 100, 1)

    # Check for sudden spike
    is_spike = (recent_count >= 2.0 * max(1, baseline_count)) and (recent_count >= 3)

    if is_spike:
        direction = "spike"
        formatted_trend = f"+{pct_change:.0f}% (Spike)" if pct_change > 0 else f"{pct_change:.0f}%"
        reason = f"Sudden surge in recent days ({recent_count} vs {baseline_count} prior)"
    elif pct_change >= 15.0:
        direction = "increasing"
        formatted_trend = f"+{pct_change:.0f}%"
        reason = f"Increasing volume (+{pct_change:.0f}% compared to earlier period)"
    elif pct_change <= -15.0:
        direction = "decreasing"
        formatted_trend = f"{pct_change:.0f}%"
        reason = f"Declining volume ({pct_change:.0f}% compared to earlier period)"
    else:
        direction = "stable"
        formatted_trend = f"{pct_change:+.0f}%" if pct_change != 0 else "0%"
        reason = "Volume has remained relatively stable"

    return {
        "trend": formatted_trend,
        "trend_direction": direction,
        "trend_percentage": pct_change,
        "reason": reason,
        "timeline": timeline
    }
