"""
FeedbackPulse — PostgreSQL Database Layer
==========================================
All data is stored in PostgreSQL. SQLite is NOT supported.

To configure: set DATABASE_URL in backend/.env:
  DATABASE_URL=postgresql://user:password@localhost:5432/reviews_db

Then install the driver: pip install psycopg2-binary
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

import psycopg2
import psycopg2.extras

from app.config import settings


# ── PostgreSQL connection helpers ─────────────────────────────────────────────

class _DictRow(dict):
    """Row object that supports both dict-style and attribute-style access."""
    def __getitem__(self, key):
        return super().__getitem__(key)

    def get(self, key, default=None):
        return super().get(key, default)


class _PgCursor:
    """
    Cursor wrapper that:
    - Converts SQLite ? placeholders → PostgreSQL %s
    - Returns _DictRow objects (dict-like) instead of tuples
    - Captures lastrowid via RETURNING id on INSERT
    """

    def __init__(self, raw_cursor):
        self._cur = raw_cursor
        self._lastrowid = None

    def execute(self, sql: str, params=()):
        # Convert ? → %s placeholders for PostgreSQL
        pg_sql = sql.replace("?", "%s")

        # For INSERT: auto-append RETURNING id so we can capture lastrowid
        if pg_sql.strip().upper().startswith("INSERT") and "RETURNING" not in pg_sql.upper():
            pg_sql = pg_sql.rstrip().rstrip(";") + " RETURNING id"
            self._cur.execute(pg_sql, params or ())
            try:
                row = self._cur.fetchone()
                self._lastrowid = row[0] if row else None
            except Exception:
                self._lastrowid = None
        else:
            self._cur.execute(pg_sql, params or ())

    def fetchone(self) -> Optional[_DictRow]:
        try:
            row = self._cur.fetchone()
        except Exception:
            return None
        if row is None or self._cur.description is None:
            return None
        cols = [d[0] for d in self._cur.description]
        return _DictRow(zip(cols, row))

    def fetchall(self) -> List[_DictRow]:
        try:
            rows = self._cur.fetchall()
        except Exception:
            return []
        if not rows or self._cur.description is None:
            return []
        cols = [d[0] for d in self._cur.description]
        return [_DictRow(zip(cols, r)) for r in rows]

    @property
    def lastrowid(self) -> Optional[int]:
        return self._lastrowid

    def __getattr__(self, name):
        return getattr(self._cur, name)


class _PgConn:
    """
    Connection wrapper that mirrors the sqlite3 connection interface:
    .cursor(), .commit(), .rollback(), .close()
    """

    def __init__(self, raw_conn):
        self._conn = raw_conn
        self._conn.autocommit = False

    def cursor(self) -> _PgCursor:
        return _PgCursor(self._conn.cursor())

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    def close(self):
        self._conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.rollback()
        else:
            self.commit()
        self.close()


def get_db_connection() -> _PgConn:
    """
    Returns a PostgreSQL connection.
    Configure DATABASE_URL in backend/.env:
      postgresql://user:password@host:5432/dbname
    """
    dsn = settings.PG_DSN
    if not dsn or not dsn.startswith("postgresql"):
        raise RuntimeError(
            "DATABASE_URL is not set to a PostgreSQL URL.\n"
            "Set DATABASE_URL=postgresql://user:password@localhost:5432/reviews_db\n"
            "in backend/.env, then restart the server."
        )
    try:
        raw_conn = psycopg2.connect(dsn)
    except psycopg2.OperationalError as e:
        raise RuntimeError(
            f"Could not connect to PostgreSQL: {e}\n"
            "Make sure PostgreSQL is running and DATABASE_URL is correct."
        )
    return _PgConn(raw_conn)


# ── DDL helpers ───────────────────────────────────────────────────────────────

def _pg_ddl(sql: str) -> str:
    """Translate SQLite DDL syntax to PostgreSQL."""
    sql = sql.replace("INTEGER PRIMARY KEY AUTOINCREMENT", "SERIAL PRIMARY KEY")
    sql = sql.replace(" AUTOINCREMENT", "")
    sql = sql.replace(" BLOB", " BYTEA")
    sql = sql.replace("BOOLEAN DEFAULT 0", "BOOLEAN DEFAULT FALSE")
    sql = sql.replace("BOOLEAN DEFAULT 1", "BOOLEAN DEFAULT TRUE")
    return sql


def _ensure_table(cursor: _PgCursor, table_sql: str):
    """Execute CREATE TABLE IF NOT EXISTS with PostgreSQL DDL translation."""
    cursor.execute(_pg_ddl(table_sql))


# ── Demo seeding ──────────────────────────────────────────────────────────────

def _seed_demo_datasets():
    """Create default org/products/datasets if not already present."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Default organization
    cursor.execute("SELECT id FROM organizations WHERE slug = ? LIMIT 1", ("demo-org",))
    org_row = cursor.fetchone()
    if not org_row:
        cursor.execute(
            "INSERT INTO organizations (name, slug, description, is_active) VALUES (?, ?, ?, 1)",
            ("Demo Organization", "demo-org", "Default organization for FeedbackPulse demo"),
        )
        org_id = cursor.lastrowid
    else:
        org_id = org_row["id"]

    # Default products
    fintech_product_id = None
    for product_name, slug, description in [
        ("FinTech App", "demo-fintech", "Demo mobile banking and payments product"),
        ("Commerce App", "demo-commerce", "Demo e-commerce shopping experience"),
        ("Travel App", "demo-travel", "Demo travel booking and reservation flow"),
    ]:
        cursor.execute(
            "SELECT id FROM products WHERE organization_id = ? AND slug = ? LIMIT 1",
            (org_id, slug),
        )
        product_row = cursor.fetchone()
        if product_row:
            if slug == "demo-fintech":
                fintech_product_id = product_row["id"]
            continue
        cursor.execute(
            "INSERT INTO products (organization_id, name, slug, description) VALUES (?, ?, ?, ?)",
            (org_id, product_name, slug, description),
        )
        pid = cursor.lastrowid
        if slug == "demo-fintech":
            fintech_product_id = pid

    # Demo dataset stubs
    cursor.execute("SELECT filename FROM datasets WHERE is_demo = 1")
    existing = {row["filename"] for row in cursor.fetchall()}

    for filename, slug in [
        ("demo_fintech.csv", "demo-fintech"),
        ("demo_ecommerce.csv", "demo-commerce"),
        ("demo_travel.csv", "demo-travel"),
    ]:
        if filename in existing:
            continue
        cursor.execute(
            "SELECT id FROM products WHERE slug = ? LIMIT 1", (slug,)
        )
        product_row = cursor.fetchone()
        product_id = product_row["id"] if product_row else fintech_product_id
        cursor.execute(
            """
            INSERT INTO datasets
              (organization_id, product_id, filename, dataset_name,
               review_count, valid_row_count, invalid_row_count, duplicate_count,
               status, is_demo, metadata, text_col, date_col, rating_col, id_col)
            VALUES (?, ?, ?, ?, 0, 0, 0, 0, 'completed', 1, ?, 'review_text', 'date', 'rating', 'review_id')
            """,
            (
                org_id, product_id, filename,
                slug.replace("demo-", "").title(),
                json.dumps({"source": "seeded_demo_dataset"}),
            ),
        )

    conn.commit()
    conn.close()


