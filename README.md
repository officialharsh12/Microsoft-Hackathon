# 🔍 FeedbackPulse — AI Review Intelligence Platform

> **Microsoft Hackathon 2026** · Built with Azure AI · Powered by RL + LLM + HuggingFace Transformers

[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-blue)](https://react.dev/)
[![PostgreSQL](https://img.shields.io/badge/Database-PostgreSQL-336791?logo=postgresql)](https://www.postgresql.org/)
[![Azure OpenAI](https://img.shields.io/badge/LLM-Azure%20OpenAI-0078D4?logo=microsoft)](https://azure.microsoft.com/en-us/products/ai-services/openai-service)

---

## 📌 Table of Contents

1. [Overview](#1-overview)
2. [AI / ML Architecture](#2-ai--ml-architecture)
3. [Tech Stack](#3-tech-stack)
4. [Project Structure](#4-project-structure)
5. [Setup & Installation](#5-setup--installation)
6. [Database Configuration (PostgreSQL)](#6-database-configuration-postgresql)
7. [How to Use the Application](#7-how-to-use-the-application)
8. [Uploading External Data](#8-uploading-external-data)
9. [API Reference](#9-api-reference)
10. [Where Is Data Stored?](#10-where-is-data-stored)

---

## 1. Overview

**FeedbackPulse** is an end-to-end, AI-powered product review intelligence platform built for **Product Managers**. It ingests customer review datasets (from app stores, surveys, CRM exports, etc.), runs a multi-stage AI pipeline, and surfaces actionable insights through:

- 📊 **Executive Dashboard** — KPI cards, sentiment distribution, emotion radar, emerging issue alerts
- 🚨 **Emerging Issue Radar** — Detects accelerating negative clusters before they go viral
- 🧠 **Explainable Issue Detection** — Every issue comes with a *Why This Was Detected* breakdown
- 📋 **Executive PM Brief** — One-click AI-generated PM document with root-cause hypotheses and recommendations
- 🤖 **RL Recommendation Engine** — Learns which PM actions (Prioritize / Investigate / Monitor / Fix) have the best outcome for a given issue type

---

## 2. AI / ML Architecture

The system runs a **5-stage inference pipeline** when a dataset is submitted:

```
CSV Upload → Preprocessing → Sentiment → Emotion → Embeddings → Clustering → Issue Aggregation → PostgreSQL
                                                                                     ↓
                                                                         RL Engine + LLM PM Brief
```

### 2.1 NLP Models (HuggingFace Transformers)

| Role | Model | Parameters | Source |
|---|---|---|---|
| **Sentiment Analysis** | `distilbert-base-uncased-finetuned-sst-2-english` | 66M | HuggingFace Hub |
| **Emotion Classification** | `SamLowe/roberta-base-go_emotions` | 125M (RoBERTa) | HuggingFace Hub |
| **Sentence Embeddings** | `sentence-transformers/all-MiniLM-L6-v2` | 22M | HuggingFace Hub |

- All models run locally on CPU / Apple MPS / CUDA (auto-detected at startup).
- Inference is batched (`BATCH_SIZE=32` by default, configurable via `.env`).
- Models process **all reviews** in the uploaded dataset with **no row limit**.

### 2.2 Clustering

| Component | Algorithm | Details |
|---|---|---|
| **Review Clustering** | HDBSCAN / KMeans | Groups semantically similar reviews into clusters using MiniLM embeddings |
| **Embedding Store** | BLOB/BYTEA in PostgreSQL | Serialized `float32` numpy arrays stored per-review for retrieval |

### 2.3 Issue Aggregation & Severity Engine

Each cluster is scored using a multi-factor severity formula:

```
Severity Score = 0.4 × (negative%) + 0.3 × (log-normalized volume) + 0.3 × (trend velocity)
```

- **Severity Labels**: CRITICAL · HIGH · MEDIUM · LOW
- **Trend Detection**: Compares review volume in the last 7 days vs. prior 14 days to flag emerging issues
- **Theme Discovery**: TF-IDF + keyword extraction over clustered review texts

### 2.4 Reinforcement Learning Engine

> `backend/app/services/rl_engine.py`

A **tabular Q-Learning / Contextual Bandit** engine that recommends which PM action to take for each issue:

| Hyperparameter | Value | Description |
|---|---|---|
| Learning Rate (α) | 0.10 | Step size for Q-value updates |
| Discount Factor (γ) | 0.95 | How much future rewards matter |
| Exploration (ε) | 0.15 | 15% random exploration to discover new actions |
| Initial Q-value | 0.0 | Unbiased start |

**State Encoding** encodes:
- Issue severity (critical / high / medium / low)
- Sentiment distribution bucket
- Review volume bucket (log-scale)
- Trend direction (rising / stable / falling)
- Customer impact estimate

**Action Space:**
| Action | Description |
|---|---|
| `prioritize_issue` | Escalate to top of sprint backlog |
| `monitor_issue` | Watch trend — no immediate action needed |
| `investigate_issue` | Assign engineering triage / root-cause analysis |
| `fix_issue` | Deploy immediate hotfix or patch |

**Reward Signal:** +1 when the issue severity improves after the recommended action; −1 when it worsens. Q-values are persisted in the `rl_q_table` PostgreSQL table and improve over repeated use.

### 2.5 LLM — Azure OpenAI (PM Brief Generator)

> `backend/app/services/llm_reasoning.py` · `backend/app/services/pm_brief.py`

| Property | Value |
|---|---|
| **Provider** | Azure OpenAI (configurable to any OpenAI-compatible endpoint) |
| **Default Model** | `gpt-4o-mini` |
| **Function** | Generates structured PM Brief: Problem Statement · Impact Signals · Customer Voice · Root-Cause Hypotheses · Action Items |
| **Fallback** | If no Azure credentials are set, brief generation returns a structured template-based fallback |

The LLM is given:
- Issue cluster theme and severity
- Top customer verbatim quotes
- Sentiment + emotion distribution
- RL-recommended action
- Review trend data

And outputs a production-ready executive brief document.

---

## 3. Tech Stack

### Backend
| Layer | Technology |
|---|---|
| **API Framework** | FastAPI (Python 3.11+) |
| **Database** | **PostgreSQL** (primary) / SQLite (zero-config local fallback) |
| **DB Driver** | psycopg2-binary (PostgreSQL) / sqlite3 stdlib (SQLite) |
| **NLP / ML** | HuggingFace Transformers, Sentence-Transformers, scikit-learn |
| **RL Engine** | Custom Q-Learning (tabular), stored in `rl_q_table` DB table |
| **LLM** | Azure OpenAI GPT-4o-mini via REST |
| **Auth** | JWT (PyJWT) + bcrypt password hashing |
| **Server** | Uvicorn (ASGI) |

### Frontend
| Layer | Technology |
|---|---|
| **Framework** | React 18 + Vite |
| **Charts** | Recharts |
| **Icons** | Lucide React |
| **Styling** | Vanilla CSS + Inline styles (no Tailwind) |
| **Auth Storage** | Browser `localStorage` (JWT token + user profile) |

---

## 4. Project Structure

```
Microsoft-Hackathon-main/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── auth.py          # JWT login / register
│   │   │   ├── reviews.py       # CSV upload + full-data AI analysis pipeline
│   │   │   ├── issues.py        # Issue CRUD + PM Brief trigger
│   │   │   ├── dashboard.py     # Aggregated KPIs and chart data
│   │   │   ├── datasets.py      # Dataset management
│   │   │   └── intelligence.py  # RL recommendations endpoint
│   │   ├── services/
│   │   │   ├── preprocessing.py  # Text cleaning, PII redaction, normalization
│   │   │   ├── clustering.py     # HDBSCAN/KMeans clustering on embeddings
│   │   │   ├── issue_engine.py   # Issue aggregation from clusters
│   │   │   ├── severity.py       # Multi-factor severity scoring
│   │   │   ├── trends.py         # Trend velocity and emerging issue detection
│   │   │   ├── theme_discovery.py# TF-IDF keyword extraction per cluster
│   │   │   ├── evidence.py       # Grounded supporting quotes retrieval
│   │   │   ├── rl_engine.py      # Q-Learning RL recommendation engine
│   │   │   ├── llm.py            # Azure OpenAI client wrapper
│   │   │   ├── llm_reasoning.py  # LLM context building + insight caching
│   │   │   └── pm_brief.py       # Executive PM Brief generator
│   │   ├── config.py             # Settings (DATABASE_URL, model names, API keys)
│   │   ├── database.py           # Dual SQLite/PostgreSQL adapter + schema init
│   │   └── main.py               # FastAPI app + router mounts + DB init
│   ├── data/
│   │   └── demo_reviews.csv      # 100 demo reviews for instant testing
│   ├── requirements.txt
│   └── .env.example              # Environment variable template
└── frontend/
    ├── src/
    │   ├── pages/
    │   │   ├── LandingPage.jsx   # Auth modal + auto-fill demo credentials
    │   │   ├── UploadPage.jsx    # CSV upload + demo data loader
    │   │   ├── DashboardPage.jsx # Main analytics dashboard
    │   │   ├── IssueDetailPage.jsx
    │   │   └── PMBriefPage.jsx   # Executive AI-generated brief
    │   ├── context/AuthContext.jsx
    │   └── services/api.js       # Axios API client
    └── index.html
```

---

## 5. Setup & Installation

### Prerequisites
- Python 3.11+
- Node.js 18+
- **PostgreSQL 14+** (recommended) — or skip for SQLite fallback

### Backend Setup

```bash
# Navigate to backend
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install PostgreSQL driver
pip install psycopg2-binary

# Copy and configure environment
cp .env.example .env
# → Edit .env and set your DATABASE_URL, Azure OpenAI keys, etc.

# Start FastAPI server (auto-initializes DB schema on first run)
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend Setup

```bash
# In a separate terminal
cd frontend

# Install packages
npm install

# Start dev server
npm run dev
```

Open **`http://localhost:5173`** in your browser.

---

## 6. Database Configuration (PostgreSQL)

### Why PostgreSQL?

PostgreSQL is the **recommended production database** for FeedbackPulse because:
- Supports large-scale review datasets (10,000+ reviews) without performance degradation
- Provides ACID transactions during concurrent analysis runs
- `BYTEA` type efficiently stores serialized embedding vectors
- RL Q-table updates benefit from row-level locking
- Native `RETURNING id` clause ensures reliable INSERT tracking

### Setup Steps

**1. Create the database**
```sql
-- Run in psql
CREATE DATABASE reviews_db;
```

**2. Configure `.env`**
```env
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/reviews_db
```

**3. Install the driver**
```bash
pip install psycopg2-binary
```

**4. Start the backend** — schema is auto-created on first run via `init_db()`.

### SQLite Fallback (Zero Setup)

If `DATABASE_URL` is not set (or set to `sqlite://...`), the app automatically falls back to SQLite at `backend/data/reviews.db`. This is convenient for local development and quick demos but **not recommended for production**.

The `database.py` adapter auto-translates all SQL at runtime:

| SQLite Syntax | PostgreSQL Equivalent |
|---|---|
| `INTEGER PRIMARY KEY AUTOINCREMENT` | `SERIAL PRIMARY KEY` |
| `?` placeholders | `%s` placeholders |
| `BLOB` column type | `BYTEA` column type |
| `sqlite3.OperationalError` on duplicate column | Caught as generic `Exception` |

---

## 7. How to Use the Application

1. **Sign In with Demo Credentials**
   - Click **Sign In** on the landing page.
   - Click **"Auto-Fill Demo Credentials"** and then **Sign In**.
   - Credentials: `demo@microsoft.com` / `hackathon2026`
   - Your session is stored in browser `localStorage` (JWT token + profile).

2. **Upload Dataset or Use 100 Demo Reviews**
   - Navigate to **Upload & Analyze**.
   - Click **"Load 100 Demo Reviews"** for instant one-click loading, OR
   - Upload **your own CSV file** — any size, any number of columns. The pipeline processes **every row** with no limit.
   - Column auto-detection identifies review text, date, rating, and review ID columns automatically.

3. **Run AI Pipeline**
   - Click **"Start AI Review Analysis"**.
   - Watch the live pipeline stepper: Preprocessing → Sentiment → Emotion → Embeddings → Clustering → Issue Aggregation.
   - All reviews in your file are analyzed.

4. **Executive Dashboard**
   - KPI Cards: Total Reviews, Positive %, Negative %, High Severity Issues, Emerging Issues
   - 🚨 **Emerging Issue Radar**: Issues trending upward in the last 7 days
   - GoEmotions bar chart: Distribution across 28 emotion categories
   - Sentiment Balance donut chart
   - Review Timeline line chart

5. **Inspect Issue Details & Evidence**
   - Click any issue card to open its full detail view.
   - Read the **"Why This Issue Was Detected"** explainable diagnostic.
   - Browse verbatim customer quotes with sentiment confidence, emotion, date, rating, and platform metadata.
   - See the **RL-recommended PM action** for this issue.

6. **Generate Executive PM Brief**
   - Click **"Generate Executive Report"** in the dashboard sidebar to create a brief for the top-severity issue, OR
   - Click **"Generate Executive PM Brief"** in any issue detail page for that specific issue.
   - The brief includes: Problem Statement · Impact Signals · Customer Voice · Engineering Hypotheses · Recommended Actions.

---

## 8. Uploading External Data

FeedbackPulse accepts **any CSV file** with at least one text column. No rigid schema is required.

### Column Auto-Detection

The system automatically identifies:

| Column Type | Auto-detected names |
|---|---|
| Review text | `review_text`, `text`, `content`, `review`, `comment`, `feedback`, `body` |
| Date | `date`, `review_date`, `created_at`, `timestamp`, `time` |
| Rating | `rating`, `stars`, `score`, `star_rating` |
| Review ID | `review_id`, `id`, `item_id`, `uid` |

### Processing All Data

- **No row limit**: The analysis pipeline reads and processes every row in your CSV.
- Large files (10,000+ reviews) are processed in batches of 32 (configurable via `BATCH_SIZE` in `.env`).
- Memory-efficient batched inference prevents OOM on large datasets.

### PII Handling

The `preprocessing.py` service applies basic PII redaction:
- Email addresses → `[EMAIL]`
- Phone numbers → `[PHONE]`
- URLs → `[URL]`

### Supported Platforms

External data from any source is accepted: App Store, Google Play, Trustpilot, G2, Salesforce, Zendesk, custom CSV exports.

---

## 9. API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Health check + loaded model info |
| `POST` | `/api/auth/login` | JWT login |
| `POST` | `/api/auth/register` | Register new user |
| `POST` | `/api/reviews/upload` | Upload CSV, detect columns |
| `POST` | `/api/reviews/upload-demo` | Load 100-row demo dataset |
| `POST` | `/api/reviews/analyze` | Run end-to-end AI pipeline on **all rows** |
| `GET` | `/api/reviews` | Paginated review list with filters |
| `GET` | `/api/dashboard` | KPIs, charts, emerging radar |
| `GET` | `/api/issues` | Filterable issue list |
| `GET` | `/api/issues/{id}` | Issue detail + timeline |
| `GET` | `/api/issues/{id}/evidence` | Grounded verbatim customer quotes |
| `GET` | `/api/issues/{id}/brief` | Generate Executive PM Brief (LLM) |
| `GET` | `/api/intelligence/recommendation/{id}` | RL-recommended PM action |
| `POST` | `/api/intelligence/feedback` | Submit action outcome (RL reward signal) |

Full interactive API docs available at **`http://localhost:8000/docs`**.

---

## 10. Where Is Data Stored?

| Data | Storage Location | Notes |
|---|---|---|
| User accounts & passwords | `users` table (PostgreSQL) | bcrypt-hashed passwords; plaintext never stored |
| JWT session token | Browser `localStorage` key `feedbackpulse_token` | Expires; cleared on logout |
| User profile | Browser `localStorage` key `feedbackpulse_user` | Name, role, avatar — not sensitive |
| Uploaded CSV files | `backend/data/upload_<filename>.csv` (disk) | Retained for re-analysis; deletable |
| Processed reviews | `reviews` table (PostgreSQL) | Cleaned text, sentiment, emotion, cluster |
| Sentence embeddings | `review_embeddings` table (PostgreSQL) | Serialized `float32` BYTEA vectors |
| Detected issues | `issues` table (PostgreSQL) | Severity, theme, trend, sample quotes |
| RL Q-table | `rl_q_table` table (PostgreSQL) | Q-values persist and improve over time |
| LLM insight cache | `llm_insights` table (PostgreSQL) | Cached PM brief responses per issue |
| Demo reviews | `backend/data/demo_reviews.csv` | 100 pre-labelled reviews, always available |

---

## 11. Environment Variables Reference

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./data/reviews.db` | **Set to PostgreSQL URL for production** |
| `AUTH_SECRET` | `dev-secret-change-me` | JWT signing secret — **change in production** |
| `LLM_PROVIDER` | `azure-openai` | LLM backend provider |
| `LLM_MODEL` | `gpt-4o-mini` | Azure OpenAI model deployment name |
| `LLM_API_KEY` | _(empty)_ | Azure OpenAI API key |
| `AZURE_OPENAI_ENDPOINT` | _(empty)_ | Azure OpenAI endpoint URL |
| `AZURE_OPENAI_DEPLOYMENT` | _(empty)_ | Azure OpenAI deployment name |
| `SENTIMENT_MODEL_NAME` | `distilbert-base-uncased-finetuned-sst-2-english` | HuggingFace sentiment model |
| `EMOTION_MODEL_NAME` | `SamLowe/roberta-base-go_emotions` | HuggingFace emotion model |
| `EMBEDDING_MODEL_NAME` | `sentence-transformers/all-MiniLM-L6-v2` | Sentence embedding model |
| `BATCH_SIZE` | `32` | Inference batch size (increase for GPU) |
| `DEVICE` | `auto` | `cpu`, `cuda`, `mps`, or `auto` |

---

## 12. Demo Credentials

| Field | Value |
|---|---|
| Email | `demo@microsoft.com` |
| Password | `hackathon2026` |

Use the **"Auto-Fill Demo Credentials"** button on the Sign In modal for one-click access.

---

*Built for the Microsoft Hackathon 2026 · FeedbackPulse Team*
