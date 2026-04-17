from fastapi import HTTPException
from app.repositories.user import UserRepository
from app.schemas.user import RegisterRequest

class AuthService:
    def __init__(self, db):
        self.user_repo = UserRepository(db)

    def register_user(self, data: RegisterRequest):
        if self.user_repo.get_by_email(data.email):
            raise HTTPException(status_code=400, detail="Email уже используется")
        if self.user_repo.get_by_username(data.username):
            raise HTTPException(status_code=400, detail="Username уже используется")
        if len(data.password) < 8:
            raise HTTPException(status_code=400, detail="Пароль должен быть минимум 8 символов")

        return self.user_repo.create(
            email=data.email,
            username=data.username,
            phone=data.phone,
            password=data.password
        )