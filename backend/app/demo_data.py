from collections import Counter
from typing import Dict, List, Any


DEMO_DATASETS: Dict[int, Dict[str, Any]] = {
    1: {
        "dataset_id": 1,
        "name": "FinTech App",
        "filename": "demo_fintech.csv",
        "is_demo": True,
        "reviews": [
            {
                "review_id": "FT-101",
                "review_text": "Payment was deducted but the checkout page still failed and showed an error.",
                "rating": 1,
                "date": "2026-09-02",
                "app_version": "8.2.1",
                "platform": "iOS",
                "country": "India",
                "sentiment": "NEGATIVE",
                "emotion": "anger",
                "theme": "Payment Failure",
                "issue": "PAYMENT_FAILURE",
                "severity": "CRITICAL",
                "priority": "P0",
            },
            {
                "review_id": "FT-102",
                "review_text": "My card was charged twice for the same transfer. This is unacceptable.",
                "rating": 1,
                "date": "2026-09-04",
                "app_version": "8.2.2",
                "platform": "Android",
                "country": "United States",
                "sentiment": "NEGATIVE",
                "emotion": "anger",
                "theme": "Payment Failure",
                "issue": "PAYMENT_FAILURE",
                "severity": "CRITICAL",
                "priority": "P0",
            },
            {
                "review_id": "FT-103",
                "review_text": "OTP never arrives after login attempt. I am locked out of my bank account.",
                "rating": 2,
                "date": "2026-09-05",
                "app_version": "8.2.1",
                "platform": "Android",
                "country": "United Arab Emirates",
                "sentiment": "NEGATIVE",
                "emotion": "fear",
                "theme": "Login & OTP",
                "issue": "LOGIN_FAILURE",
                "severity": "HIGH",
                "priority": "P1",
            },
            {
                "review_id": "FT-104",
                "review_text": "Transfer screen hangs for minutes and then times out. Very frustrating.",
                "rating": 2,
                "date": "2026-09-07",
                "app_version": "8.2.3",
                "platform": "iOS",
                "country": "Singapore",
                "sentiment": "NEGATIVE",
                "emotion": "annoyance",
                "theme": "Transaction Delay",
                "issue": "TRANSACTION_DELAY",
                "severity": "HIGH",
                "priority": "P1",
            },
            {
                "review_id": "FT-105",
                "review_text": "The latest update improved the app flow and the transfers now work smoothly.",
                "rating": 5,
                "date": "2026-09-10",
                "app_version": "8.2.4",
                "platform": "iOS",
                "country": "Australia",
                "sentiment": "POSITIVE",
                "emotion": "joy",
                "theme": "App Stability",
                "issue": "APP_STABILITY",
                "severity": "LOW",
                "priority": "P3",
            },
        ],
    },
    2: {
        "dataset_id": 2,
        "name": "E-Commerce App",
        "filename": "demo_ecommerce.csv",
        "is_demo": True,
        "reviews": [
            {
                "review_id": "EC-201",
                "review_text": "Delivery is late again and there is no updated tracking information.",
                "rating": 2,
                "date": "2026-09-03",
                "app_version": "5.9.0",
                "platform": "Android",
                "country": "Germany",
                "sentiment": "NEGATIVE",
                "emotion": "disappointment",
                "theme": "Delivery Delay",
                "issue": "DELIVERY_DELAY",
                "severity": "HIGH",
                "priority": "P1",
            },
            {
                "review_id": "EC-202",
                "review_text": "I requested a refund but the app says it is processing without any confirmation.",
                "rating": 1,
                "date": "2026-09-05",
                "app_version": "5.9.1",
                "platform": "Android",
                "country": "France",
                "sentiment": "NEGATIVE",
                "emotion": "frustration",
                "theme": "Refund Issue",
                "issue": "REFUND_ISSUE",
                "severity": "HIGH",
                "priority": "P1",
            },
            {
                "review_id": "EC-203",
                "review_text": "Search is broken: it returns irrelevant products and no results for common items.",
                "rating": 2,
                "date": "2026-09-06",
                "app_version": "5.9.2",
                "platform": "iOS",
                "country": "United Kingdom",
                "sentiment": "NEGATIVE",
                "emotion": "annoyance",
                "theme": "Search Quality",
                "issue": "SEARCH_FAILURE",
                "severity": "MEDIUM",
                "priority": "P2",
            },
            {
                "review_id": "EC-204",
                "review_text": "Product pages are slow and images take forever to load on mobile data.",
                "rating": 3,
                "date": "2026-09-08",
                "app_version": "5.9.1",
                "platform": "iOS",
                "country": "Canada",
                "sentiment": "NEGATIVE",
                "emotion": "sadness",
                "theme": "Performance",
                "issue": "PERFORMANCE",
                "severity": "MEDIUM",
                "priority": "P2",
            },
            {
                "review_id": "EC-205",
                "review_text": "The new search filters are excellent and product discovery is much easier.",
                "rating": 5,
                "date": "2026-09-12",
                "app_version": "5.9.3",
                "platform": "Android",
                "country": "United States",
                "sentiment": "POSITIVE",
                "emotion": "joy",
                "theme": "Product Discovery",
                "issue": "DISCOVERY_EXPERIENCE",
                "severity": "LOW",
                "priority": "P3",
            },
        ],
    },
    3: {
        "dataset_id": 3,
        "name": "Travel App",
        "filename": "demo_travel.csv",
        "is_demo": True,
        "reviews": [
            {
                "review_id": "TR-301",
                "review_text": "Booking failed at payment and my reservation was not created.",
                "rating": 1,
                "date": "2026-09-02",
                "app_version": "7.4.0",
                "platform": "Android",
                "country": "Italy",
                "sentiment": "NEGATIVE",
                "emotion": "anger",
                "theme": "Booking Failure",
                "issue": "BOOKING_FAILURE",
                "severity": "CRITICAL",
                "priority": "P0",
            },
            {
                "review_id": "TR-302",
                "review_text": "Cancellation process is confusing and the app keeps saying the request failed.",
                "rating": 2,
                "date": "2026-09-04",
                "app_version": "7.4.1",
                "platform": "iOS",
                "country": "Spain",
                "sentiment": "NEGATIVE",
                "emotion": "frustration",
                "theme": "Cancellation Flow",
                "issue": "CANCELLATION_ISSUE",
                "severity": "HIGH",
                "priority": "P1",
            },
            {
                "review_id": "TR-303",
                "review_text": "Flight results load too slowly and the pricing page freezes on my phone.",
                "rating": 3,
                "date": "2026-09-07",
                "app_version": "7.4.2",
                "platform": "Android",
                "country": "United States",
                "sentiment": "NEGATIVE",
                "emotion": "annoyance",
                "theme": "Performance",
                "issue": "PERFORMANCE",
                "severity": "MEDIUM",
                "priority": "P2",
            },
            {
                "review_id": "TR-304",
                "review_text": "The app was easy to use and the itinerary summary looked great after booking.",
                "rating": 5,
                "date": "2026-09-10",
                "app_version": "7.4.3",
                "platform": "iOS",
                "country": "Australia",
                "sentiment": "POSITIVE",
                "emotion": "joy",
                "theme": "Booking Experience",
                "issue": "BOOKING_EXPERIENCE",
                "severity": "LOW",
                "priority": "P3",
            },
            {
                "review_id": "TR-305",
                "review_text": "Payment authorization fails when I use saved card details. Very unreliable.",
                "rating": 2,
                "date": "2026-09-11",
                "app_version": "7.4.3",
                "platform": "Android",
                "country": "France",
                "sentiment": "NEGATIVE",
                "emotion": "fear",
                "theme": "Payment Failure",
                "issue": "PAYMENT_FAILURE",
                "severity": "HIGH",
                "priority": "P1",
            },
        ],
    },
}


