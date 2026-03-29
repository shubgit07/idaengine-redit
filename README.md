# RedEngine

Backend service for collecting Reddit posts and extracting structured pain points with an OpenAI-compatible API.

## Project Layout

- `backend/app`: FastAPI app code (API, services, DB models, schemas)
- `backend/scripts/ingest.py`: ingestion pipeline entrypoint
- `backend/requirements.txt`: Python dependencies

## Local Setup

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r backend/requirements.txt
```

3. Create env file:

```powershell
Copy-Item backend/.env.example backend/.env
```

4. Run API (from repo root):

```powershell
Set-Location backend
uvicorn app.main:app --reload
```

## GitHub Push Checklist

- Keep secrets only in `backend/.env` (ignored by `.gitignore`).
- Do not commit local DB files like `backend/app.db`.
- If `backend/.env` was ever committed in a previous repository history, rotate the API key and untrack the file:

```powershell
git rm --cached backend/.env
```
- Initialize git in repo root (if not already):

```bash
git init
git add .
git commit -m "Initial commit"
```
