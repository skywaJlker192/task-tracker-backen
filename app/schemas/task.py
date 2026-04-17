from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = ""

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None

class TaskOut(BaseModel):
    id: int
    title: str
    description: str
    status: str
    owner_id: int
    created_at: datetime

    class Config:
        from_attributes = True