def dataset_list():
    return [
        {
            "id": dataset_id,
            "filename": dataset["filename"],
            "dataset_name": dataset["name"],
            "status": "completed",
            "is_demo": True,
            "review_count": len(dataset["reviews"]),
            "created_at": "2026-09-01T00:00:00Z",
        }
        for dataset_id, dataset in sorted(DEMO_DATASETS.items())
    ]


def get_demo_dataset(dataset_id: int):
    return DEMO_DATASETS.get(dataset_id)


def dashboard_payload(dataset_id: int):
    dataset = get_demo_dataset(dataset_id)
    if not dataset:
        return {}

    reviews = dataset["reviews"]
    total_reviews = len(reviews)
    sentiment_counts = Counter(r["sentiment"] for r in reviews)
    positive_count = sentiment_counts.get("POSITIVE", 0)
    negative_count = sentiment_counts.get("NEGATIVE", 0)
    positive_pct = round((positive_count / total_reviews) * 100, 1) if total_reviews else 0
    negative_pct = round((negative_count / total_reviews) * 100, 1) if total_reviews else 0

    issue_groups: Dict[str, Dict[str, Any]] = {}
    for review in reviews:
        item = issue_groups.setdefault(
            review["issue"],
            {"id": review["issue"], "theme": review["theme"], "severity": review["severity"], "review_count": 0, "negative_percentage": 0, "is_emerging": review["severity"] in {"HIGH", "CRITICAL"}, "trend": "+12%", "sample_quotes": [], "issue_rate": 0.0},
        )
        item["review_count"] += 1
        if review["sentiment"] == "NEGATIVE":
            item["negative_percentage"] += 1
        item["sample_quotes"].append(review["review_text"])

    issue_list = []
    for issue_id, issue in issue_groups.items():
        review_count = issue["review_count"]
        negative_pct_issue = round((issue["negative_percentage"] / review_count) * 100, 1) if review_count else 0
        issue_list.append(
            {
                "id": issue_id,
                "dataset_id": dataset_id,
                "cluster_id": 1,
                "theme": issue["theme"],
                "review_count": review_count,
                "negative_percentage": negative_pct_issue,
                "dominant_emotion": "anger",
                "severity": issue["severity"],
                "severity_score": 0.82 if issue["severity"] == "CRITICAL" else 0.68 if issue["severity"] == "HIGH" else 0.45,
                "severity_reason": "Customer friction detected in review evidence.",
                "trend": issue["trend"],
                "trend_direction": "increasing",
                "trend_percentage": 12.0,
                "is_emerging": issue["is_emerging"],
                "sample_quotes": issue["sample_quotes"][:2],
                "timeline": [],
            }
        )

    issue_list = sorted(issue_list, key=lambda item: (item["is_emerging"], item["severity_score"]), reverse=True)
    high_sev_count = sum(1 for item in issue_list if item["severity"] in {"CRITICAL", "HIGH"})

    emotion_counts = Counter(r["emotion"] for r in reviews)
    emotion_distribution = [
        {"name": name.title(), "count": count, "percentage": round((count / total_reviews) * 100, 1)}
        for name, count in emotion_counts.most_common(5)
    ]

    top_themes = []
    theme_counts = Counter(r["theme"] for r in reviews)
    for theme_name, count in theme_counts.most_common(4):
        top_themes.append({
            "theme": theme_name,
            "count": count,
            "percentage": round((count / total_reviews) * 100, 1),
            "sentiment": "NEGATIVE" if count >= 2 else "POSITIVE",
        })

    timeline = [
        {"date": "2026-09-01", "count": 2},
        {"date": "2026-09-03", "count": 3},
        {"date": "2026-09-05", "count": 5},
        {"date": "2026-09-07", "count": 6},
        {"date": "2026-09-09", "count": 4},
        {"date": "2026-09-11", "count": 7},
    ]

    return {
        "dataset_id": dataset_id,
        "dataset_filename": dataset["filename"],
        "total_reviews": total_reviews,
        "positive_percentage": positive_pct,
        "negative_percentage": negative_pct,
        "high_severity_count": high_sev_count,
        "emerging_issues_count": sum(1 for item in issue_list if item["is_emerging"]),
        "sentiment_distribution": [
            {"name": "Positive", "count": positive_count, "percentage": positive_pct, "color": "#22c55e"},
            {"name": "Negative", "count": negative_count, "percentage": negative_pct, "color": "#ef4444"},
        ],
        "emotion_distribution": emotion_distribution,
        "severity_distribution": [
            {"severity": "CRITICAL", "count": sum(1 for r in reviews if r["severity"] == "CRITICAL"), "color": "#f87171"},
            {"severity": "HIGH", "count": sum(1 for r in reviews if r["severity"] == "HIGH"), "color": "#f59e0b"},
            {"severity": "MEDIUM", "count": sum(1 for r in reviews if r["severity"] == "MEDIUM"), "color": "#a78bfa"},
            {"severity": "LOW", "count": sum(1 for r in reviews if r["severity"] == "LOW"), "color": "#22c55e"},
        ],
        "top_issues": issue_list,
        "emerging_issues": [item for item in issue_list if item["is_emerging"]][:3],
        "trend_timeline": timeline,
        "top_themes": top_themes,
    }


