from pydantic import BaseModel, EmailStr, field_validator
import re
from datetime import datetime

class RegisterRequest(BaseModel):
    email: EmailStr
    username: str
    phone: str
    password: str

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str):
        if not re.match(r"^[a-zA-Z][a-zA-Z0-9_]{2,19}$", value):
            raise ValueError("Username должен начинаться с буквы и содержать 3-20 символов")
        return value


class UserOut(BaseModel):
    id: int
    email: str
    username: str
    phone: str
    role: str
    created_at: datetime

    class Config:
        from_attributes = True