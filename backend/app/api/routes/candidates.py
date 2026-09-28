from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import current_user
from app.database.session import get_db
from app.ml.matching import semantic_similarity
from app.models import Application, Candidate, CandidateSkill, Job, MatchResult, RecruiterNote, Resume, User
from app.schemas.schemas import CandidateUpdate, NoteCreate
from app.services.matching_service import candidate_payload

router = APIRouter(prefix="/api/candidates", tags=["candidates"])
STATUSES = {"New", "Reviewed", "Shortlisted", "Interview", "Rejected", "Hired"}


def _candidate_query(user_id: int):
    return select(Candidate).where(Candidate.owner_id == user_id).options(selectinload(Candidate.skills).selectinload(CandidateSkill.skill), selectinload(Candidate.experiences), selectinload(Candidate.education), selectinload(Candidate.projects), selectinload(Candidate.certifications), selectinload(Candidate.resumes), selectinload(Candidate.applications).selectinload(Application.match_result), selectinload(Candidate.applications).selectinload(Application.job), selectinload(Candidate.applications).selectinload(Application.notes))


def _serialize(candidate: Candidate) -> dict:
    data = candidate_payload(candidate)
    data["resumes"] = [{"id": resume.id, "filename": resume.filename, "uploaded_at": resume.uploaded_at.isoformat()} for resume in candidate.resumes]
    data["applications"] = [{"application_id": application.id, "job_id": application.job_id, "job_title": application.job.title, "company": application.job.company, "status": application.status, "recruiter_note": application.recruiter_note, "notes": [{"id": note.id, "body": note.body, "created_at": note.created_at.isoformat()} for note in application.notes], "match": ({"overall_score": application.match_result.overall_score, "skill_score": application.match_result.skill_score, "semantic_score": application.match_result.semantic_score, "experience_score": application.match_result.experience_score, "education_score": application.match_result.education_score, "project_score": application.match_result.project_score, "certification_score": application.match_result.certification_score, "matched_skills": application.match_result.matched_skills, "missing_skills": application.match_result.missing_skills, "explanation": application.match_result.explanation} if application.match_result else None)} for application in candidate.applications]
    data["status"] = candidate.applications[0].status if candidate.applications else "New"
    return data


@router.get("")
def list_candidates(db: Session = Depends(get_db), user: User = Depends(current_user), search: str = "", job_id: int | None = None, status: str | None = None, min_score: float = Query(0, ge=0, le=100), skill: str | None = None, sort_by: str = "score", offset: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=250)):
    candidates = list(db.scalars(_candidate_query(user.id).order_by(Candidate.created_at.desc())))
    rows = [_serialize(candidate) for candidate in candidates]
    if job_id:
        rows = [row for row in rows if any(application["job_id"] == job_id for application in row["applications"])]
    if search.strip():
        resumes = list(db.scalars(select(Resume).where(Resume.candidate_id.in_([candidate.id for candidate in candidates])))) if candidates else []
        text_by_candidate: dict[int, str] = {}
        for resume in resumes:
            text_by_candidate[resume.candidate_id] = f"{text_by_candidate.get(resume.candidate_id, '')} {resume.extracted_text}"
        query = search.strip()
        for row in rows:
            row["_relevance"] = semantic_similarity(query, text_by_candidate.get(row["id"], ""), (row["name"], row.get("email") or "", row.get("phone") or ""))
            row["_lexical"] = any(term in " ".join([row["name"], row.get("location") or "", " ".join(item["name"] for item in row["skills"])]).casefold() for term in query.casefold().split())
        rows = [row for row in rows if row["_lexical"] or row["_relevance"] >= 0.02]
    if status:
        rows = [row for row in rows if any(app["status"] == status for app in row["applications"])]
    if skill:
        rows = [row for row in rows if skill.casefold() in {item["name"].casefold() for item in row["skills"]}]
    rows = [row for row in rows if max(((app["match"] or {}).get("overall_score", 0) for app in row["applications"]), default=0) >= min_score]
    if search.strip() and sort_by == "score":
        rows.sort(key=lambda row: (row.get("_relevance", 0), max(((app["match"] or {}).get("overall_score", 0) for app in row["applications"]), default=0)), reverse=True)
    elif sort_by == "name":
        rows.sort(key=lambda row: row["name"].casefold())
    elif sort_by == "experience":
        rows.sort(key=lambda row: row["experience_years"], reverse=True)
    elif sort_by == "date":
        rows.sort(key=lambda row: row["resumes"][0]["uploaded_at"] if row["resumes"] else "", reverse=True)
    else:
        rows.sort(key=lambda row: max(((app["match"] or {}).get("overall_score", 0) for app in row["applications"]), default=0), reverse=True)
    for row in rows:
        row.pop("_relevance", None)
        row.pop("_lexical", None)
    return {"items": rows[offset:offset + limit], "total": len(rows), "offset": offset, "limit": limit}


@router.get("/{candidate_id}")
def get_candidate(candidate_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    candidate = db.scalar(_candidate_query(user.id).where(Candidate.id == candidate_id))
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found.")
    return _serialize(candidate)


@router.put("/{candidate_id}")
def update_candidate(candidate_id: int, payload: CandidateUpdate, db: Session = Depends(get_db), user: User = Depends(current_user)):
    candidate = db.scalar(_candidate_query(user.id).where(Candidate.id == candidate_id))
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found.")
    values = payload.model_dump(exclude_unset=True)
    application_id = values.pop("application_id", None)
    if "status" in values:
        if values["status"] not in STATUSES:
            raise HTTPException(status_code=422, detail=f"Status must be one of: {', '.join(sorted(STATUSES))}.")
        application = db.scalar(select(Application).join(Job).where(Application.candidate_id == candidate.id, Job.owner_id == user.id, *([Application.id == application_id] if application_id else [])))
        if not application:
            raise HTTPException(status_code=404, detail="Application not found.")
        application.status = values.pop("status")
    db.commit()
    db.refresh(candidate)
    return _serialize(candidate)


@router.post("/{candidate_id}/applications/{application_id}/notes", status_code=201)
def add_note(candidate_id: int, application_id: int, payload: NoteCreate, db: Session = Depends(get_db), user: User = Depends(current_user)):
    application = db.scalar(select(Application).join(Job).where(Application.id == application_id, Application.candidate_id == candidate_id, Job.owner_id == user.id))
    if not application:
        raise HTTPException(status_code=404, detail="Application not found.")
    note = RecruiterNote(application_id=application.id, author_id=user.id, body=payload.body.strip())
    db.add(note)
    db.commit()
    db.refresh(note)
    return {"id": note.id, "body": note.body, "created_at": note.created_at.isoformat()}
