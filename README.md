# Search-Based Entity Resolution Pipeline

This project provides a **Search-Based Product Matching** workflow with:
- **Backend**: Python + FastAPI mock pipeline APIs
- **Frontend**: React + Vite + TypeScript dashboard UI

## 1) Backend setup (FastAPI)

```bash
cd /home/runner/work/Paper_boat/Paper_boat
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload
```

Backend runs at: `http://localhost:8000`

## 2) Frontend setup (React/Vite)

Open a new terminal:

```bash
cd /home/runner/work/Paper_boat/Paper_boat/frontend
npm install
npm run dev
```

Frontend runs at: `http://localhost:5173`

## 3) Run both services concurrently

- Terminal 1: run FastAPI (`uvicorn backend.main:app --reload`)
- Terminal 2: run Vite (`npm run dev`)

Then use the dashboard to submit a product and trigger `/api/evaluate-match`.

## API endpoints

- `POST /api/products`: mock-save a base product payload.
- `GET /api/generate-url?name=...&brand=...`: create Amazon AE + Noon search URLs.
- `POST /api/evaluate-match`: simulate scraping 3 results + return structured LLM-style match evaluation.
