import io

from docx import Document


def _resume(name: str, email: str, skills: str) -> bytes:
    document = Document()
    for line in [name, email, "3 years experience", "Skills", skills, "Education", "B.S. Computer Science", "Projects", "Python API service built with FastAPI and PostgreSQL"]:
        document.add_paragraph(line)
    stream = io.BytesIO()
    document.save(stream)
    return stream.getvalue()


def _auth(client):
    response = client.post("/api/auth/register", json={"full_name": "Recruiter Example", "email": "recruiter@example.com", "password": "strong-test-password"})
    assert response.status_code == 201, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_auth_job_resume_upload_matching_and_analytics(client):
    assert client.get("/api/analytics/dashboard").status_code == 401
    headers = _auth(client)
    assert client.get("/api/auth/me", headers=headers).json()["email"] == "recruiter@example.com"
    job_response = client.post("/api/jobs", headers=headers, json={"title": "Python Engineer", "company": "Sample Co", "description": "Build Python APIs using FastAPI, SQL, PostgreSQL, and Git for production services.", "experience_required": 2, "required_skills": ["Python", "FastAPI", "SQL"], "preferred_skills": ["Docker"]})
    assert job_response.status_code == 201, job_response.text
    job_id = job_response.json()["id"]
    files = [
        ("files", ("good-fit.docx", _resume("Alex Sample", "alex@example.test", "Python, FastAPI, SQL, Docker"), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")),
        ("files", ("partial-fit.docx", _resume("Jamie Sample", "jamie@example.test", "Python, Git"), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")),
        ("files", ("invalid.pdf", b"not actually a PDF", "application/pdf")),
    ]
    upload = client.post("/api/resumes/upload-multiple", headers=headers, data={"job_id": job_id}, files=files)
    assert upload.status_code == 201, upload.text
    assert upload.json()["processed"] == 2
    assert upload.json()["failed"] == 1
    ranked = client.get(f"/api/jobs/{job_id}/ranking", headers=headers)
    assert ranked.status_code == 200
    assert len(ranked.json()) == 2
    assert ranked.json()[0]["name"] == "Alex Sample"
    assert ranked.json()[0]["match"]["overall_score"] > ranked.json()[1]["match"]["overall_score"]
    assert "Docker" in ranked.json()[0]["match"]["matched_skills"]
    assert "SQL" in ranked.json()[1]["match"]["missing_skills"]
    candidate_id = ranked.json()[0]["id"]
    application_id = ranked.json()[0]["application_id"]
    summary = client.post(f"/api/candidates/{candidate_id}/applications/{application_id}/summary", headers=headers)
    assert summary.status_code == 200
    assert summary.json()["source"] == "rule-based"
    questions = client.post(f"/api/candidates/{candidate_id}/applications/{application_id}/interview-questions", headers=headers)
    assert questions.status_code == 200
    assert len(questions.json()["technical"]) == 5
    assert len(questions.json()["project"]) == 3
    assert len(set(questions.json()["technical"])) == 5
    assert len(set(questions.json()["project"])) == 3
    assert len(set(questions.json()["behavioral"])) == 2
    note = client.post(f"/api/candidates/{candidate_id}/applications/{application_id}/notes", headers=headers, json={"body": "Discuss the production tradeoffs in the API project."})
    assert note.status_code == 201
    detail = client.get(f"/api/candidates/{candidate_id}", headers=headers)
    assert detail.json()["applications"][0]["notes"][0]["body"] == "Discuss the production tradeoffs in the API project."
    search = client.get("/api/candidates?search=Python API", headers=headers)
    assert search.status_code == 200
    assert search.json()["total"] >= 1
    status = client.put(f"/api/candidates/{candidate_id}", headers=headers, json={"status": "Shortlisted", "application_id": application_id})
    assert status.status_code == 200, status.text
    assert status.json()["applications"][0]["status"] == "Shortlisted"
    analytics = client.get("/api/analytics/dashboard", headers=headers)
    assert analytics.status_code == 200
    assert analytics.json()["total_candidates"] == 2
    assert analytics.json()["resumes_processed"] == 2


def test_demo_workspace_is_useful_and_idempotent(client):
    headers = _auth(client)
    first = client.post("/api/demo/seed", headers=headers)
    assert first.status_code == 200, first.text
    assert first.json()["created"] is True
    assert first.json()["candidates"] == 5
    second = client.post("/api/demo/seed", headers=headers)
    assert second.json()["created"] is False
    stats = client.get("/api/analytics/dashboard", headers=headers).json()
    assert stats["total_jobs"] == 3
    assert stats["total_candidates"] == 5
