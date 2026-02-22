# Resume Reviewer

An AI-powered resume reviewer built with FastAPI + React. Upload a PDF or DOCX resume, get inline annotated feedback, an overall score, and an enhanced rewrite — all powered by Claude.

## Features

- Upload PDF or DOCX resumes (up to 10 MB)
- Parsed into labeled sections (Experience, Education, Skills, etc.)
- Claude analyzes and returns:
  - Overall score (0–100) with SVG gauge
  - Summary + 4–12 inline annotations with severity highlighting
  - 3–7 prioritized improvement suggestions
- "Enhance Resume" rewrites sections for maximum impact
- Side-by-side original vs. enhanced comparison
- Download enhanced resume as plain text

## Quick Start

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env and set ANTHROPIC_API_KEY=sk-ant-...

uvicorn main:app --reload
# API available at http://localhost:8000
# Health check: http://localhost:8000/api/health
```

### Frontend

```bash
cd frontend
npm install
npm run dev
# App available at http://localhost:5173
```

## API Reference

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/upload` | Upload PDF/DOCX, returns parsed sections |
| POST | `/api/analyze` | Run Claude analysis, returns score + annotations |
| POST | `/api/enhance` | Run Claude enhancement, returns rewritten sections |
| GET | `/api/health` | Health check |

## Architecture

```
Browser (React + Vite, :5173)
        │  HTTP REST
        ▼
FastAPI (:8000)
  ├── parser.py      — PDF (PyMuPDF) / DOCX (python-docx)
  ├── claude_client.py — Anthropic SDK calls
  └── session_store.py — in-memory UUID sessions
        │
        ▼
Anthropic Claude API (claude-sonnet-4-5)
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `ANTHROPIC_API_KEY` | Your Anthropic API key |
