import re
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import current_user, owned_job
from app.core.config import settings
from app.database.session import get_db
from app.ml.skills import SKILL_CATEGORY
from app.models import Application, Candidate, CandidateSkill, Certification, Education, Experience, Job, Project, RecruiterNote, Resume, User
from app.services.matching_service import ensure_skill, score_application
from app.services.resume_parser import extract_text, parse_resume

router = APIRouter(prefix="/api/resumes", tags=["resumes"])
ALLOWED_EXTENSIONS = {".pdf", ".docx"}


def validate_file(filename: str, content: bytes) -> str:
    suffix = Path(filename or "").suffix.casefold()
    if suffix not in ALLOWED_EXTENSIONS:
        raise ValueError("Unsupported file type. Upload a PDF or DOCX resume.")
    if not content:
        raise ValueError("This file is empty.")
    if len(content) > settings.max_upload_bytes:
        raise ValueError(f"File is larger than the {settings.max_upload_bytes // (1024 * 1024)} MB limit.")
    if suffix == ".pdf" and not content.startswith(b"%PDF-"):
        raise ValueError("This file does not have a valid PDF signature.")
    if suffix == ".docx" and not content.startswith(b"PK"):
        raise ValueError("This file does not have a valid DOCX signature.")
    return "application/pdf" if suffix == ".pdf" else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def _persist_resume(db: Session, upload: UploadFile, job: Job, user: User, content: bytes) -> dict:
    content_type = validate_file(upload.filename or "", content)
    text = extract_text(upload.filename or "resume", content)
    parsed = parse_resume(text)
    normalized_email = parsed["email"].casefold() if parsed["email"] else None
    candidate = db.scalar(select(Candidate).where(Candidate.owner_id == user.id, Candidate.email == normalized_email)) if normalized_email else None
    is_new_candidate = candidate is None
    if candidate is None:
        candidate = Candidate(owner_id=user.id, full_name=parsed["name"], email=normalized_email, phone=parsed["phone"], location=parsed["location"], linkedin=parsed["linkedin"], github=parsed["github"], portfolio=parsed["portfolio"], total_experience=parsed["experience_years"])
        db.add(candidate)
        db.flush()
        for item in parsed["skills"]:
            skill = ensure_skill(db, item["name"], item["category"])
            db.add(CandidateSkill(candidate_id=candidate.id, skill_id=skill.id, evidence="Detected in uploaded resume"))
        for item in parsed["education"]:
            db.add(Education(candidate_id=candidate.id, **item))
        for item in parsed["projects"]:
            db.add(Project(candidate_id=candidate.id, **item))
        for item in parsed["certifications"]:
            db.add(Certification(candidate_id=candidate.id, **item))
        experience_section = parsed["sections"].get("experience", "")
        if experience_section:
            for block in re.split(r"\n\s*\n", experience_section)[:12]:
                lines = [line.strip(" •-*\t") for line in block.splitlines() if line.strip(" •-*\t")]
                if lines:
                    db.add(Experience(candidate_id=candidate.id, title=lines[0][:180], description="\n".join(lines[1:])))
    else:
        if parsed["experience_years"] > candidate.total_experience:
            candidate.total_experience = parsed["experience_years"]
        for item in parsed["skills"]:
            skill = ensure_skill(db, item["name"], item["category"])
            exists = db.scalar(select(CandidateSkill.id).where(CandidateSkill.candidate_id == candidate.id, CandidateSkill.skill_id == skill.id))
            if not exists:
                db.add(CandidateSkill(candidate_id=candidate.id, skill_id=skill.id, evidence="Detected in uploaded resume"))
    upload_dir = Path(settings.upload_dir).resolve()
    upload_dir.mkdir(parents=True, exist_ok=True)
    stored_name = f"{uuid.uuid4().hex}{Path(upload.filename or 'resume').suffix.casefold()}"
    stored_path = upload_dir / stored_name
    stored_path.write_bytes(content)
    resume = Resume(candidate_id=candidate.id, filename=Path(upload.filename or "resume").name[:255], stored_path=str(stored_path), content_type=content_type, extracted_text=text, sections=parsed["sections"])
    db.add(resume)
    db.flush()
    application = db.scalar(select(Application).where(Application.job_id == job.id, Application.candidate_id == candidate.id))
    if not application:
        application = Application(job_id=job.id, candidate_id=candidate.id, status="New")
        db.add(application)
        db.flush()
    score_application(db, application, job)
    return {"candidate_id": candidate.id, "resume_id": resume.id, "application_id": application.id, "name": candidate.full_name, "email": candidate.email, "skills_detected": len(parsed["skills"]), "status": "processed"}


@router.post("/upload-multiple", status_code=201)
async def upload_multiple(job_id: int = Form(...), files: list[UploadFile] = File(...), db: Session = Depends(get_db), user: User = Depends(current_user)):
    job = owned_job(job_id, user, db)
    if not files:
        raise HTTPException(status_code=422, detail="Select at least one resume to upload.")
    results = []
    errors = []
    for upload in files:
        try:
            content = await upload.read(settings.max_upload_bytes + 1)
            result = _persist_resume(db, upload, job, user, content)
            db.commit()
            results.append(result)
        except Exception as error:
            db.rollback()
            errors.append({"filename": upload.filename or "unnamed file", "error": str(error) if isinstance(error, ValueError) else "File could not be processed. Confirm the document is a valid PDF or DOCX."})
    db.commit()
    return {"processed": len(results), "failed": len(errors), "results": results, "errors": errors}


@router.post("/upload", status_code=201)
async def upload_one(job_id: int = Form(...), file: UploadFile = File(...), db: Session = Depends(get_db), user: User = Depends(current_user)):
    job = owned_job(job_id, user, db)
    try:
        content = await file.read(settings.max_upload_bytes + 1)
        result = _persist_resume(db, file, job, user, content)
        db.commit()
        return result
    except ValueError as error:
        db.rollback()
        raise HTTPException(status_code=422, detail=str(error)) from error
    except Exception as error:
        db.rollback()
        raise HTTPException(status_code=422, detail="File could not be processed. Confirm it is a readable PDF or DOCX.") from error


@router.get("/{resume_id}")
def get_resume(resume_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    resume = db.scalar(select(Resume).join(Candidate).where(Resume.id == resume_id, Candidate.owner_id == user.id))
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found.")
    return {"id": resume.id, "candidate_id": resume.candidate_id, "filename": resume.filename, "uploaded_at": resume.uploaded_at.isoformat(), "extracted_text": resume.extracted_text, "sections": resume.sections}


@router.delete("/{resume_id}", status_code=204)
def delete_resume(resume_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    resume = db.scalar(select(Resume).join(Candidate).where(Resume.id == resume_id, Candidate.owner_id == user.id))
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found.")
    path = Path(resume.stored_path)
    if path.exists():
        path.unlink()
    db.delete(resume)
    db.commit()
