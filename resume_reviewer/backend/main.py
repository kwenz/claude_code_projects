from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from models.schemas import HealthResponse
from routers import upload, analyze, enhance

app = FastAPI(title="Resume Reviewer API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router, prefix="/api")
app.include_router(analyze.router, prefix="/api")
app.include_router(enhance.router, prefix="/api")


@app.get("/api/health", response_model=HealthResponse)
async def health():
    return HealthResponse(status="ok")
