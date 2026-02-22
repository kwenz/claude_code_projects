import json
import os
import re
from typing import List

import google.generativeai as genai
from dotenv import load_dotenv

from models.schemas import Section, AnalyzeResponse, EnhanceResponse

load_dotenv()

_api_key = os.environ.get("GEMINI_API_KEY")
if _api_key:
    genai.configure(api_key=_api_key)

MODEL = "gemini-2.0-flash"


def _sections_to_text(sections: List[Section]) -> str:
    parts = []
    for s in sections:
        parts.append(f"[SECTION id={s.id} title={s.title}]\n{s.content}")
    return "\n\n".join(parts)


def _extract_json(text: str) -> dict:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return json.loads(text)


def analyze_resume(sections: List[Section]) -> AnalyzeResponse:
    if not _api_key:
        raise RuntimeError(
            "GEMINI_API_KEY environment variable is not set. "
            "Add it to backend/.env to use the Gemini provider."
        )

    resume_text = _sections_to_text(sections)
    section_ids = [s.id for s in sections]

    prompt = f"""You are an expert resume reviewer and career coach.
Analyze the following resume and return ONLY a JSON object with this exact schema (no prose, no markdown fences):

{{
  "overall_score": <integer 0-100>,
  "summary": "<2-4 sentence overall assessment>",
  "annotations": [
    {{
      "section_id": "<one of: {', '.join(section_ids)}>",
      "excerpt": "<short verbatim text from that section, max 80 chars>",
      "severity": "<error|warning|info>",
      "comment": "<actionable feedback>",
      "category": "<e.g. Impact, Clarity, ATS, Formatting, Grammar>"
    }}
  ],
  "suggestions": [
    {{
      "priority": <1-based integer>,
      "title": "<short title>",
      "detail": "<2-3 sentence explanation>"
    }}
  ]
}}

Rules:
- annotations: 4 to 12 items
- suggestions: 3 to 7 items, ordered by priority (1 = most important)
- excerpt must be an exact substring of the section content
- severity "error" = significant problem, "warning" = improvement needed, "info" = minor tip

RESUME:
{resume_text}"""

    model = genai.GenerativeModel(MODEL)
    response = model.generate_content(prompt)
    data = _extract_json(response.text)
    return AnalyzeResponse(**data)


def enhance_resume(sections: List[Section]) -> EnhanceResponse:
    if not _api_key:
        raise RuntimeError(
            "GEMINI_API_KEY environment variable is not set. "
            "Add it to backend/.env to use the Gemini provider."
        )

    resume_text = _sections_to_text(sections)

    prompt = f"""You are an expert resume writer.
Rewrite the following resume sections to be more compelling, concise, and ATS-friendly.
Preserve all factual content (dates, companies, titles, technologies).
Return ONLY a JSON object (no prose, no markdown fences):

{{
  "enhanced_sections": [
    {{
      "id": "<same id as original>",
      "title": "<same title as original>",
      "content": "<improved content>"
    }}
  ],
  "change_summary": "<2-4 sentences describing overall improvements made>"
}}

RESUME:
{resume_text}"""

    model = genai.GenerativeModel(MODEL)
    response = model.generate_content(prompt)
    data = _extract_json(response.text)
    return EnhanceResponse(**data)
