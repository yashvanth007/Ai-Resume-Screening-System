import os
from pathlib import Path

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_screening.db")
os.environ.setdefault("UPLOAD_DIR", "./test_uploads")
os.environ.setdefault("SECRET_KEY", "test-secret-do-not-use-in-production")

import pytest
from fastapi.testclient import TestClient

from app.database.session import Base, engine
from app.main import app
from app.models import models  # noqa: F401


@pytest.fixture
def client():
    Base.metadata.drop_all(bind=engine)
    with TestClient(app) as test_client:
        yield test_client
    Base.metadata.drop_all(bind=engine)
    upload_dir = Path(os.environ["UPLOAD_DIR"])
    if upload_dir.exists():
        for path in upload_dir.iterdir():
            path.unlink()
        upload_dir.rmdir()
