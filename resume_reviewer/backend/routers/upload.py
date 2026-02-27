from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

from models.schemas import UploadResponse
from services import parser, session_store

router = APIRouter()

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
TMP_DIR = Path(__file__).parent.parent / "tmp"
TMP_DIR.mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {".pdf", ".docx"}


@router.post("/upload", response_model=UploadResponse)
async def upload_resume(file: UploadFile = File(...)):
    # Sanitize and validate filename
    safe_name = Path(file.filename or "upload").name
    suffix = Path(safe_name).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{suffix}'. Upload a PDF or DOCX.",
        )

    # Read and check size
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="File exceeds 10 MB limit.",
        )

    # Save to tmp
    session_id = session_store.create_session()
    tmp_path = TMP_DIR / f"{session_id}{suffix}"
    tmp_path.write_bytes(content)

    try:
        if suffix == ".pdf":
            sections = parser.parse_pdf(tmp_path)
        else:
            sections = parser.parse_docx(tmp_path)
    except Exception as e:
        session_store.delete_session(session_id)
        raise HTTPException(status_code=422, detail="Could not parse the uploaded file.")
    finally:
        tmp_path.unlink(missing_ok=True)

    if not sections:
        session_store.delete_session(session_id)
        raise HTTPException(status_code=422, detail="No readable text found in file.")

    raw_text = "\n\n".join(s.content for s in sections)
    session_store.update_session(
        session_id,
        sections=[s.model_dump() for s in sections],
        raw_text=raw_text,
        file_name=safe_name,
    )

    return UploadResponse(
        session_id=session_id,
        file_name=safe_name,
        sections=sections,
    )
