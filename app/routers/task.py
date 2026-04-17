from fastapi import APIRouter, Depends
from app.schemas.task import TaskCreate, TaskUpdate, TaskOut
from app.services.task import TaskService
from app.core.database import get_db
from app.dependencies.auth import get_current_user
from sqlalchemy.orm import Session

router = APIRouter()

@router.post("/", response_model=TaskOut, status_code=201)
def create_task(data: TaskCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    service = TaskService(db)
    return service.create_task(current_user.id, data)

@router.get("/", response_model=list)
def list_tasks(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    service = TaskService(db)
    return service.list_tasks(current_user.id)

@router.get("/{task_id}", response_model=TaskOut)
def get_task(task_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    service = TaskService(db)
    return service.get_task_for_user(task_id, current_user)

@router.patch("/{task_id}", response_model=TaskOut)
def update_task(task_id: int, data: TaskUpdate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    service = TaskService(db)
    task = service.get_task_for_user(task_id, current_user)
    if data.title is not None:
        task.title = data.title
    if data.description is not None:
        task.description = data.description
    if data.status is not None:
        task.status = data.status
    return service.task_repo.update(task)

@router.delete("/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    service = TaskService(db)
    service.get_task_for_user(task_id, current_user)  # проверка прав
    task = service.task_repo.get_by_id(task_id)
    service.task_repo.delete(task)
    return {"message": "Задача удалена"}