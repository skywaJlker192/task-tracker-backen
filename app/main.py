from fastapi import FastAPI
from app.core.database import Base, engine
from app.routers import auth, tasks, admin
import app.models.user
import app.models.task

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Task Tracker API", version="1.0.0")
# Главный файл приложения - подключаем все роутеры

@app.on_event("startup")
def on_startup():
    from app.core.database import SessionLocal
    from app.repositories.user import UserRepository

    db = SessionLocal()
    try:
        repo = UserRepository(db)
        if not repo.get_by_username("admin"):
            repo.create(
                email="admin@example.com",
                username="admin",
                phone="+7-900-000-00-00",
                password="Admin123",
                role="admin"
            )
    finally:
        db.close()


@app.get("/")
def root():
    return {"message": "Task Tracker API is running"}


# Подключаем роутеры
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(tasks.router, prefix="/tasks", tags=["Tasks"])
app.include_router(admin.router, prefix="/admin", tags=["Admin"])