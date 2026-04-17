from fastapi import APIRouter, Depends
from app.repositories.user import UserRepository
from app.core.database import get_db
from app.dependencies.auth import get_current_admin
from sqlalchemy.orm import Session

router = APIRouter()

@router.get("/users")
def list_users(db: Session = Depends(get_db), admin = Depends(get_current_admin)):
    return UserRepository(db).list_all()