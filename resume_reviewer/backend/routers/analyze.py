from fastapi import APIRouter, HTTPException

from models.schemas import AnalyzeRequest, AnalyzeResponse, Section
from services import claude_client, gemini_client, session_store

router = APIRouter()


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_resume(body: AnalyzeRequest):
    session = session_store.get_session(body.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")

    cache_key = f"analysis_{body.provider}"

    # Return cached result if available
    if session.get(cache_key):
        return AnalyzeResponse(**session[cache_key])

    sections = [Section(**s) for s in session["sections"]]
    if not sections:
        raise HTTPException(status_code=422, detail="No sections in session.")

    client = claude_client if body.provider == "claude" else gemini_client

    try:
        result = client.analyze_resume(sections)
    except Exception:
        raise HTTPException(status_code=500, detail="Resume analysis failed. Please try again.")

    session_store.update_session(body.session_id, **{cache_key: result.model_dump()})
    return result
