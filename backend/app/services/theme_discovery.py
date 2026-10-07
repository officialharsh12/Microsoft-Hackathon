from typing import List, Dict, Any, Tuple
import numpy as np
from collections import Counter
from sklearn.feature_extraction.text import TfidfVectorizer

# Domain stop words to filter out generic review filler
DOMAIN_STOPWORDS = {
    "app", "application", "phone", "iphone", "android", "mobile", "device",
    "just", "really", "even", "every", "also", "would", "could", "get", "got",
    "use", "using", "used", "like", "good", "bad", "thing", "things", "time",
    "times", "update", "version", "new", "day", "days", "way", "please", "fix",
    "people", "user", "users", "trying", "tried", "screen", "go", "going"
}

def extract_cluster_keywords(texts: List[str], top_n: int = 4) -> List[str]:
    """
    Extracts top keywords/bigrams from a group of texts using TF-IDF.
    """
    if not texts:
        return ["General Feedback"]

    try:
        tfidf = TfidfVectorizer(
            stop_words="english",
            ngram_range=(1, 2),
            max_df=0.9,
            min_df=1,
            max_features=100
        )
        matrix = tfidf.fit_transform(texts)
        feature_names = tfidf.get_feature_names_out()
        scores = np.asarray(matrix.sum(axis=0)).ravel()
        
        # Sort features by cumulative score, filtering out domain filler
        ranked_indices = scores.argsort()[::-1]
        valid_keywords = []
        for idx in ranked_indices:
            term = feature_names[idx].strip()
            words = term.split()
            # If all words in ngram are in domain stopwords, skip
            if all(w in DOMAIN_STOPWORDS for w in words):
                continue
            if len(term) < 3:
                continue
            valid_keywords.append(term.title())
            if len(valid_keywords) >= top_n:
                break

        return valid_keywords if valid_keywords else ["General Feedback"]
    except Exception:
        # Fallback to simple word counter
        words = []
        for t in texts:
            words.extend([w.lower() for w in t.split() if len(w) > 3 and w.lower() not in DOMAIN_STOPWORDS])
        counts = Counter(words).most_common(top_n)
        return [w.title() for w, _ in counts] if counts else ["General Feedback"]

def generate_theme_title(keywords: List[str], top_review_text: str) -> str:
    """
    Generates a human-friendly theme title from top keywords.
    """
    if not keywords:
        return "Customer Feedback"
    
    # Capitalize and join top 2-3 distinctive keywords
    selected_kws = keywords[:3]
    return " & ".join(selected_kws)

def discover_themes(
    reviews: List[Dict[str, Any]],
    embeddings: np.ndarray,
    cluster_labels: np.ndarray
) -> List[Dict[str, Any]]:
    """
    Discovers themes for each identified cluster.
    Returns:
        List of cluster theme objects:
        [
          {
            "cluster_id": int,
            "theme": str,
            "keywords": List[str],
            "review_count": int,
            "positive_count": int,
            "negative_count": int,
            "negative_percentage": float,
            "dominant_emotion": str,
            "representative_review_ids": List[int/str],
            "representative_reviews": List[str],
            "reviews": List[Dict[str, Any]]
          },
          ...
        ]
    """
    unique_clusters = sorted(list(set(cluster_labels)))
    theme_results = []

    for cluster_id in unique_clusters:
        indices = np.where(cluster_labels == cluster_id)[0]
        cluster_reviews = [reviews[idx] for idx in indices]
        cluster_embeddings = embeddings[indices]
        count = len(cluster_reviews)

        # 1. Compute cluster centroid
        centroid = np.mean(cluster_embeddings, axis=0)
        # Cosine similarity to centroid for all members
        similarities = np.dot(cluster_embeddings, centroid)
        ranked_member_indices = np.argsort(similarities)[::-1]

        # Top representative reviews (up to 5)
        top_k_indices = ranked_member_indices[:min(5, count)]
        rep_reviews = [cluster_reviews[i]["cleaned_text"] for i in top_k_indices]
        rep_ids = [cluster_reviews[i].get("id") or cluster_reviews[i].get("original_id") for i in top_k_indices]

        # 2. Sentiment distribution
        sentiments = [r.get("sentiment", "NEGATIVE").upper() for r in cluster_reviews]
        neg_count = sum(1 for s in sentiments if s == "NEGATIVE")
        pos_count = sum(1 for s in sentiments if s == "POSITIVE")
        neg_pct = round((neg_count / count) * 100, 1) if count > 0 else 0.0

        # 3. Dominant emotion
        emotions = [r.get("emotion", "neutral") for r in cluster_reviews if r.get("emotion")]
        emotion_counts = Counter(emotions)
        dominant_emotion = emotion_counts.most_common(1)[0][0] if emotion_counts else "neutral"

        # 4. Keyword and Theme extraction
        all_texts = [r["cleaned_text"] for r in cluster_reviews]
        keywords = extract_cluster_keywords(all_texts, top_n=3)
        theme_title = generate_theme_title(keywords, rep_reviews[0] if rep_reviews else "")

        theme_results.append({
            "cluster_id": int(cluster_id),
            "theme": theme_title,
            "keywords": keywords,
            "review_count": count,
            "positive_count": pos_count,
            "negative_count": neg_count,
            "negative_percentage": neg_pct,
            "dominant_emotion": dominant_emotion,
            "representative_review_ids": rep_ids,
            "representative_reviews": rep_reviews,
            "review_indices": indices.tolist(),
        })

    # Sort themes by review count descending
    theme_results.sort(key=lambda t: t["review_count"], reverse=True)
    return theme_results
