from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import current_user
from app.database.session import get_db
from app.models import User
from app.services.demo_data import seed_demo

router = APIRouter(prefix="/api/demo", tags=["demo data"])


@router.post("/seed")
def load_demo_data(db: Session = Depends(get_db), user: User = Depends(current_user)):
    return seed_demo(db, user.id)
