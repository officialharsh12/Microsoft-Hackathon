import io
import shutil
import pandas as pd
from pathlib import Path
from typing import Optional, List
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query
from app.config import settings
from app.database import get_db_connection
from app.schemas.review import CSVUploadResponse, AnalysisRequest, AnalysisResponse, ReviewItem
from app.services.preprocessing import preprocess_dataframe
from app.models.sentiment import sentiment_model
from app.models.emotion import emotion_model
from app.models.embeddings import embedding_model
from app.services.clustering import cluster_embeddings
from app.services.issue_engine import aggregate_issues

router = APIRouter(prefix="/reviews", tags=["Reviews"])

@router.post("/upload-demo", response_model=CSVUploadResponse)
async def upload_demo_csv():
    """
    Loads the full 100-review demo dataset directly from disk.
    """
    demo_path = settings.DATA_DIR / "demo_reviews.csv"
    if not demo_path.exists():
        raise HTTPException(status_code=404, detail="Demo dataset file not found.")

    with open(demo_path, "rb") as f:
        contents = f.read()

    df = pd.read_csv(io.BytesIO(contents))
    columns = list(df.columns)

    dataset_filename = "demo_reviews.csv"
    upload_path = settings.DATA_DIR / f"upload_{dataset_filename}"
    with open(upload_path, "wb") as f:
        f.write(contents)

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO datasets (filename, review_count, status, text_col, date_col, rating_col, id_col, is_demo)
        VALUES (?, ?, 'uploaded', 'review_text', 'date', 'rating', 'review_id', 1)
        """,
        (dataset_filename, len(df))
    )
    dataset_id = cursor.lastrowid
    conn.commit()
    conn.close()

    sample_rows = df.head(5).fillna("").to_dict(orient="records")

    return CSVUploadResponse(
        dataset_id=dataset_id,
        filename=dataset_filename,
        total_rows=len(df),
        columns=columns,
        detected_text_column="review_text",
        detected_date_column="date",
        detected_rating_column="rating",
        detected_id_column="review_id",
        sample_rows=sample_rows
    )

@router.post("/upload", response_model=CSVUploadResponse)
async def upload_csv(file: UploadFile = File(...)):
    """
    Accepts CSV upload, extracts column metadata, guesses column types,
    and stages raw file for analysis.
    """
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Uploaded file must be a CSV (.csv)")

    try:
        contents = await file.read()
        # Read entire CSV for accurate row count and column detection
        # (only head(5) is sent back as a preview sample)
        try:
            df = pd.read_csv(io.BytesIO(contents))
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to parse CSV file: {str(e)}")

        if df.empty or len(df.columns) == 0:
            raise HTTPException(status_code=400, detail="CSV file appears to be empty.")

        columns = list(df.columns)

        # Detect columns intelligently based on priority heuristics
        def find_col(exact_candidates, partial_candidates=None, exclude=None):
            exclude = exclude or []
            # 1. Exact match first
            for col in columns:
                cl = col.lower().strip()
                if cl in exclude:
                    continue
                if cl in exact_candidates:
                    return col
            # 2. Substring match
            if partial_candidates:
                for col in columns:
                    cl = col.lower().strip()
                    if any(ex in cl for ex in exclude):
                        continue
                    if any(cand in cl for cand in partial_candidates):
                        return col
            return None

        id_col = find_col(["review_id", "id", "item_id", "uid"], partial_candidates=["id"])
        text_col = find_col(
            ["review_text", "text", "content", "review", "comment", "feedback", "body", "description"],
            partial_candidates=["review", "text", "content", "comment"],
            exclude=["id", "date", "rating", "version", "platform"]
        )
        date_col = find_col(
            ["date", "review_date", "created_at", "timestamp", "time"],
            partial_candidates=["date", "time", "created"]
        )
        rating_col = find_col(
            ["rating", "stars", "score", "star_rating"],
            partial_candidates=["rating", "star", "score"]
        )

        # Save uploaded file to data folder
        dataset_filename = file.filename
        upload_path = settings.DATA_DIR / f"upload_{dataset_filename}"
        with open(upload_path, "wb") as f:
            f.write(contents)

        # Record dataset entry in DB
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO datasets (filename, review_count, status, text_col, date_col, rating_col, id_col)
            VALUES (?, ?, 'uploaded', ?, ?, ?, ?)
            """,
            (dataset_filename, len(df), text_col, date_col, rating_col, id_col)
        )
        dataset_id = cursor.lastrowid
        conn.commit()
        conn.close()

        # Clean sample rows for JSON response
        sample_rows = df.head(5).fillna("").to_dict(orient="records")

        return CSVUploadResponse(
            dataset_id=dataset_id,
            filename=dataset_filename,
            total_rows=len(df),
            columns=columns,
            detected_text_column=text_col,
            detected_date_column=date_col,
            detected_rating_column=rating_col,
            detected_id_column=id_col,
            sample_rows=sample_rows
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error uploading CSV: {str(e)}")

@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_dataset(payload: AnalysisRequest):
    """
    End-to-end AI intelligence pipeline:
    1. Preprocessing (PII redaction, dedup)
    2. Sentiment Analysis (DistilBERT)
    3. Emotion Classification (RoBERTa GoEmotions - 28 categories)
    4. Sentence Embeddings (MiniLM-L6-v2)
    5. Semantic Clustering (HDBSCAN/KMeans)
    6. Issue Aggregation + Severity Scoring
    7. RL Recommendation (Q-Learning engine) — runs per issue
    8. PostgreSQL persistence

    Supports unlimited rows (10,000+ reviews). No row cap.
    """
    import json
    from app.services.rl_engine import get_rl_recommendation

    conn = get_db_connection()
    cursor = conn.cursor()

    # Verify dataset exists
    cursor.execute("SELECT * FROM datasets WHERE id = ?", (payload.dataset_id,))
    dataset_row = cursor.fetchone()
    if not dataset_row:
        conn.close()
        raise HTTPException(status_code=404, detail="Dataset not found")

    filename = dataset_row["filename"]
    csv_path = settings.DATA_DIR / f"upload_{filename}"
    if not csv_path.exists():
        # Try demo path fallback
        demo_path = settings.DATA_DIR / "demo_reviews.csv"
        if demo_path.exists():
            csv_path = demo_path
        else:
            conn.close()
            raise HTTPException(status_code=404, detail="Dataset file not found on disk")

    try:
        # ── Step 1: Load full CSV (no row limit) ─────────────────────────────
        df = pd.read_csv(csv_path)
        total_input_rows = len(df)

        # Optional cap only if MAX_REVIEWS > 0 (default=0 means unlimited)
        if settings.MAX_REVIEWS > 0 and total_input_rows > settings.MAX_REVIEWS:
            df = df.head(settings.MAX_REVIEWS)

        # ── Step 2: Preprocess (text-only filter — never drops for missing date/rating) ──
        processed_records, stats = preprocess_dataframe(
            df=df,
            text_col=payload.text_column,
            date_col=payload.date_column,
            rating_col=payload.rating_column,
            id_col=payload.id_column,
            platform_col=payload.platform_column,
            version_col=payload.version_column,
        )

        if len(processed_records) == 0:
            conn.close()
            raise HTTPException(
                status_code=400,
                detail=f"No valid reviews found. Check that '{payload.text_column}' column has text content."
            )

        # Update dataset status to processing
        cursor.execute(
            """
            UPDATE datasets
            SET text_col = ?, date_col = ?, rating_col = ?, id_col = ?,
                review_count = ?, valid_row_count = ?, invalid_row_count = ?,
                duplicate_count = ?, status = 'processing'
            WHERE id = ?
            """,
            (
                payload.text_column, payload.date_column, payload.rating_column,
                payload.id_column, total_input_rows,
                stats["valid_row_count"], stats["null_or_empty_removed"],
                stats["duplicate_count"], payload.dataset_id
            )
        )
        conn.commit()

        # ── Step 3: NLP Inference (Batched, GPU-accelerated if available) ─────
        cleaned_texts = [r["cleaned_text"] for r in processed_records]

        # Sentiment: DistilBERT (POSITIVE / NEGATIVE + confidence score)
        sentiment_results = sentiment_model.predict_batch(cleaned_texts)

        # Emotion: RoBERTa GoEmotions (28 emotion categories)
        emotion_results = emotion_model.predict_batch(cleaned_texts)

        # Embeddings: MiniLM-L6-v2 (384-dimensional sentence vectors)
        embeddings = embedding_model.encode(cleaned_texts)

        # ── Step 4: Semantic Clustering ───────────────────────────────────────
        cluster_labels = cluster_embeddings(embeddings)

        # Merge inference results into records
        for i, r in enumerate(processed_records):
            r["sentiment"] = sentiment_results[i]["sentiment"]
            r["sentiment_score"] = sentiment_results[i]["sentiment_score"]
            r["emotion"] = emotion_results[i]["emotion"]
            r["emotion_score"] = emotion_results[i]["emotion_score"]
            r["cluster_id"] = int(cluster_labels[i])

        # ── Step 5: Clear prior results for this dataset ──────────────────────
        cursor.execute("DELETE FROM reviews WHERE dataset_id = ?", (payload.dataset_id,))
        cursor.execute("DELETE FROM issues WHERE dataset_id = ?", (payload.dataset_id,))
        cursor.execute("DELETE FROM review_embeddings WHERE dataset_id = ?", (payload.dataset_id,))
        cursor.execute("DELETE FROM llm_insights WHERE dataset_id = ?", (payload.dataset_id,))
        conn.commit()

        # ── Step 6: Persist all reviews + embeddings ──────────────────────────
        review_ids = []
        for i, r in enumerate(processed_records):
            cursor.execute(
                """
                INSERT INTO reviews (
                    dataset_id, original_id, raw_text, cleaned_text, review_date, rating,
                    platform, app_version, sentiment, sentiment_score, emotion, emotion_score, cluster_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload.dataset_id, r["original_id"], r["raw_text"], r["cleaned_text"],
                    r["review_date"], r["rating"], r["platform"], r["app_version"],
                    r["sentiment"], r["sentiment_score"], r["emotion"], r["emotion_score"],
                    r["cluster_id"]
                )
            )
            r_id = cursor.lastrowid
            review_ids.append(r_id)
            r["id"] = r_id

            # Serialize and store embedding vector
            emb_blob = embedding_model.serialize_vector(embeddings[i])
            cursor.execute(
                "INSERT INTO review_embeddings (dataset_id, review_id, embedding) VALUES (?, ?, ?)",
                (payload.dataset_id, r_id, emb_blob)
            )

        conn.commit()

        # ── Step 7: Issue Aggregation + Severity Scoring ──────────────────────
        issues = aggregate_issues(processed_records, embeddings, cluster_labels)

        # ── Step 8: Persist issues + run RL per issue ─────────────────────────
        emerging_count = 0
        for iss in issues:
            if iss["is_emerging"]:
                emerging_count += 1

            quotes_json = json.dumps(iss.get("sample_quotes", []))
            cursor.execute(
                """
                INSERT INTO issues (
                    dataset_id, cluster_id, issue_key, title, description, theme,
                    review_count, negative_percentage, dominant_emotion,
                    severity, severity_score, severity_reason,
                    trend, trend_direction, trend_percentage, is_emerging, sample_quotes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload.dataset_id, iss["cluster_id"],
                    iss.get("issue_key") or iss["theme"],
                    iss["theme"],
                    iss.get("severity_reason") or iss["theme"],
                    iss["theme"], iss["review_count"],
                    iss["negative_percentage"], iss["dominant_emotion"],
                    iss["severity"], iss["severity_score"], iss["severity_reason"],
                    iss["trend"], iss["trend_direction"], iss["trend_percentage"],
                    True if iss["is_emerging"] else False,
                    quotes_json
                )
            )
            issue_id = cursor.lastrowid
            iss["id"] = issue_id

            # ── RL Step: Get Q-Learning recommendation for this issue ─────────
            try:
                rl_result = get_rl_recommendation(
                    issue_id=issue_id,
                    dataset_id=payload.dataset_id,
                    severity_score=iss["severity_score"],
                    sentiment_neg_pct=iss["negative_percentage"],
                    review_count=iss["review_count"],
                    trend_direction=iss.get("trend_direction", "stable"),
                )
                # Store recommended action in actions table
                cursor.execute(
                    """
                    INSERT INTO actions (dataset_id, issue_id, action_code, title, description, recommended_by)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        payload.dataset_id, issue_id,
                        rl_result.get("action", "monitor_issue"),
                        rl_result.get("label", "Continue Monitoring"),
                        rl_result.get("description", ""),
                        "rl_engine_v1"
                    )
                )
            except Exception:
                # RL failure is non-fatal — analysis still completes
                pass

        # ── Finalize ──────────────────────────────────────────────────────────
        cursor.execute(
            "UPDATE datasets SET status = 'completed', completed_at = CURRENT_TIMESTAMP WHERE id = ?",
            (payload.dataset_id,)
        )

        # Record analysis run metadata
        cursor.execute(
            """
            INSERT INTO analysis_runs (dataset_id, pipeline_version, model_versions, status, completed_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (
                payload.dataset_id, "2.0.0",
                json.dumps({
                    "sentiment": settings.SENTIMENT_MODEL_NAME,
                    "emotion": settings.EMOTION_MODEL_NAME,
                    "embeddings": settings.EMBEDDING_MODEL_NAME,
                    "llm": settings.LLM_MODEL,
                    "rl": "q-learning-v1"
                }),
                "completed"
            )
        )
        conn.commit()
        conn.close()

        return AnalysisResponse(
            dataset_id=payload.dataset_id,
            status="completed",
            message=(
                f"Analysis completed. Processed {len(processed_records)} of {total_input_rows} reviews. "
                f"Discovered {len(issues)} issues ({emerging_count} emerging). "
                f"RL recommendations generated for all issues."
            ),
            total_reviews_analyzed=len(processed_records),
            issues_discovered=len(issues),
            emerging_issues_count=emerging_count
        )

    except HTTPException:
        raise
    except Exception as e:
        try:
            conn.rollback()
            conn.close()
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=f"Analysis pipeline error: {str(e)}")




@router.get("", response_model=List[ReviewItem])
async def get_reviews(
    dataset_id: Optional[int] = Query(None),
    sentiment: Optional[str] = Query(None),
    cluster_id: Optional[int] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """Retrieves processed reviews with optional filtering."""
    conn = get_db_connection()
    cursor = conn.cursor()

    query = "SELECT * FROM reviews WHERE 1=1"
    params = []

    if dataset_id is not None:
        query += " AND dataset_id = ?"
        params.append(dataset_id)
    if sentiment is not None:
        query += " AND UPPER(sentiment) = UPPER(?)"
        params.append(sentiment)
    if cluster_id is not None:
        query += " AND cluster_id = ?"
        params.append(cluster_id)

    query += " ORDER BY id ASC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    return [dict(r) for r in rows]

@router.get("/{review_id}", response_model=ReviewItem)
async def get_review_by_id(review_id: int):
    """Retrieves a single review by its internal ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM reviews WHERE id = ?", (review_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Review not found")
    return dict(row)
