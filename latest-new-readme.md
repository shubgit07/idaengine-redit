# RedEngine - Full Stack Project Documentation

Last updated: April 10, 2026

RedEngine is a full-stack project that discovers startup pain points from Reddit, scores them, stores them in SQLite, and exposes them in a filterable dashboard.

## Table of Contents

- [Overview](#overview)
- [Current Implementation Status](#current-implementation-status)
- [Tech Stack](#tech-stack)
- [Architecture and Data Flow](#architecture-and-data-flow)
- [Repository Structure](#repository-structure)
- [Backend Setup](#backend-setup)
- [Frontend Setup](#frontend-setup)
- [Running the System](#running-the-system)
- [Environment Variables](#environment-variables)
- [Backend Scripts](#backend-scripts)
- [API Reference](#api-reference)
- [Data Model](#data-model)
- [Scoring Logic](#scoring-logic)
- [Frontend Dashboard Behavior](#frontend-dashboard-behavior)
- [Operational Notes and Troubleshooting](#operational-notes-and-troubleshooting)
- [Known Gaps](#known-gaps)

## Overview

RedEngine currently implements a 3-step pipeline:

1. Fetch Reddit posts from target subreddits and store only new posts.
2. Analyze pending posts with an LLM to extract 1-2 structured pain points.
3. Serve stored pain points through FastAPI and render them in a Next.js dashboard.

Core behavior in the current codebase:

- Reddit fetch is asynchronous, rate-limit aware, and retries transient failures.
- LLM extraction validates and normalizes output to a strict schema.
- Pain points are deduplicated by `(reddit_id, pain_point)` and updated when re-analyzed.
- Scores are computed from severity, emotional intensity, willingness to pay, confidence, and Reddit engagement.
- Frontend consumes a local Next.js API route that proxies to the backend.

## Current Implementation Status

Implemented and working in code:

- Backend FastAPI app with:
  - `GET /` health endpoint
  - `GET /pain-points/` listing endpoint
- SQLite persistence via SQLAlchemy async engine
- Ingestion pipeline (`scripts/ingest.py`) currently configured for:
  - subreddits: `Entrepreneur`, `startups`, `SaaS`, `smallbusiness`
  - limit: `5` posts per subreddit
  - sequential subreddit fetches with anti-burst delays
- Analysis pipeline (`scripts/analyze_posts.py`) currently configured for:
  - batch size: `5`
  - statuses: `pending` by default, `pending+failed` with `--reprocess-failed`
  - per-post status transitions: `pending -> processing -> done|failed`
- LLM extraction with schema normalization, duplicate suppression, and max-2 pain points per post
- Category normalization and inference in both persistence flow and API response shaping
- Score recomputation script (`scripts/recompute_scores.py`) with current `score_version = v3`
- Next.js dashboard with URL-synced controls:
  - search
  - category multi-filter
  - severity multi-filter
  - sort (`latest`, `highest_score`)
  - loading, error, retry, and empty states

## Tech Stack

### Backend

- FastAPI
- SQLAlchemy 2.x (async)
- SQLite (`aiosqlite`)
- HTTPX (HTTP/2 enabled)
- Pydantic v2
- python-dotenv

### Frontend

- Next.js 16 (App Router)
- React 19
- Tailwind CSS

## Architecture and Data Flow

```text
Reddit (JSON endpoint)
  -> RedditService (with retry/backoff)
  -> fallback to Reddit RSS on 403
  -> save_posts() to reddit_posts (new rows only)
  -> analysis_status = pending

analyze_posts.py
  -> picks pending (or pending+failed) in batches
  -> llm_service.analyze_post()
     -> chunking_service.chunk_text()
     -> OpenAI-compatible chat/completions
     -> parse/normalize/dedupe/limit to max 2 pain points
     -> compute engagement + final score
  -> save_pain_points() insert/update
  -> mark post as done or failed

FastAPI
  -> GET /pain-points/
  -> joins pain_points + reddit_posts
  -> returns enriched payload

Next.js frontend
  -> GET /api/pain-points (route handler proxy)
  -> calls backend /pain-points/
  -> renders dashboard cards + controls
```

## Repository Structure

```text
backend/
  requirements.txt
  .env.example
  app/
    main.py
    api/pain_points.py
    core/retry.py
    db/base.py
    db/session.py
    models/
      __init__.py
      reddit_post.py
      pain_point.py
    schemas/
      reddit.py
      pain_point.py
    services/
      reddit_service.py
      reddit_persistence.py
      llm_service.py
      chunking_service.py
      pain_point_persistence.py
      scoring_service.py
  scripts/
    ingest.py
    analyze_posts.py
    recompute_scores.py

frontend/
  package.json
  .env.example
  app/
    layout.jsx
    page.jsx
    api/pain-points/route.js
  components/
  hooks/usePainPoints.js
  lib/api.js
  lib/dashboardControls.js
  lib/painPointModel.js
```

## Backend Setup

From repository root:

```powershell
Set-Location backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `backend/.env`:

```env
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini
OPENAI_BASE_URL=https://api.openai.com/v1
```

## Frontend Setup

From repository root:

```powershell
Set-Location frontend
npm install
Copy-Item .env.example .env.local
```

`frontend/.env.local` supports:

```env
BACKEND_API_BASE_URL=http://127.0.0.1:8000
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

Both are optional. If missing, frontend defaults to `http://127.0.0.1:8000`.

## Running the System

Use separate terminals.

1. Run backend API:

```powershell
Set-Location backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload
```

2. Ingest Reddit posts:

```powershell
Set-Location backend
.\.venv\Scripts\Activate.ps1
python scripts/ingest.py
```

3. Analyze pending posts with LLM:

```powershell
Set-Location backend
.\.venv\Scripts\Activate.ps1
python scripts/analyze_posts.py
```

Optional retry for failed analyses:

```powershell
python scripts/analyze_posts.py --reprocess-failed
```

4. Run frontend:

```powershell
Set-Location frontend
npm run dev
```

5. Open dashboard:

- Frontend: http://127.0.0.1:3000
- Backend docs: http://127.0.0.1:8000/docs

## Environment Variables

### Backend (`backend/.env`)

- `OPENAI_API_KEY` (required for analysis)
- `OPENAI_MODEL` (default `gpt-4o-mini`)
- `OPENAI_BASE_URL` (default `https://api.openai.com/v1`)

### Frontend (`frontend/.env.local`)

- `BACKEND_API_BASE_URL` (server route target)
- `NEXT_PUBLIC_API_BASE_URL` (fallback target)

## Backend Scripts

### `scripts/ingest.py`

- Initializes DB tables and lightweight schema upgrades via `init_db()`.
- Fetches top posts from:
  - `Entrepreneur`
  - `startups`
  - `SaaS`
  - `smallbusiness`
- Uses limit `5` posts per subreddit in current script.
- Inserts only new posts and sets `analysis_status = pending`.

### `scripts/analyze_posts.py`

- Batch size: `5` posts.
- Selects by status:
  - default: `pending`
  - with `--reprocess-failed`: `pending` and `failed`
- Marks each post as `processing`, then `done` or `failed`.
- On failure stores truncated error message in `last_error`.

### `scripts/recompute_scores.py`

- Recalculates engagement and final score for all existing pain points.
- Does not call the LLM.
- Sets `score_version = v3`.

## API Reference

### Backend API

#### `GET /`

Health check.

Response:

```json
{
  "status": "ok"
}
```

#### `GET /pain-points/`

Returns pain points joined with Reddit post metadata, ordered by newest pain point row first.

Response item shape:

```json
{
  "id": 1,
  "reddit_id": "abc123",
  "subreddit": "r/startups",
  "post_title": "...",
  "post_url": "https://...",
  "pain_point": "...",
  "pain_point_headline": "...",
  "category": "general",
  "severity": "high",
  "emotional_intensity": 0.82,
  "willingness_to_pay": 0.67,
  "confidence": 0.9,
  "engagement_score": 0.58,
  "score": 78.2,
  "score_version": "v3",
  "score_reason": null,
  "created_at": "2026-04-02T10:22:30Z"
}
```

### Frontend API Route

#### `GET /api/pain-points`

- Implemented in Next.js route handler.
- Proxies request to backend `GET /pain-points/`.
- Returns `502` with message when backend is unreachable.

## Data Model

### Table: `reddit_posts`

- `id` (PK, int, autoincrement)
- `reddit_id` (unique, indexed)
- `subreddit`
- `title`
- `post_body`
- `upvotes`
- `num_comments`
- `url`
- `created_utc`
- `analysis_status` (indexed, default `pending`)
- `analyzed_at` (nullable)
- `last_error` (nullable)
- `inserted_at` (server timestamp)

### Table: `pain_points`

- `id` (PK, int, autoincrement)
- `reddit_id` (FK -> `reddit_posts.reddit_id`, indexed)
- `pain_point`
- `pain_point_headline`
- `category` (indexed)
- `severity` with check constraint: `low | medium | high`
- `emotional_intensity`
- `willingness_to_pay`
- `confidence`
- `engagement_score`
- `score`
- `score_version`
- `score_reason` (nullable)
- `created_at` (server timestamp)

## Scoring Logic

Current weighted score (0-100):

- Severity: 30%
- Emotional intensity: 20%
- Willingness to pay: 20%
- Confidence: 10%
- Engagement score: 20%

Severity mapping:

- `low` -> `0.33`
- `medium` -> `0.66`
- `high` -> `1.0`

Engagement score is derived from Reddit activity using log scaling on upvotes and comments, then normalized to `[0, 1]`.

## Frontend Dashboard Behavior

Implemented controls and rendering behavior:

- Search across headline, title, pain point text, subreddit, category
- Severity multi-filter (`high`, `medium`, `low`)
- Category multi-filter (derived dynamically from loaded data)
- Sort options:
  - latest
  - highest score
- URL-synced filters via query parameters (`search`, `category`, `severity`, `sort`)
- Loading skeletons, retryable error state, empty state

## Operational Notes and Troubleshooting

### API starts but `/pain-points/` fails with DB errors

Run ingestion once to initialize/upgrade tables:

```powershell
Set-Location backend
python scripts/ingest.py
```

### Analysis script returns no extracted items

Check:

- `OPENAI_API_KEY` exists and is valid
- `OPENAI_BASE_URL` and `OPENAI_MODEL` are correct
- Failed rows in `reddit_posts.last_error`

### Reddit fetch intermittently fails

Current implementation already includes:

- retry with exponential backoff
- handling of HTTP 429 via `Retry-After`
- RSS fallback when JSON endpoint returns 403

### Frontend cannot reach backend

- Ensure backend is running on expected host/port
- Set `BACKEND_API_BASE_URL` in `frontend/.env.local`
- Restart `npm run dev` after env changes

## Known Gaps

- No automated test suite in repository yet.
- No formal migration framework (schema updates are handled by runtime column checks in `init_db`).
- API currently exposes read-only pain point listing and root health endpoint only.
- No pagination/cursor support on `GET /pain-points/` yet.
- Database path is currently fixed to local SQLite (`sqlite+aiosqlite:///./app.db`) in backend session config.

