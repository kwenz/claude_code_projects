import json
import os
import re
from typing import List

import anthropic
from dotenv import load_dotenv

from models.schemas import Section, AnalyzeResponse, EnhanceResponse

load_dotenv()

_api_key = os.environ.get("ANTHROPIC_API_KEY")
if not _api_key:
    raise RuntimeError(
        "ANTHROPIC_API_KEY environment variable is not set. "
        "Copy backend/.env.example to backend/.env and add your key."
    )
_client = anthropic.Anthropic(api_key=_api_key)
MODEL = "claude-sonnet-4-5"


def _sections_to_text(sections: List[Section]) -> str:
    parts = []
    for s in sections:
        parts.append(f"[SECTION id={s.id} title={s.title}]\n{s.content}")
    return "\n\n".join(parts)


def _extract_json(text: str) -> dict:
    # Strip markdown code fences if present
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return json.loads(text)


def analyze_resume(sections: List[Section]) -> AnalyzeResponse:
    resume_text = _sections_to_text(sections)
    section_ids = [s.id for s in sections]

    system_prompt = (
        "You are an expert resume reviewer and career coach. "
        "Analyze the provided resume and return ONLY valid JSON — no prose, no markdown fences."
    )

    user_prompt = f"""Analyze the following resume. Return ONLY a JSON object with this exact schema:

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
{resume_text}
"""

    message = _client.messages.create(
        model=MODEL,
        max_tokens=4096,
        messages=[{"role": "user", "content": user_prompt}],
        system=system_prompt,
    )

    raw = message.content[0].text
    data = _extract_json(raw)
    return AnalyzeResponse(**data)


def enhance_resume(sections: List[Section]) -> EnhanceResponse:
    resume_text = _sections_to_text(sections)

    system_prompt = (
        "You are an expert resume writer. "
        "Rewrite the provided resume sections to be more compelling, concise, and ATS-friendly. "
        "Return ONLY valid JSON — no prose, no markdown fences."
    )

    user_prompt = f"""Rewrite the following resume sections to maximize impact and professionalism.
Preserve all factual content (dates, companies, titles, technologies). Return ONLY a JSON object:

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
{resume_text}
"""

    message = _client.messages.create(
        model=MODEL,
        max_tokens=8192,
        messages=[{"role": "user", "content": user_prompt}],
        system=system_prompt,
    )

    raw = message.content[0].text
    data = _extract_json(raw)
    return EnhanceResponse(**data)
