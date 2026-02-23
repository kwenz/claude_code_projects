# Resume Reviewer

An AI-powered resume reviewer built with FastAPI + React. Upload a PDF or DOCX resume, get inline annotated feedback, an overall score, and an enhanced rewrite — powered by **Claude** or **Gemini** (your choice).

## Features

- Upload PDF or DOCX resumes (up to 10 MB)
- Parsed into labeled sections (Experience, Education, Skills, etc.)
- Choose your AI provider: **Claude** (Anthropic) or **Gemini** (Google)
- Analysis includes:
  - Overall score (0–100) with SVG gauge
  - Summary + 4–12 inline annotations with severity highlighting
  - 3–7 prioritized improvement suggestions
- "Enhance Resume" rewrites sections for maximum impact
- Side-by-side original vs. enhanced comparison
- Results cached per provider — switch and compare without re-uploading

## Quick Start

### 1. Clone & configure

```bash
git clone <repo-url>
cd resume_reviewer
```

Copy the env file and add your API keys:

```bash
cp backend/.env.example backend/.env
# Edit backend/.env:
#   ANTHROPIC_API_KEY=sk-ant-...
#   GEMINI_API_KEY=...        (optional, only needed to use Gemini)
```

### 2. Set up the backend venv (first time only)

```bash
cd backend
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
cd ..
```

### 3. Install frontend dependencies (first time only)

```bash
cd frontend
npm install
cd ..
```

### 4. Run

```bash
python run.py
```

This starts both servers and prints the URLs:

```
  Backend:  http://localhost:8000
  Frontend: http://localhost:5173
```

Open **http://localhost:5173** in your browser. Press `Ctrl+C` to stop.

---

## Manual Start (alternative)

If you prefer to run the servers separately:

**Backend**
```bash
cd backend
PYTHONPATH=venv/lib/python3.12/site-packages venv/bin/python -m uvicorn main:app --port 8000
```

**Frontend**
```bash
cd frontend
npm run dev
```

---

## API Reference

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/upload` | Upload PDF/DOCX, returns parsed sections |
| POST | `/api/analyze` | Run analysis (`provider`: `claude` or `gemini`) |
| POST | `/api/enhance` | Run enhancement (`provider`: `claude` or `gemini`) |
| GET | `/api/health` | Health check |

## Architecture

```
Browser (React + Vite, :5173)
        │  HTTP REST
        ▼
FastAPI (:8000)
  ├── parser.py        — PDF (PyMuPDF) / DOCX (python-docx)
  ├── claude_client.py — Anthropic SDK (claude-sonnet-4-5)
  ├── gemini_client.py — Google GenAI SDK (gemini-2.5-flash)
  └── session_store.py — in-memory UUID sessions
        │
        ▼
Anthropic API  /  Google Gemini API
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | Yes | Anthropic API key — get one at console.anthropic.com |
| `GEMINI_API_KEY` | No | Google Gemini API key — get one at aistudio.google.com |
