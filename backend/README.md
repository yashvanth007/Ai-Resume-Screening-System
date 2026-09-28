# Backend

FastAPI service for authentication, job management, resume parsing, candidate matching, and analytics.

From this directory:

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item ..\.env.example .env
python -m uvicorn app.main:app --reload --port 8000
```

Run `python -m pytest -q` for the backend suite. OpenAPI documentation is served at `/docs`. SQLite and `create_all` are used for simple local startup; PostgreSQL deployments should run `alembic upgrade head` as a release step. Optional semantic model dependencies are in `requirements-ml.txt`.
# Example