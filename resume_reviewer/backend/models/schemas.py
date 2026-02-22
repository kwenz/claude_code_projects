from typing import List, Literal
from pydantic import BaseModel, Field


class Section(BaseModel):
    id: str
    title: str
    content: str


class UploadResponse(BaseModel):
    session_id: str
    file_name: str
    sections: List[Section]


class AnalyzeRequest(BaseModel):
    session_id: str
    provider: Literal["claude", "gemini"] = "claude"


class Annotation(BaseModel):
    section_id: str
    excerpt: str
    severity: Literal["error", "warning", "info"]
    comment: str
    category: str


class Suggestion(BaseModel):
    priority: int = Field(ge=1)
    title: str
    detail: str


class AnalyzeResponse(BaseModel):
    overall_score: int = Field(ge=0, le=100)
    summary: str
    annotations: List[Annotation]
    suggestions: List[Suggestion]


class EnhanceRequest(BaseModel):
    session_id: str
    provider: Literal["claude", "gemini"] = "claude"


class EnhancedSection(BaseModel):
    id: str
    title: str
    content: str


class EnhanceResponse(BaseModel):
    enhanced_sections: List[EnhancedSection]
    change_summary: str


class HealthResponse(BaseModel):
    status: str
