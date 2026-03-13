# 🧠 AI Research Paper Feed

A web application that fetches daily research papers from arXiv, analyzes them with an LLM, and surfaces the most interesting ones through a clean Streamlit interface.

## Features

- 📊 **Daily Feed** — papers organized by announcement date, top-scored ones shown first
- 🏆 **Ranked Feed** — best papers of the current calendar year per arXiv category
- 🗄️ **Database Viewer** — browse all stored papers, filter by field, analyze or reanalyze individual papers
- 🤖 **LLM Scoring** — papers rated 1–10 with explanations and key insights; scores calibrated across batches
- ⚠️ **Fallback detection** — papers scored via keyword fallback (when LLM fails) are flagged and can be reanalyzed
- 🔌 **arXiv API** — fetches papers by announcement date, newest-first, up to `MAX_PAPERS_LOOKBACK` total
- 🗃️ **SQLite storage** — persistent local database with automatic schema migrations
- 🔑 **Multi-provider LLM** — supports Google Gemini, OpenAI, and Hugging Face

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure your LLM provider** — copy `env_example.txt` to `.env` and fill in:

   **Google Gemini** (recommended — free tier):
   ```
   LLM_PROVIDER=gemini
   GEMINI_API_KEY=your_key_here
   ```
   Get a free key at https://aistudio.google.com/
   Free tier limits: 5 requests/min, 25 requests/day (gemini-2.5-flash)

   **OpenAI** (paid, best quality):
   ```
   LLM_PROVIDER=openai
   OPENAI_API_KEY=your_key_here
   ```

   **Hugging Face** (free, lower quality):
   ```
   LLM_PROVIDER=huggingface
   HUGGINGFACE_API_KEY=your_token_here  # optional
   ```

3. **Run the web app:**
   ```bash
   python3 -m streamlit run app/app.py
   ```
   Then open http://localhost:8501

## How it works

1. Select an arXiv field (e.g. `cs.AI`) and click **Refresh** on the Daily Feed page
2. The app fetches papers from arXiv starting from the most recent date, going back until `MAX_PAPERS_LOOKBACK` papers have been analyzed
3. Papers are analyzed in batches by the LLM using a structured rubric (scores 1–10, median ≈ 5)
4. If multiple batches are analyzed, a final recalibration pass normalizes scores across batches
5. Results are stored in the local SQLite database and displayed ranked by score

## Project Structure

```
sci_paper_feed/
├── app/
│   ├── app.py                # Main Streamlit app + Daily Feed page
│   ├── ranked_feed.py        # Ranked Feed page (best of year)
│   └── database_viewer.py    # Database Viewer page
├── core/
│   ├── arxiv_client.py       # arXiv API client
│   ├── llm_client.py         # LLM provider abstraction (rate limiting, retry)
│   └── paper_analyzer.py     # Batch analysis, scoring, recalibration
├── models/
│   └── paper.py              # SQLAlchemy Paper model
├── prompts/
│   ├── batch_analysis.md     # Scoring rubric prompt
│   ├── recalibrate_scores.md # Cross-batch calibration prompt
│   └── daily_summary.md      # Daily summary prompt
├── services/
│   ├── database.py           # DatabaseManager (queries, migrations)
│   └── paper_service.py      # Orchestrates fetch → analyze → store
├── scripts/
│   ├── main.py               # Legacy CLI
│   ├── run_app.py            # Alternative app launcher
│   └── migrate_database.py   # Manual migration script
├── config.py                 # All configuration settings
└── requirements.txt
```

## Configuration (`config.py`)

| Setting | Default | Description |
|---|---|---|
| `MAX_PAPERS_TO_ANALYZE` | 50 | Max papers analyzed per day during refresh |
| `MAX_PAPERS_LOOKBACK` | 200 | Max total papers analyzed per refresh run |
| `TOP_PAPERS_COUNT` | 5 | Papers shown per day in Daily Feed |
| `ANALYSIS_BATCH_SIZE` | 10 | Papers per LLM batch call |
| `DAYS_TO_DISPLAY` | 7 | Days shown in Daily Feed |
| `AVAILABLE_FIELDS` | `['cs.AI', 'hep-th', 'cs.HC']` | Fields available in the UI |

LLM model settings (temperature, max tokens, rate limiting) are in the `MODEL_CONFIGS` dict per provider.

## Requirements

- Python 3.10+
- Internet connection (arXiv API + LLM API)
- LLM API key (see above)
