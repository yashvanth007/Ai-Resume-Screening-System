from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import current_user, owned_job
from app.database.session import get_db
from app.ml.matching import extract_job_skills
from app.ml.skills import ALL_SKILLS, SKILL_CATEGORY
from app.models import Application, Candidate, CandidateSkill, Job, JobSkill, MatchResult, User
from app.schemas.schemas import JobCreate, JobUpdate
from app.services.matching_service import candidate_payload, ensure_skill, score_application

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


def serialize_job(job: Job, include_candidates: bool = False) -> dict:
    data = {"id": job.id, "title": job.title, "company": job.company, "location": job.location, "employment_type": job.employment_type, "experience_required": job.experience_required, "education_requirement": job.education_requirement, "salary_min": job.salary_min, "salary_max": job.salary_max, "description": job.description, "required_skills": job.required_skills or [], "preferred_skills": job.preferred_skills or [], "created_at": job.created_at.isoformat() if job.created_at else None, "candidate_count": len(job.applications)}
    if include_candidates:
        data["candidates"] = [serialize_application(application) for application in sorted(job.applications, key=lambda item: item.match_result.overall_score if item.match_result else 0, reverse=True)]
    return data


def serialize_application(application: Application) -> dict:
    candidate = application.candidate
    match = application.match_result
    data = candidate_payload(candidate)
    data.update({"application_id": application.id, "job_id": application.job_id, "status": application.status, "recruiter_note": application.recruiter_note, "uploaded_at": application.created_at.isoformat(), "match": None})
    if match:
        data["match"] = {"overall_score": match.overall_score, "skill_score": match.skill_score, "semantic_score": match.semantic_score, "experience_score": match.experience_score, "education_score": match.education_score, "project_score": match.project_score, "certification_score": match.certification_score, "matched_skills": match.matched_skills, "missing_skills": match.missing_skills, "explanation": match.explanation}
    if candidate.resumes:
        resume = max(candidate.resumes, key=lambda item: item.uploaded_at)
        data["resume_id"] = resume.id
        data["resume_filename"] = resume.filename
    return data


@router.post("", status_code=201)
def create_job(payload: JobCreate, db: Session = Depends(get_db), user: User = Depends(current_user)):
    required = list(dict.fromkeys(skill.strip() for skill in payload.required_skills if skill.strip()))
    preferred = list(dict.fromkeys(skill.strip() for skill in payload.preferred_skills if skill.strip()))
    if not required:
        required = extract_job_skills(payload.description, ALL_SKILLS)
    job = Job(owner_id=user.id, title=payload.title.strip(), company=payload.company.strip(), location=payload.location, employment_type=payload.employment_type, experience_required=payload.experience_required, education_requirement=payload.education_requirement, salary_min=payload.salary_min, salary_max=payload.salary_max, description=payload.description.strip(), required_skills=required, preferred_skills=preferred)
    db.add(job)
    db.flush()
    for name in required + [item for item in preferred if item.casefold() not in {value.casefold() for value in required}]:
        skill = ensure_skill(db, name, next((category.title() for key, category in SKILL_CATEGORY.items() if key == name.casefold()), "Other"))
        db.add(JobSkill(job_id=job.id, skill_id=skill.id, required=name in required))
    db.commit()
    db.refresh(job)
    return serialize_job(job)


@router.get("")
def list_jobs(db: Session = Depends(get_db), user: User = Depends(current_user), search: str = ""):
    statement = select(Job).where(Job.owner_id == user.id).options(selectinload(Job.applications).selectinload(Application.match_result)).order_by(Job.created_at.desc())
    jobs = list(db.scalars(statement))
    if search.strip():
        term = search.casefold()
        jobs = [job for job in jobs if term in job.title.casefold() or term in job.company.casefold()]
    return [serialize_job(job) for job in jobs]


