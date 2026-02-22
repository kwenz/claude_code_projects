import re
from pathlib import Path
from typing import List
from models.schemas import Section

SECTION_KEYWORDS = {
    "summary", "objective", "profile", "about",
    "experience", "work experience", "employment", "work history",
    "education", "academic", "qualifications",
    "skills", "technical skills", "core competencies", "competencies",
    "projects", "portfolio",
    "certifications", "certificates", "licenses",
    "awards", "honors", "achievements",
    "publications", "research",
    "languages",
    "volunteer", "volunteering",
    "references",
    "contact", "personal information",
}


def _make_section_id(title: str, index: int) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")
    return f"{slug}_{index}"


def _is_section_header(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    # All-caps line (at least 3 chars, no digits dominating)
    if stripped.isupper() and len(stripped) >= 3 and len(stripped) <= 60:
        return True
    # Matches known keywords (case-insensitive)
    lower = stripped.lower().rstrip(":").strip()
    if lower in SECTION_KEYWORDS:
        return True
    return False


def parse_pdf(file_path: Path) -> List[Section]:
    import fitz  # PyMuPDF

    doc = fitz.open(str(file_path))
    lines: List[str] = []
    for page in doc:
        text = page.get_text("text")
        lines.extend(text.splitlines())
    doc.close()

    return _segment_lines(lines)


def parse_docx(file_path: Path) -> List[Section]:
    from docx import Document

    doc = Document(str(file_path))
    lines: List[str] = []
    for para in doc.paragraphs:
        text = para.text.strip()
        if not text:
            lines.append("")
            continue
        style_name = para.style.name.lower() if para.style else ""
        # Heading styles → treat as section header
        if "heading" in style_name:
            lines.append(text.upper())
        else:
            lines.append(text)

    return _segment_lines(lines)


def _segment_lines(lines: List[str]) -> List[Section]:
    sections: List[Section] = []
    current_title = "Header"
    current_lines: List[str] = []
    section_index = 0

    def flush():
        nonlocal current_title, current_lines, section_index
        content = "\n".join(current_lines).strip()
        if content:
            sid = _make_section_id(current_title, section_index)
            sections.append(Section(id=sid, title=current_title, content=content))
            section_index += 1
        current_lines = []

    for line in lines:
        if _is_section_header(line):
            flush()
            current_title = line.strip().rstrip(":")
        else:
            current_lines.append(line)

    flush()

    # If only one giant block (no headers detected), split by blank lines
    if len(sections) == 1 and "\n\n" in sections[0].content:
        raw = sections[0].content
        chunks = [c.strip() for c in re.split(r"\n{2,}", raw) if c.strip()]
        sections = []
        for i, chunk in enumerate(chunks):
            first_line = chunk.splitlines()[0][:40]
            sid = _make_section_id(first_line, i)
            sections.append(Section(id=sid, title=first_line, content=chunk))

    return sections