def issue_list_for_dataset(dataset_id: int):
    dataset = get_demo_dataset(dataset_id)
    if not dataset:
        return []
    grouped: Dict[str, Dict[str, Any]] = {}
    for review in dataset["reviews"]:
        issue = grouped.setdefault(review["issue"], {"id": review["issue"], "theme": review["theme"], "severity": review["severity"], "review_count": 0, "negative_percentage": 0, "trend": "+12%", "is_emerging": review["severity"] in {"HIGH", "CRITICAL"}})
        issue["review_count"] += 1
        if review["sentiment"] == "NEGATIVE":
            issue["negative_percentage"] += 1
    items = []
    for issue_id, issue in grouped.items():
        review_count = issue["review_count"]
        neg_pct = round((issue["negative_percentage"] / review_count) * 100, 1) if review_count else 0
        items.append({
            "id": issue_id,
            "dataset_id": dataset_id,
            "cluster_id": 1,
            "theme": issue["theme"],
            "review_count": review_count,
            "negative_percentage": neg_pct,
            "dominant_emotion": "anger",
            "severity": issue["severity"],
            "severity_score": 0.82 if issue["severity"] == "CRITICAL" else 0.68 if issue["severity"] == "HIGH" else 0.45,
            "severity_reason": "Customer friction detected in review evidence.",
            "trend": issue["trend"],
            "trend_direction": "increasing",
            "trend_percentage": 12.0,
            "is_emerging": issue["is_emerging"],
            "sample_quotes": [r["review_text"] for r in dataset["reviews"] if r["issue"] == issue_id][:2],
            "timeline": [],
        })
    return sorted(items, key=lambda item: item["severity_score"], reverse=True)


