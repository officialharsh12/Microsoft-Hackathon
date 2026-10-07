import pandas as pd
from app.services.preprocessing import clean_review_text, redact_pii, preprocess_dataframe

def test_pii_redaction():
    text = "Contact me at user@example.com or call 555-123-4567. Card: 4111-2222-3333-4444 visit https://mysite.com"
    redacted = redact_pii(text)
    assert "[EMAIL]" in redacted
    assert "[PHONE]" in redacted
    assert "[CARD_NUMBER]" in redacted
    assert "[URL]" in redacted
    assert "user@example.com" not in redacted
    assert "4111-2222-3333-4444" not in redacted

def test_clean_review_text():
    text = "   This  app    crashes on   startup!!! \n\n Please fix it!  "
    cleaned = clean_review_text(text)
    assert cleaned == "This app crashes on startup!!! Please fix it!"

def test_preprocess_dataframe():
    data = {
        "id": ["1", "2", "3", "4", "5"],
        "content": [
            "Great app, love it!",
            "Payment failed with error",
            "Payment failed with error", # Duplicate
            "",                          # Empty
            None                         # Null
        ],
        "created_at": ["2026-03-01", "2026-03-02", "2026-03-02", "2026-03-03", "2026-03-04"],
        "stars": [5, 1, 1, 3, 2]
    }
    df = pd.DataFrame(data)
    records, stats = preprocess_dataframe(
        df,
        text_col="content",
        date_col="created_at",
        rating_col="stars",
        id_col="id"
    )
    assert stats["original_rows"] == 5
    assert stats["duplicates_removed"] == 1
    assert stats["null_or_empty_removed"] == 2
    assert stats["final_rows"] == 2
    assert len(records) == 2
    assert records[0]["original_id"] == "1"
    assert records[0]["rating"] == 5.0
    assert records[0]["review_date"] == "2026-03-01"
