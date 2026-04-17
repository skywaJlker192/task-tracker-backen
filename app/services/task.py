import json
from app.repositories.task import TaskRepository
from app.schemas.task import TaskCreate, TaskUpdate
from app.core.redis import redis_client
from fastapi import HTTPException

class TaskService:
    def __init__(self, db):
        self.task_repo = TaskRepository(db)

    def _cache_key(self, user_id: int):
        return f"user:{user_id}:tasks"

    def create_task(self, user_id: int, data: TaskCreate):
        task = self.task_repo.create(user_id, data.title, data.description or "")
        if redis_client:
            redis_client.delete(self._cache_key(user_id))
        return task

    def list_tasks(self, user_id: int):
        cache_key = self._cache_key(user_id)

        if redis_client:
            try:
                cached = redis_client.get(cache_key)
                if cached:
                    return json.loads(cached)
            except:
                pass  # если redis упал - работаем без кэша

        tasks = self.task_repo.list_by_owner(user_id)
        result = [task.__dict__ for task in tasks]

        if redis_client:
            try:
                redis_client.setex(cache_key, 60, json.dumps(result, default=str))
            except:
                pass

        return result

    def get_task_for_user(self, task_id: int, current_user):
        task = self.task_repo.get_by_id(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Задача не найдена")

        if task.owner_id != current_user.id and current_user.role != "admin":
            raise HTTPException(status_code=403, detail="У вас нет доступа к этой задаче")

        return task