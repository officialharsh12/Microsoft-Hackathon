from typing import Dict, Any, List

def generate_pm_brief(issue: Dict[str, Any], evidence_reviews: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generates a structured, evidence-grounded PM Brief for an issue.
    All statistics and customer statements come strictly from actual review data.
    """
    theme = issue.get("theme", "Product Area Concern")
    review_count = issue.get("review_count", 0)
    negative_pct = issue.get("negative_percentage", 0.0)
    dominant_emotion = issue.get("dominant_emotion", "annoyance")
    severity = issue.get("severity", "MEDIUM")
    severity_score = issue.get("severity_score", 0.5)
    severity_reason = issue.get("severity_reason", "Customer complaints reported.")
    trend = issue.get("trend", "N/A")
    trend_direction = issue.get("trend_direction", "stable")
    trend_reason = issue.get("trend_reason", "")
    is_emerging = issue.get("is_emerging", False)

    # Top customer quotes (real text only)
    customer_quotes = []
    for r in evidence_reviews[:5]:
        txt = r.get("text") or r.get("cleaned_text") or ""
        rating_str = f" ({int(r['rating'])}★)" if r.get("rating") else ""
        date_str = f" [{r['date']}]" if r.get("date") else ""
        customer_quotes.append({
            "quote": txt,
            "metadata": f"{r.get('platform') or 'User'}{rating_str}{date_str}",
            "emotion": r.get("emotion") or dominant_emotion,
            "rating": r.get("rating")
        })

    # Domain specific hypotheses
    theme_lower = theme.lower()
    investigation_areas = []
    if "payment" in theme_lower or "checkout" in theme_lower or "card" in theme_lower:
        investigation_areas = [
            "Payment Gateway Integration: Verify webhook handling and timeout thresholds with payment service provider.",
            "Double-Charge / Idempotency: Inspect idempotency keys on checkout transaction retries.",
            "Client-Side Validation: Ensure payment button disables during in-flight transaction to prevent duplicate submissions."
        ]
    elif "crash" in theme_lower or "freeze" in theme_lower or "startup" in theme_lower:
        investigation_areas = [
            "Crash Diagnostics: Query Sentry/Firebase Crashlytics for recent stack traces matching latest releases.",
            "Memory Leak / GPU Render: Review image/asset memory allocation on affected device architectures.",
            "Startup Initialization: Check for blocking network calls on application splash/main thread."
        ]
    elif "login" in theme_lower or "auth" in theme_lower or "password" in theme_lower:
        investigation_areas = [
            "OAuth & Token Refresh: Inspect OAuth redirect URIs and expired token renewal logic.",
            "SMS / 2FA Delivery: Verify SMS gateway deliverability rates and vendor latency.",
            "Session Invalidation: Check session cookie expiry rules and cross-platform biometric auth."
        ]
    elif "subscription" in theme_lower or "charge" in theme_lower or "billing" in theme_lower:
        investigation_areas = [
            "Store Receipt Validation: Audit Apple StoreKit / Google Play Billing receipt synchronization.",
            "Cancellation UX: Clarify subscription management entry points to prevent accidental dispute escalation.",
            "Trial-to-Paid Transition: Verify grace period notifications and renewal warning emails."
        ]
    elif "search" in theme_lower or "results" in theme_lower:
        investigation_areas = [
            "Search Query Indexing: Review Elasticsearch / Algolia zero-result query logs.",
            "Filter Facets: Check filter state sanitization and sorting regression.",
            "Latency: Measure search API p99 latency during peak traffic hours."
        ]
    elif "notification" in theme_lower or "push" in theme_lower:
        investigation_areas = [
            "Push Notification Throttling: Review APNS / FCM push frequency caps and notification batching.",
            "User Preferences: Verify whether opt-out toggle correctly updates server-side topic subscriptions.",
            "Background Delivery Service: Check background sync reliability on power-saving mode."
        ]
    else:
        investigation_areas = [
            "User Experience Flow: Review conversion drop-off funnel for the impacted feature surface.",
            "Telemetry & Error Logs: Cross-reference telemetry events with user journey timestamps.",
            "Customer Support Playbook: Provide front-line support with temporary troubleshooting workarounds."
        ]

    # Action recommendations
    recommended_actions = [
        f"Prioritize ticket in upcoming sprint under {severity} urgency.",
        f"Assign engineering triage team to investigate: {investigation_areas[0].split(':')[0]}.",
        "Monitor temporal trajectory over the next 48 hours for further volume escalation."
    ]

    return {
        "title": f"PM Executive Brief: {theme}",
        "issue_id": issue.get("id"),
        "theme": theme,
        "is_emerging": is_emerging,
        "summary": f"{'🚨 CRITICAL ALERT: ' if is_emerging else ''}An issue regarding '{theme}' has accumulated {review_count} customer reports, with {negative_pct}% negative sentiment and dominant emotion of '{dominant_emotion}'.",
        "problem_statement": f"Customers are experiencing significant friction with {theme}. The issue has reached {severity} severity (score: {severity_score:.2f}) primarily due to: {severity_reason}",
        "impact_signals": {
            "total_reviews": review_count,
            "negative_percentage": f"{negative_pct}%",
            "dominant_emotion": dominant_emotion,
            "severity_level": severity,
            "severity_score": severity_score,
            "severity_rationale": severity_reason
        },
        "temporal_trajectory": {
            "trend": trend,
            "trend_direction": trend_direction,
            "explanation": trend_reason or ("Stable volume" if trend != "N/A" else "Date information not present in uploaded CSV.")
        },
        "customer_statements": customer_quotes,
        "investigation_areas": investigation_areas,
        "recommended_actions": recommended_actions
    }