def issue_detail_for_dataset(dataset_id: int, issue_key: str):
    issues = issue_list_for_dataset(dataset_id)
    for item in issues:
        if item["id"] == issue_key:
            return item
    return issues[0] if issues else {}


def evidence_for_issue(dataset_id: int, issue_key: str):
    dataset = get_demo_dataset(dataset_id)
    reviews = [r for r in dataset["reviews"] if r["issue"] == issue_key]
    return {
        "issue_id": issue_key,
        "theme": reviews[0]["theme"] if reviews else "Issue",
        "severity": reviews[0]["severity"] if reviews else "MEDIUM",
        "severity_score": 0.8,
        "negative_percentage": 80,
        "dominant_emotion": "anger",
        "trend": "+12%",
        "detection_rationale": {
            "summary": "Recurring negative feedback around the same customer journey step.",
            "review_volume": f"{len(reviews)} matching reviews clustered together.",
            "sentiment_signal": "The majority of the cluster is negative sentiment.",
            "emotional_resonance": "Frustration and anger dominate the issue narrative.",
            "severity_level": "Critical issue with high customer impact.",
            "trend_trajectory": "Issue volume is increasing across recent dates.",
        },
        "evidence_count": len(reviews),
        "total_related_reviews": len(reviews),
        "evidence_reviews": [
            {
                "id": r["review_id"],
                "original_id": r["review_id"],
                "text": r["review_text"],
                "cleaned_text": r["review_text"],
                "sentiment": r["sentiment"],
                "sentiment_score": 0.92,
                "emotion": r["emotion"],
                "emotion_score": 0.87,
                "rating": r["rating"],
                "date": r["date"],
                "platform": r["platform"],
                "app_version": r["app_version"],
            }
            for r in reviews
        ],
    }


def pm_brief_for_issue(dataset_id: int, issue_key: str):
    dataset = get_demo_dataset(dataset_id)
    reviews = [r for r in dataset["reviews"] if r["issue"] == issue_key]
    theme = reviews[0]["theme"] if reviews else "Product Issue"
    return {
        "title": f"PM Executive Brief: {theme}",
        "issue_id": issue_key,
        "theme": theme,
        "is_emerging": True,
        "summary": f"Customers are reporting repeated friction in {theme} and the issue is growing across recent reviews.",
        "problem_statement": f"The {theme.lower()} cluster contains repeated customer complaints with negative sentiment and high impact on conversion.",
        "impact_signals": {
            "total_reviews": len(reviews),
            "negative_percentage": "80%",
            "dominant_emotion": "anger",
            "severity_level": reviews[0]["severity"] if reviews else "HIGH",
            "severity_score": 0.82,
            "severity_rationale": "High-volume negative feedback and customer frustration.",
        },
        "temporal_trajectory": {"trend": "+12%", "trend_direction": "increasing", "explanation": "Issue volume is rising over the most recent time window."},
        "customer_statements": [{"quote": r["review_text"], "metadata": f"{r['platform']} {r['rating']}★ {r['date']}", "emotion": r["emotion"], "rating": r["rating"]} for r in reviews[:3]],
        "investigation_areas": [
            "Inspect transaction and validation flows across the affected paths.",
            "Review recent release regressions tied to the app version in the customer reports.",
            "Confirm whether the same issue is affecting both iOS and Android users.",
        ],
        "recommended_actions": [
            "Prioritize a triage fix in the next active sprint.",
            "Validate suspected root cause with recent release telemetry.",
            "Monitor the issue rate after the fix and measure the next 7-day trend.",
        ],
    }