@router.get("/{job_id}")
def get_job(job_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    job = db.scalar(select(Job).where(Job.id == job_id, Job.owner_id == user.id).options(selectinload(Job.applications).selectinload(Application.candidate).selectinload(Candidate.skills).selectinload(CandidateSkill.skill), selectinload(Job.applications).selectinload(Application.candidate).selectinload(Candidate.education), selectinload(Job.applications).selectinload(Application.candidate).selectinload(Candidate.experiences), selectinload(Job.applications).selectinload(Application.candidate).selectinload(Candidate.projects), selectinload(Job.applications).selectinload(Application.candidate).selectinload(Candidate.certifications), selectinload(Job.applications).selectinload(Application.candidate).selectinload(Candidate.resumes), selectinload(Job.applications).selectinload(Application.match_result)))
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    return serialize_job(job, include_candidates=True)


@router.put("/{job_id}")
def update_job(job_id: int, payload: JobUpdate, db: Session = Depends(get_db), user: User = Depends(current_user)):
    job = owned_job(job_id, user, db)
    for key, value in payload.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(job, key, value)
    db.commit()
    db.refresh(job)
    return serialize_job(job)


@router.delete("/{job_id}", status_code=204)
def delete_job(job_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    job = owned_job(job_id, user, db)
    db.delete(job)
    db.commit()
    return Response(status_code=204)


@router.post("/{job_id}/match")
def match_job(job_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    job = owned_job(job_id, user, db)
    applications = list(db.scalars(select(Application).where(Application.job_id == job.id).options(selectinload(Application.candidate))))
    for application in applications:
        score_application(db, application, job)
    db.commit()
    return {"job_id": job.id, "processed": len(applications), "candidates": len(applications)}


@router.get("/{job_id}/candidates")
def job_candidates(job_id: int, db: Session = Depends(get_db), user: User = Depends(current_user), search: str = "", status: str | None = None, min_score: float = Query(0, ge=0, le=100), skill: str | None = None, sort_by: str = "score"):
    job = db.scalar(select(Job).where(Job.id == job_id, Job.owner_id == user.id).options(selectinload(Job.applications).selectinload(Application.candidate).selectinload(Candidate.skills).selectinload(CandidateSkill.skill), selectinload(Job.applications).selectinload(Application.candidate).selectinload(Candidate.education), selectinload(Job.applications).selectinload(Application.candidate).selectinload(Candidate.experiences), selectinload(Job.applications).selectinload(Application.candidate).selectinload(Candidate.projects), selectinload(Job.applications).selectinload(Application.candidate).selectinload(Candidate.certifications), selectinload(Job.applications).selectinload(Application.candidate).selectinload(Candidate.resumes), selectinload(Job.applications).selectinload(Application.match_result)))
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    rows = [serialize_application(application) for application in job.applications]
    if search.strip():
        terms = search.casefold().split()
        rows = [row for row in rows if all(any(term in str(value).casefold() for value in [row["name"], row.get("email", ""), " ".join(item["name"] for item in row["skills"]), " ".join(item.get("name") or "" for item in row["projects"])]) for term in terms)]
    if status:
        rows = [row for row in rows if row["status"] == status]
    if skill:
        rows = [row for row in rows if skill.casefold() in {item["name"].casefold() for item in row["skills"]}]
    rows = [row for row in rows if (row["match"] or {}).get("overall_score", 0) >= min_score]
    if sort_by == "name":
        rows.sort(key=lambda row: row["name"].casefold())
    elif sort_by == "experience":
        rows.sort(key=lambda row: row["experience_years"], reverse=True)
    elif sort_by == "date":
        rows.sort(key=lambda row: row["uploaded_at"], reverse=True)
    else:
        rows.sort(key=lambda row: (row["match"] or {}).get("overall_score", 0), reverse=True)
    return rows


@router.get("/{job_id}/ranking")
def job_ranking(job_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    return job_candidates(job_id, db, user, min_score=0)
