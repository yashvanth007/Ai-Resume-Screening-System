# AI Resume Screening & Candidate Matching

A full-stack recruiter decision-support application. Recruiters can create job openings, upload PDF/DOCX resumes, inspect extracted evidence, compare and rank applicants, add notes, and review pipeline analytics. Match scores are transparent signals; they do not make hiring decisions.

> **Fairness notice:** AI-generated scores are decision-support signals and should be reviewed by qualified recruiters. The system does not make final hiring decisions. Names and contact details are excluded from matching features and from optional LLM requests.

## Features

- Recruiter registration/login with expiring JWT sessions and Argon2 password hashes.
- Job CRUD, automatic skill extraction from descriptions, required/preferred skills, location, employment type, salary and experience fields.
- Multi-file PDF/DOCX uploads with type/signature/size checks, PDF/DOCX text extraction, contact/skill/education/project/certification parsing, and graceful invalid-file results.
- Six-factor explainable ranking, required/preferred skill gap reporting, candidate search, status filtering, pagination, and 2–5 person comparisons.
- Candidate profiles, status workflow, recruiter notes, extracted-text preview, deterministic candidate summaries and interview prompts.
- Optional OpenAI-compatible candidate summaries and optional sentence-transformer embeddings. Both fall back locally; no API key is required to run.
- Workspace dashboard, charts, analytics, a synthetic demo workspace, SQLite local mode, PostgreSQL Docker Compose mode, and Alembic migrations.

## Architecture

```text
React + Vite
    | JSON / multipart REST, JWT bearer token
FastAPI routes -> services -> parser / NLP / matching
    | SQLAlchemy ORM
SQLite (local) or PostgreSQL (Compose)
```

The backend separates routes, Pydantic schemas, SQLAlchemy models, services, parser utilities, and ML matching. FastAPI publishes interactive OpenAPI docs at `/docs` and `/redoc`.

## Requirements

- Python 3.12 or newer (tested locally with Python 3.14).
- Node.js 20.19+ or 22.12+ and npm.
- Docker Desktop only for the PostgreSQL Compose workflow.

## Run Locally (SQLite)

From the repository root in PowerShell:

```powershell
cd backend
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item ..\.env.example .env
python -m uvicorn app.main:app --reload --port 8000
```

In a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`, register a recruiter account, then create a job and upload resumes. The API runs at `http://localhost:8000`; Swagger UI is at `http://localhost:8000/docs`. By default the database is `backend/resume_screening.db` and uploads are saved under `backend/uploads/`.

For another OS, create/activate a virtual environment using its normal Python command, install `backend/requirements.txt`, then run Uvicorn from `backend/` and Vite from `frontend/`.

## Try the Sample Workspace

After registering, use **Try sample workspace** on the empty dashboard. This creates three sample openings, five synthetic candidates, fifteen real match results, and synthetic resume records. Seeding is idempotent and does not add duplicates. No real people or private contact data are used.

To generate five actual DOCX example files for manual upload, from the repository root run:

```powershell
backend\.venv\Scripts\python.exe data\generate_sample_resumes.py
```

Three editable job examples are in `data/sample_jobs/roles.json`.

## Environment Variables

Copy `.env.example` to `backend/.env` for local development, or to the repository root for Docker Compose.

| Variable | Purpose | Local default |
| --- | --- | --- |
| `SECRET_KEY` | Signs access tokens; set a long random production value | Development-only placeholder |
| `DATABASE_URL` | SQLAlchemy URL | `sqlite:///./resume_screening.db` |
| `CORS_ORIGINS` | Comma-separated frontend origins | `http://localhost:5173,http://127.0.0.1:5173` |
| `UPLOAD_DIR` | Resume storage directory | `./uploads` |
| `MAX_UPLOAD_BYTES` | Per-file upload cap | `10485760` (10 MiB) |
| `ACCESS_TOKEN_MINUTES` | JWT lifetime | `720` |
| `LLM_API_KEY` | Optional OpenAI-compatible API credential | Unset; local deterministic fallback |
| `LLM_BASE_URL` | Optional API base, e.g. `https://api.openai.com/v1` | Unset |
| `LLM_MODEL` | Model name sent to chat completions | `gpt-4o-mini` |
| `USE_SENTENCE_TRANSFORMERS` | Enable local cached MiniLM embeddings | `false` |

