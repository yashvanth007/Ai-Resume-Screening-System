from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import analytics, assist, auth, candidates, demo, jobs, resumes
from app.core.config import settings
from app.database.session import Base, engine
from app.models import models  # noqa: F401


@asynccontextmanager
async def lifespan(_: FastAPI):
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title=settings.app_name, version="1.0.0", description="Decision-support tooling for evidence-based resume review. AI-generated scores are signals, not hiring decisions.", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=settings.allowed_origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


@app.exception_handler(Exception)
async def unhandled_exception(_: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"detail": "An unexpected server error occurred."})


@app.get("/health")
def health():
    return {"status": "ok", "service": "resume-screening-api"}


for route in (auth.router, jobs.router, resumes.router, candidates.router, assist.router, analytics.router, demo.router):
    app.include_router(route)
