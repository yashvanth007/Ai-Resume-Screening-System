from collections import Counter

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import current_user
from app.database.session import get_db
from app.models import Application, Candidate, CandidateSkill, Job, MatchResult, User

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


def _overview(db: Session, user: User, job_id: int | None = None) -> dict:
    jobs = list(db.scalars(select(Job).where(Job.owner_id == user.id).options(selectinload(Job.applications).selectinload(Application.match_result))))
    if job_id is not None:
        jobs = [job for job in jobs if job.id == job_id]
        if not jobs:
            raise HTTPException(status_code=404, detail="Job not found.")
    applications = [application for job in jobs for application in job.applications]
    candidate_ids = {application.candidate_id for application in applications}
    scores = [application.match_result.overall_score for application in applications if application.match_result]
    statuses = Counter(application.status for application in applications)
    by_job = [{"job_id": job.id, "title": job.title, "company": job.company, "candidates": len(job.applications), "average_score": round(sum(app.match_result.overall_score for app in job.applications if app.match_result) / max(1, sum(bool(app.match_result) for app in job.applications)), 1)} for job in jobs]
    candidates = list(db.scalars(select(Candidate).where(Candidate.owner_id == user.id, Candidate.id.in_(candidate_ids)).options(selectinload(Candidate.skills).selectinload(CandidateSkill.skill)))) if candidate_ids else []
    skill_counts = Counter(skill.skill.name for candidate in candidates for skill in candidate.skills)
    missing_counts = Counter(skill for application in applications if application.match_result for skill in application.match_result.missing_skills)
    processed = sum(len(candidate.resumes) for candidate in candidates)
    return {"total_jobs": len(jobs), "total_candidates": len(candidate_ids), "resumes_processed": processed, "shortlisted_candidates": statuses["Shortlisted"], "average_match_score": round(sum(scores) / len(scores), 1) if scores else 0, "candidates_per_job": by_job, "status_distribution": dict(statuses), "top_skills": [{"name": name, "count": count} for name, count in skill_counts.most_common(10)], "missing_skills": [{"name": name, "count": count} for name, count in missing_counts.most_common(10)]}


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db), user: User = Depends(current_user)):
    return _overview(db, user)


@router.get("/jobs/{job_id}")
def job_analytics(job_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    return _overview(db, user, job_id)