# ── Schema init ───────────────────────────────────────────────────────────────

def init_db():
    """
    Initialize the PostgreSQL schema. Safe to call on every startup —
    uses CREATE TABLE IF NOT EXISTS and ALTER TABLE with conflict handling.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # ── Core tables ───────────────────────────────────────────────────────────

    _ensure_table(cursor, """
        CREATE TABLE IF NOT EXISTS organizations (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            slug TEXT NOT NULL UNIQUE,
            description TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    _ensure_table(cursor, """
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            organization_id INTEGER NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL DEFAULT '',
            full_name TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'PM',
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE
        )
    """)

    _ensure_table(cursor, """
        CREATE TABLE IF NOT EXISTS products (
            id SERIAL PRIMARY KEY,
            organization_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            slug TEXT NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(organization_id, slug),
            FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE
        )
    """)

    _ensure_table(cursor, """
        CREATE TABLE IF NOT EXISTS datasets (
            id SERIAL PRIMARY KEY,
            organization_id INTEGER DEFAULT 1,
            product_id INTEGER,
            filename TEXT NOT NULL,
            dataset_name TEXT,
            review_count INTEGER DEFAULT 0,
            valid_row_count INTEGER DEFAULT 0,
            invalid_row_count INTEGER DEFAULT 0,
            duplicate_count INTEGER DEFAULT 0,
            text_col TEXT,
            date_col TEXT,
            rating_col TEXT,
            id_col TEXT,
            platform_col TEXT,
            version_col TEXT,
            status TEXT DEFAULT 'uploaded',
            is_demo INTEGER DEFAULT 0,
            uploaded_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            metadata TEXT,
            FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE,
            FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE SET NULL,
            FOREIGN KEY (uploaded_by) REFERENCES users(id) ON DELETE SET NULL
        )
    """)

    _ensure_table(cursor, """
        CREATE TABLE IF NOT EXISTS reviews (
            id SERIAL PRIMARY KEY,
            dataset_id INTEGER NOT NULL,
            original_id TEXT,
            raw_text TEXT NOT NULL,
            cleaned_text TEXT NOT NULL,
            review_date TEXT,
            rating REAL,
            platform TEXT,
            app_version TEXT,
            sentiment TEXT,
            sentiment_score REAL,
            emotion TEXT,
            emotion_score REAL,
            cluster_id INTEGER,
            metadata TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (dataset_id) REFERENCES datasets(id) ON DELETE CASCADE
        )
    """)

    _ensure_table(cursor, """
        CREATE TABLE IF NOT EXISTS review_analysis (
            id SERIAL PRIMARY KEY,
            dataset_id INTEGER NOT NULL,
            review_id INTEGER NOT NULL,
            sentiment_label TEXT,
            sentiment_score REAL,
            emotion_label TEXT,
            emotion_score REAL,
            model_name TEXT,
            model_version TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (dataset_id) REFERENCES datasets(id) ON DELETE CASCADE,
            FOREIGN KEY (review_id) REFERENCES reviews(id) ON DELETE CASCADE
        )
    """)

    _ensure_table(cursor, """
        CREATE TABLE IF NOT EXISTS review_embeddings (
            id SERIAL PRIMARY KEY,
            dataset_id INTEGER NOT NULL,
            review_id INTEGER NOT NULL,
            embedding BYTEA,
            model_name TEXT,
            model_version TEXT DEFAULT 'sentence-transformers/all-MiniLM-L6-v2',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (dataset_id) REFERENCES datasets(id) ON DELETE CASCADE,
            FOREIGN KEY (review_id) REFERENCES reviews(id) ON DELETE CASCADE
        )
    """)

    _ensure_table(cursor, """
        CREATE TABLE IF NOT EXISTS clusters (
            id SERIAL PRIMARY KEY,
            dataset_id INTEGER NOT NULL,
            algorithm TEXT NOT NULL,
            cluster_count INTEGER,
            silhouette_score REAL,
            noise_ratio REAL,
            quality_score REAL,
            review_count INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (dataset_id) REFERENCES datasets(id) ON DELETE CASCADE
        )
    """)

    _ensure_table(cursor, """
        CREATE TABLE IF NOT EXISTS themes (
            id SERIAL PRIMARY KEY,
            dataset_id INTEGER NOT NULL,
            cluster_id INTEGER,
            theme_name TEXT NOT NULL,
            description TEXT,
            keywords TEXT,
            naming_method TEXT,
            confidence REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (dataset_id) REFERENCES datasets(id) ON DELETE CASCADE
        )
    """)

    _ensure_table(cursor, """
        CREATE TABLE IF NOT EXISTS issues (
            id SERIAL PRIMARY KEY,
            dataset_id INTEGER NOT NULL,
            product_id INTEGER,
            issue_key TEXT,
            title TEXT NOT NULL,
            description TEXT,
            cluster_id INTEGER NOT NULL,
            theme TEXT NOT NULL,
            review_count INTEGER NOT NULL,
            negative_percentage REAL NOT NULL,
            dominant_emotion TEXT NOT NULL,
            severity TEXT NOT NULL,
            severity_score REAL NOT NULL,
            severity_reason TEXT NOT NULL,
            trend TEXT,
            trend_direction TEXT,
            trend_percentage REAL,
            is_emerging BOOLEAN DEFAULT FALSE,
            sample_quotes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (dataset_id) REFERENCES datasets(id) ON DELETE CASCADE,
            FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE SET NULL
        )
    """)

    _ensure_table(cursor, """
        CREATE TABLE IF NOT EXISTS issue_reviews (
            id SERIAL PRIMARY KEY,
            issue_id INTEGER NOT NULL,
            review_id INTEGER NOT NULL,
            dataset_id INTEGER NOT NULL,
            similarity_score REAL,
            is_primary_evidence INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (issue_id) REFERENCES issues(id) ON DELETE CASCADE,
            FOREIGN KEY (review_id) REFERENCES reviews(id) ON DELETE CASCADE,
            FOREIGN KEY (dataset_id) REFERENCES datasets(id) ON DELETE CASCADE
        )
    """)

    _ensure_table(cursor, """
        CREATE TABLE IF NOT EXISTS issue_metrics (
            id SERIAL PRIMARY KEY,
            issue_id INTEGER NOT NULL,
            dataset_id INTEGER NOT NULL,
            metric_name TEXT NOT NULL,
            metric_value REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (issue_id) REFERENCES issues(id) ON DELETE CASCADE,
            FOREIGN KEY (dataset_id) REFERENCES datasets(id) ON DELETE CASCADE
        )
    """)

    _ensure_table(cursor, """
        CREATE TABLE IF NOT EXISTS trend_metrics (
            id SERIAL PRIMARY KEY,
            dataset_id INTEGER NOT NULL,
            issue_id INTEGER,
            period DATE,
            granularity TEXT,
            issue_rate REAL,
            growth_rate REAL,
            persistence REAL,
            trend_score REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (dataset_id) REFERENCES datasets(id) ON DELETE CASCADE,
            FOREIGN KEY (issue_id) REFERENCES issues(id) ON DELETE CASCADE
        )
    """)

    _ensure_table(cursor, """
        CREATE TABLE IF NOT EXISTS business_impact_calibrations (
            id SERIAL PRIMARY KEY,
            issue_id INTEGER NOT NULL,
            dataset_id INTEGER NOT NULL,
            default_score REAL,
            final_score REAL,
            reason TEXT,
            changed_by TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (issue_id) REFERENCES issues(id) ON DELETE CASCADE,
            FOREIGN KEY (dataset_id) REFERENCES datasets(id) ON DELETE CASCADE
        )
    """)

    _ensure_table(cursor, """
        CREATE TABLE IF NOT EXISTS pm_briefs (
            id SERIAL PRIMARY KEY,
            dataset_id INTEGER NOT NULL,
            issue_id INTEGER,
            title TEXT,
            summary TEXT,
            body TEXT,
            evidence_review_ids TEXT,
            model_name TEXT,
            model_version TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (dataset_id) REFERENCES datasets(id) ON DELETE CASCADE,
            FOREIGN KEY (issue_id) REFERENCES issues(id) ON DELETE CASCADE
        )
    """)

    _ensure_table(cursor, """
        CREATE TABLE IF NOT EXISTS actions (
            id SERIAL PRIMARY KEY,
            dataset_id INTEGER NOT NULL,
            issue_id INTEGER,
            action_code TEXT NOT NULL,
            title TEXT,
            description TEXT,
            recommended_by TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (dataset_id) REFERENCES datasets(id) ON DELETE CASCADE,
            FOREIGN KEY (issue_id) REFERENCES issues(id) ON DELETE CASCADE
        )
    """)

    _ensure_table(cursor, """
        CREATE TABLE IF NOT EXISTS outcomes (
            id SERIAL PRIMARY KEY,
            action_id INTEGER NOT NULL,
            issue_id INTEGER,
            before_metrics TEXT,
            after_metrics TEXT,
            reward REAL,
            success INTEGER DEFAULT 0,
            recorded_by TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (action_id) REFERENCES actions(id) ON DELETE CASCADE,
            FOREIGN KEY (issue_id) REFERENCES issues(id) ON DELETE CASCADE
        )
    """)

    _ensure_table(cursor, """
        CREATE TABLE IF NOT EXISTS analysis_runs (
            id SERIAL PRIMARY KEY,
            dataset_id INTEGER NOT NULL,
            pipeline_version TEXT,
            model_versions TEXT,
            status TEXT,
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            error_message TEXT,
            FOREIGN KEY (dataset_id) REFERENCES datasets(id) ON DELETE CASCADE
        )
    """)

    # ── RL Engine tables ──────────────────────────────────────────────────────

    _ensure_table(cursor, """
        CREATE TABLE IF NOT EXISTS rl_q_table (
            id SERIAL PRIMARY KEY,
            state_key TEXT NOT NULL,
            action TEXT NOT NULL,
            q_value REAL NOT NULL DEFAULT 0.0,
            visit_count INTEGER NOT NULL DEFAULT 0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(state_key, action)
        )
    """)

    _ensure_table(cursor, """
        CREATE TABLE IF NOT EXISTS rl_feedback (
            id SERIAL PRIMARY KEY,
            issue_id INTEGER NOT NULL,
            dataset_id INTEGER NOT NULL,
            action_taken TEXT NOT NULL,
            reward REAL NOT NULL DEFAULT 0.0,
            state_snapshot TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (issue_id) REFERENCES issues(id) ON DELETE CASCADE,
            FOREIGN KEY (dataset_id) REFERENCES datasets(id) ON DELETE CASCADE
        )
    """)

    # ── LLM Insight cache ─────────────────────────────────────────────────────

    _ensure_table(cursor, """
        CREATE TABLE IF NOT EXISTS llm_insights (
            id SERIAL PRIMARY KEY,
            issue_id INTEGER NOT NULL,
            dataset_id INTEGER NOT NULL,
            executive_summary TEXT,
            root_cause_hypothesis TEXT,
            recommended_action TEXT,
            why_it_matters TEXT,
            priority_score REAL,
            evidence_review_ids TEXT,
            model_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (issue_id) REFERENCES issues(id) ON DELETE CASCADE,
            FOREIGN KEY (dataset_id) REFERENCES datasets(id) ON DELETE CASCADE
        )
    """)

    # ── Indexes ───────────────────────────────────────────────────────────────
    conn.commit()

    for index_sql in [
        "CREATE INDEX IF NOT EXISTS idx_reviews_dataset ON reviews(dataset_id)",
        "CREATE INDEX IF NOT EXISTS idx_reviews_cluster ON reviews(cluster_id)",
        "CREATE INDEX IF NOT EXISTS idx_issues_dataset ON issues(dataset_id)",
        "CREATE INDEX IF NOT EXISTS idx_issues_severity ON issues(severity_score DESC)",
        "CREATE INDEX IF NOT EXISTS idx_datasets_org ON datasets(organization_id)",
        "CREATE INDEX IF NOT EXISTS idx_issue_reviews_issue ON issue_reviews(issue_id)",
        "CREATE INDEX IF NOT EXISTS idx_trend_metrics_dataset ON trend_metrics(dataset_id)",
        "CREATE INDEX IF NOT EXISTS idx_analysis_runs_dataset ON analysis_runs(dataset_id)",
        "CREATE INDEX IF NOT EXISTS idx_rl_q_table_state ON rl_q_table(state_key)",
        "CREATE INDEX IF NOT EXISTS idx_llm_insights_issue ON llm_insights(issue_id)",
    ]:
        try:
            cursor.execute(index_sql)
            conn.commit()
        except Exception:
            try:
                conn.commit()
            except Exception:
                pass

    conn.commit()
    conn.close()

    _seed_demo_datasets()


if __name__ == "__main__":
    init_db()
    print("PostgreSQL database initialized successfully.")
    print("Connection:", settings.PG_DSN.split("@")[-1])  # safe: shows only host/dbname
