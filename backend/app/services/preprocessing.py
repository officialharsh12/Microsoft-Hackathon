import re
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple

# Pre-compiled regex patterns for PII redaction
EMAIL_REGEX = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b')
PHONE_REGEX = re.compile(r'\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b')
CARD_REGEX = re.compile(r'\b(?:\d{4}[-\s]?){3}\d{4}\b')
URL_REGEX = re.compile(r'https?://\S+|www\.\S+')
WHITESPACE_REGEX = re.compile(r'\s+')


def redact_pii(text: str) -> str:
    """
    Redacts basic PII while preserving semantic meaning for sentiment/emotion models.
    """
    if not text:
        return ""
    text = EMAIL_REGEX.sub("[EMAIL]", text)
    text = PHONE_REGEX.sub("[PHONE]", text)
    text = CARD_REGEX.sub("[CARD_NUMBER]", text)
    text = URL_REGEX.sub("[URL]", text)
    return text


def clean_review_text(text: str) -> str:
    """
    Normalizes whitespace, removes unprintable characters, applies PII redaction,
    preserving case and punctuation needed for sentiment and emotion detection.
    """
    if not isinstance(text, str):
        return ""
    cleaned = WHITESPACE_REGEX.sub(" ", text).strip()
    cleaned = redact_pii(cleaned)
    return cleaned


def parse_date(date_val: Any) -> Optional[str]:
    """
    Safely parse various date formats into standard YYYY-MM-DD string.
    Returns None on failure — never raises.
    """
    if date_val is None:
        return None
    try:
        if pd.isna(date_val):
            return None
    except (TypeError, ValueError):
        pass
    try:
        dt = pd.to_datetime(date_val, errors="coerce")
        if pd.isna(dt):
            return None
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return None


def parse_rating(rating_val: Any) -> Optional[float]:
    """
    Safely parse numerical rating. Returns None on failure — never raises.
    """
    if rating_val is None:
        return None
    try:
        if pd.isna(rating_val):
            return None
    except (TypeError, ValueError):
        pass
    try:
        return float(rating_val)
    except (ValueError, TypeError):
        return None


def normalize_text(value: Any) -> str:
    """
    Normalize and strip text value.
    """
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass
    return str(value).strip()


def preprocess_dataframe(
    df: pd.DataFrame,
    text_col: str,
    date_col: Optional[str] = None,
    rating_col: Optional[str] = None,
    id_col: Optional[str] = None,
    platform_col: Optional[str] = None,
    version_col: Optional[str] = None,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Validates and preprocesses a raw reviews DataFrame.

    IMPORTANT: The ONLY hard filter is empty/missing review text.
    Missing date, rating, or ID fields are tolerated — those rows are still
    processed so that the full dataset is always analyzed.

    Supports datasets up to 10,000+ rows. Processes every row with no cap.

    Returns:
        processed_records: List of cleaned dicts ready for database insertion
        stats: Summary of preprocessing results
    """
    if text_col not in df.columns:
        raise ValueError(f"Review text column '{text_col}' not found in DataFrame. "
                         f"Available columns: {list(df.columns)}")

    original_count = len(df)
    valid_rows: List[Dict[str, Any]] = []
    skipped_empty = 0
    skipped_duplicate_id = 0
    skipped_duplicate_text = 0

    seen_ids: set = set()
    seen_texts: dict = {}

    for idx, row in df.iterrows():
        # ── 1. Text is the only mandatory field ───────────────────────────────
        raw_text = normalize_text(row.get(text_col) if text_col in row.index else None)
        cleaned_text = clean_review_text(raw_text)

        if not cleaned_text or len(cleaned_text.strip()) < 3:
            skipped_empty += 1
            continue  # Only skip truly empty/garbage rows

        # ── 2. Review ID — generate synthetic if missing ──────────────────────
        review_id: Optional[str] = None
        if id_col and id_col in row.index:
            review_id = normalize_text(row[id_col]) or None

        if not review_id:
            review_id = f"REV-{idx + 1:06d}"

        # Skip duplicate IDs (exact duplicate records)
        if review_id in seen_ids:
            skipped_duplicate_id += 1
            continue
        seen_ids.add(review_id)

        # Skip exact duplicate text (copy-pasted reviews)
        if cleaned_text in seen_texts:
            skipped_duplicate_text += 1
            continue
        seen_texts[cleaned_text] = review_id

        # ── 3. Optional fields — parse but NEVER skip for being missing ───────
        review_date = None
        if date_col and date_col in row.index:
            review_date = parse_date(row[date_col])

        rating = None
        if rating_col and rating_col in row.index:
            rating = parse_rating(row[rating_col])

        platform = None
        if platform_col and platform_col in row.index and pd.notna(row[platform_col]):
            platform = str(row[platform_col]).strip() or None

        version = None
        if version_col and version_col in row.index and pd.notna(row[version_col]):
            version = str(row[version_col]).strip() or None

        valid_rows.append({
            "original_id": review_id,
            "raw_text": raw_text,
            "cleaned_text": cleaned_text,
            "review_date": review_date,
            "rating": rating,
            "platform": platform,
            "app_version": version,
        })

    stats = {
        "original_rows": original_count,
        "valid_row_count": len(valid_rows),
        "invalid_row_count": original_count - len(valid_rows),
        "duplicate_count": skipped_duplicate_id + skipped_duplicate_text,
        "duplicates_removed": skipped_duplicate_id + skipped_duplicate_text,
        "null_or_empty_removed": skipped_empty,
        "final_rows": len(valid_rows),
        "has_date": any(r["review_date"] is not None for r in valid_rows),
        "has_rating": any(r["rating"] is not None for r in valid_rows),
    }

    return valid_rows, stats
