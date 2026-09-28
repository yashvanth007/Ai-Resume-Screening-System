from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import current_user
from app.database.session import get_db
from app.models import Application, Candidate, CandidateSkill, Job, User
from app.services.assistant import generate_candidate_summary, generate_interview_questions
from app.services.matching_service import candidate_payload

router = APIRouter(prefix="/api", tags=["candidate assistance"])


def _context(candidate_id: int, application_id: int, db: Session, user: User):
    application = db.scalar(select(Application).join(Job).where(Application.id == application_id, Application.candidate_id == candidate_id, Job.owner_id == user.id).options(selectinload(Application.candidate).selectinload(Candidate.skills).selectinload(CandidateSkill.skill), selectinload(Application.candidate).selectinload(Candidate.education), selectinload(Application.candidate).selectinload(Candidate.experiences), selectinload(Application.candidate).selectinload(Candidate.projects), selectinload(Application.candidate).selectinload(Candidate.certifications), selectinload(Application.job), selectinload(Application.match_result)))
    if not application:
        raise HTTPException(status_code=404, detail="Application not found.")
    candidate = candidate_payload(application.candidate)
    job = {"title": application.job.title, "description": application.job.description, "required_skills": application.job.required_skills, "preferred_skills": application.job.preferred_skills}
    match = {"overall_score": 0, "matched_skills": [], "missing_skills": []}
    if application.match_result:
        result = application.match_result
        match = {"overall_score": result.overall_score, "matched_skills": result.matched_skills, "missing_skills": result.missing_skills, "explanation": result.explanation}
    return candidate, job, match


@router.post("/candidates/{candidate_id}/applications/{application_id}/summary")
def candidate_summary(candidate_id: int, application_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    candidate, job, match = _context(candidate_id, application_id, db, user)
    return generate_candidate_summary(candidate, job, match)


@router.post("/candidates/{candidate_id}/applications/{application_id}/interview-questions")
def interview_questions(candidate_id: int, application_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    candidate, job, match = _context(candidate_id, application_id, db, user)
    return generate_interview_questions(candidate, job, match)
