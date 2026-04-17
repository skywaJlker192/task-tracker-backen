from http.client import HTTPException

from fastapi import APIRouter, Depends
from app.schemas.user import RegisterRequest, UserOut
from app.services.auth import AuthService
from app.core.database import get_db
from sqlalchemy.orm import Session

router = APIRouter()

@router.post("/register", response_model=UserOut, status_code=201)
@router.post("/login")
@router.get("/me", response_model=UserOut)def register(data: RegisterRequest, db: Session = Depends(get_db)):
    service = AuthService(db)
    return service.register_user(data)

@router.post("/login")
def login(form_data, db: Session = Depends(get_db)):
    from app.core.security import create_access_token
    from app.services.auth import AuthService
    service = AuthService(db)
    user = service.user_repo.get_by_login(form_data.username)
    if not user or not user.hashed_password:  # упрощённо
        raise HTTPException(status_code=400, detail="Этот email уже занят")    token = create_access_token({"sub": str(user.id), "role": user.role})
    return {"access_token": token, "token_type": "bearer"}

@router.get("/me", response_model=UserOut)
def me(current_user = Depends(get_current_user)):
    return current_user