Never commit `.env` or production credentials.

## PostgreSQL with Docker Compose

Start Docker Desktop, then from the project root:

```powershell
Copy-Item .env.example .env
docker compose up --build
```

Open `http://localhost:5173`; API and Swagger docs are at `http://localhost:8000` and `/docs`. Compose starts PostgreSQL 17, waits for its health check, runs Alembic migrations, then launches the API and Nginx-served frontend. Persistent named volumes hold database data and uploaded resumes. Stop with `Ctrl+C`; `docker compose down` keeps volumes, while `docker compose down -v` deletes the local database/uploads.

## Tests and Checks

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest -q
```

Tests cover parser extraction, file validation, skills, score weights, auth, job APIs, DOCX multi-upload (including a rejected file), ranking, status changes, notes, summaries, interview prompts, analytics, and sample seeding.

```powershell
cd frontend
npm run lint
npm run build
```

## API Overview

All `/api/*` application endpoints except `/api/auth/register` and `/api/auth/login` require `Authorization: Bearer <token>`. JSON validation errors use HTTP 422; unauthenticated requests return 401; missing/foreign-owned resources return 404.

| Method and path | Operation |
| --- | --- |
| `POST /api/auth/register`, `POST /api/auth/login`, `GET /api/auth/me` | Recruiter identity and JWT |
| `POST/GET /api/jobs`, `GET/PUT/DELETE /api/jobs/{job_id}` | Job lifecycle |
| `POST /api/jobs/{job_id}/match` | Recalculate all matches for a role |
| `GET /api/jobs/{job_id}/candidates`, `GET /api/jobs/{job_id}/ranking` | Filtered candidates and score-ranked candidates |
| `POST /api/resumes/upload` | Upload one resume (`job_id`, `file` multipart fields) |
| `POST /api/resumes/upload-multiple` | Upload multiple resumes (`job_id`, repeated `files` multipart fields); returns per-file results/errors |
| `GET/DELETE /api/resumes/{resume_id}` | Inspect extracted text or delete an owned resume |
| `GET /api/candidates`, `GET/PUT /api/candidates/{candidate_id}` | Search/filter profiles and update application status |
| `POST /api/candidates/{candidate_id}/applications/{application_id}/notes` | Add a recruiter note |
| `POST /api/candidates/{candidate_id}/applications/{application_id}/summary` | Generate grounded candidate summary |
| `POST /api/candidates/{candidate_id}/applications/{application_id}/interview-questions` | Create technical, project, and behavioral prompts |
| `GET /api/analytics/dashboard`, `GET /api/analytics/jobs/{job_id}` | Workspace/job aggregate metrics |
| `POST /api/demo/seed` | Create synthetic demonstration records once per workspace |

Example create-job request:

```json
{
  "title": "Python Developer",
  "company": "Example Co",
  "location": "Remote",
  "employment_type": "Full-time",
  "experience_required": 2,
  "description": "Build Python services with FastAPI, SQL, REST APIs, and Git.",
  "required_skills": ["Python", "FastAPI", "SQL", "REST API", "Git"],
  "preferred_skills": ["Docker", "AWS"]
}
```

Success responses return JSON resources and 201 on creation/upload. Deletes return 204. Upload batches return `processed`, `failed`, `results`, and `errors`; one invalid file does not roll back other successfully processed files.

## NLP and Matching Methodology

1. PyMuPDF extracts PDF text; python-docx extracts DOCX paragraphs/tables. Scanned image-only PDFs return a clear unreadable-text error; OCR is not enabled by default.
2. Text is whitespace-normalized and recognized section headings are mapped to summary, skills, experience, education, projects, and certifications. Regexes detect email, phone, links, stated years, degree labels, graduation year, and GPA when present. Missing fields remain null/empty or `Not detected`.
3. A categorized, configurable skill vocabulary detects programming, web, database, AI/ML, cloud, DevOps, and analytics skills. It is deterministic and avoids protected-characteristic extraction.
4. Skill score gives required skills 80% and preferred skills 20% when both are provided; required-only roles use required coverage. Missing required skills are returned explicitly.
5. Final score: skills 35%, resume/JD semantic similarity 25%, experience 15%, education 10%, project relevance 10%, and certification relevance 5%. TF-IDF word/bigram cosine similarity is the default; `requirements-ml.txt` enables cached `all-MiniLM-L6-v2` embeddings as an optional local semantic path. Optional vectors are cached and stored in the match record only when that mode is enabled.
6. Every score exposes its six component percentages, matched/missing skills, and evidence-based explanations. Adjust weights in `backend/app/ml/matching.py` for experiments and document any change.

Scores are prioritization aids, not hiring decisions. A similarity score is not a probability of performance or a validated measure of job success. Recruiters must review underlying evidence and apply consistent, job-related criteria.

## Data Model

`users` own `jobs` and `candidates`. Each `candidate` has resumes plus normalized candidate skills, experience entries, education, projects, and certifications. `skills` is a reusable vocabulary referenced through `candidate_skills` and `job_skills` join tables. `applications` connect candidates to jobs and track status/note. Each application can have one `match_results` record and many `recruiter_notes`. Foreign keys and indexes support ownership checks, ranking, and status queries. ORM queries are parameterized through SQLAlchemy.

## Deploy

- **Frontend:** `frontend/` is a standard Vite build suitable for Vercel static hosting. Set `VITE_API_URL` to the deployed API origin and configure matching backend CORS origins.
- **Backend:** `backend/Dockerfile` is a non-root FastAPI image. Set a strong `SECRET_KEY`, PostgreSQL `DATABASE_URL`, upload storage, CORS origins, and any optional LLM variables. Use a persistent private volume/object store for uploaded resumes.
- **Database:** Use managed PostgreSQL with backups and TLS in production. Run `alembic upgrade head` as a release step.
- Resume documents and candidate data are sensitive: configure retention, access controls, encryption, logging redaction, and legal/privacy review before a production hiring deployment.

## Screenshots

Add current recruiter-dashboard and candidate-profile screenshots here after launching locally.

## Troubleshooting

- **Frontend cannot reach the API:** confirm backend is on port 8000, `VITE_API_URL` is correct, and the origin is in `CORS_ORIGINS`.
- **Resume upload fails:** use a readable PDF/DOCX under 10 MiB. Image-only scanned PDFs need OCR, which is intentionally not represented as successful extraction.
- **Docker Compose cannot connect:** start Docker Desktop and wait for the Linux engine before retrying.
- **Sentence-transformer model is unavailable:** install `backend/requirements-ml.txt` and enable `USE_SENTENCE_TRANSFORMERS=true`; a model download is needed on first use. Otherwise TF-IDF works offline.
- **LLM summaries use local fallback:** configure both `LLM_API_KEY` and `LLM_BASE_URL`; upstream errors/timeouts fall back to deterministic summaries.
- **Database schema changed:** from `backend/`, run `alembic upgrade head` after adding a migration. SQLite files are local development state and can be removed only when you intend to reset local records.

## Future Improvements

- Add OCR through an explicitly configured local OCR service, asynchronous queue processing, malware scanning, and object storage.
- Add pgvector indexing for large-scale candidate search, with re-index jobs and tenant-scoped access controls.
- Improve section/entity extraction with a validated spaCy pipeline and structured date-range parsing.
- Add formal retention/export/delete workflows, audit trails, role permissions, reviewer calibration, and fairness monitoring reviewed by qualified experts.
- Add richer frontend integration tests and production monitoring/alerting.
#   A i - R e s u m e - S c r e e n i n g - S y s t e m  
 