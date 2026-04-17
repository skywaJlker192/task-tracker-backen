import json
import re
from datetime import datetime, timedelta, timezone
from typing import List, Optional

import redis
from fastapi import APIRouter, Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, ConfigDict, field_validator
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, create_engine, or_
from sqlalchemy.orm import Session, declarative_base, relationship, sessionmaker

# ==========================================================
# CONFIG
# ==========================================================

DATABASE_URL = "sqlite:///./app.db"
SECRET_KEY = "super_secret_key_for_demo_project_change_me"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REDIS_URL = "redis://localhost:6379/0"

# ==========================================================
# DB
# ==========================================================

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()

# ==========================================================
# REDIS
# ==========================================================

def get_redis_client():
    try:
        client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
        client.ping()
        return client
    except Exception:
        return None

redis_client = get_redis_client()

# ==========================================================
# MODELS
# ==========================================================

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    phone = Column(String(20), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), default="user", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    tasks = relationship("Task", back_populates="owner", cascade="all, delete")


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, default="")
    status = Column(String(30), default="new", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    owner = relationship("User", back_populates="tasks")

# ==========================================================
# Pydantic SCHEMAS
# ==========================================================

class RegisterRequest(BaseModel):
    email: str
    username: str
    phone: str
    password: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
        if not re.match(pattern, value):
            raise ValueError("Некорректный email")
        return value

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        pattern = r"^[a-zA-Z][a-zA-Z0-9_]{2,19}$"
        if not re.match(pattern, value):
            raise ValueError("Username должен начинаться с буквы и содержать 3-20 символов")
        return value

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        pattern = r"^\+7-\d{3}-\d{3}-\d{2}-\d{2}$"
        if not re.match(pattern, value):
            raise ValueError("Телефон должен быть в формате +7-900-123-45-67")
        return value

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if len(value) < 8:
            raise ValueError("Пароль должен содержать минимум 8 символов")
        if not re.search(r"[A-Z]", value):
            raise ValueError("Пароль должен содержать хотя бы одну заглавную букву")
        if not re.search(r"[a-z]", value):
            raise ValueError("Пароль должен содержать хотя бы одну строчную букву")
        if not re.search(r"\d", value):
            raise ValueError("Пароль должен содержать хотя бы одну цифру")
        return value


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: int
    email: str
    username: str
    phone: str
    role: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = ""

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        if len(value.strip()) < 3:
            raise ValueError("Название задачи должно содержать минимум 3 символа")
        return value.strip()


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        allowed = {"new", "in_progress", "done"}
        if value not in allowed:
            raise ValueError(f"Статус должен быть одним из: {allowed}")
        return value


class TaskOut(BaseModel):
    id: int
    title: str
    description: str
    status: str
    owner_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# ==========================================================
# SECURITY
# ==========================================================

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_minutes: int = ACCESS_TOKEN_EXPIRE_MINUTES) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Некорректный или просроченный токен"
        )

# ==========================================================
# REPOSITORIES
# ==========================================================

class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_email(self, email: str):
        return self.db.query(User).filter(User.email == email).first()

    def get_by_username(self, username: str):
        return self.db.query(User).filter(User.username == username).first()

    def get_by_login(self, login: str):
        return self.db.query(User).filter(
            or_(User.email == login, User.username == login)
        ).first()

    def get_by_id(self, user_id: int):
        return self.db.query(User).filter(User.id == user_id).first()

    def list_all(self):
        return self.db.query(User).all()

    def create(self, email: str, username: str, phone: str, password: str, role: str = "user"):
        user = User(
            email=email,
            username=username,
            phone=phone,
            hashed_password=hash_password(password),
            role=role
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user


class TaskRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, owner_id: int, title: str, description: str = ""):
        task = Task(
            owner_id=owner_id,
            title=title,
            description=description,
            status="new"
        )
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return task

    def get_by_id(self, task_id: int):
        return self.db.query(Task).filter(Task.id == task_id).first()

    def list_by_owner(self, owner_id: int):
        return self.db.query(Task).filter(Task.owner_id == owner_id).all()

    def update(self, task: Task):
        self.db.commit()
        self.db.refresh(task)
        return task

    def delete(self, task: Task):
        self.db.delete(task)
        self.db.commit()

# ==========================================================
# SERVICES
# ==========================================================

class AuthService:
    def __init__(self, db: Session):
        self.user_repo = UserRepository(db)

    def register_user(self, data: RegisterRequest):
        if self.user_repo.get_by_email(data.email):
            raise HTTPException(status_code=400, detail="Email уже используется")
        if self.user_repo.get_by_username(data.username):
            raise HTTPException(status_code=400, detail="Username уже используется")

        return self.user_repo.create(
            email=data.email,
            username=data.username,
            phone=data.phone,
            password=data.password
        )

    def authenticate_user(self, login: str, password: str):
        user = self.user_repo.get_by_login(login)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user


class TaskService:
    def __init__(self, db: Session):
        self.task_repo = TaskRepository(db)

    def _cache_key(self, user_id: int) -> str:
        return f"user:{user_id}:tasks"

    def _serialize_task(self, task: Task) -> dict:
        return {
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "status": task.status,
            "owner_id": task.owner_id,
            "created_at": task.created_at.isoformat()
        }

    def _invalidate_tasks_cache(self, user_id: int):
        if redis_client:
            redis_client.delete(self._cache_key(user_id))

    def create_task(self, user_id: int, data: TaskCreate):
        task = self.task_repo.create(
            owner_id=user_id,
            title=data.title,
            description=data.description or ""
        )
        self._invalidate_tasks_cache(user_id)
        return task

    def list_tasks(self, user_id: int):
        cache_key = self._cache_key(user_id)

        if redis_client:
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)

        tasks = self.task_repo.list_by_owner(user_id)
        result = [self._serialize_task(task) for task in tasks]

        if redis_client:
            redis_client.setex(cache_key, 60, json.dumps(result, ensure_ascii=False))

        return result

    def get_task_for_user(self, task_id: int, current_user: User):
        task = self.task_repo.get_by_id(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Задача не найдена")

        if task.owner_id != current_user.id and current_user.role != "admin":
            raise HTTPException(status_code=403, detail="Нет доступа к задаче")

        return task

    def update_task(self, task_id: int, data: TaskUpdate, current_user: User):
        task = self.get_task_for_user(task_id, current_user)

        if data.title is not None:
            task.title = data.title
        if data.description is not None:
            task.description = data.description
        if data.status is not None:
            task.status = data.status

        updated_task = self.task_repo.update(task)
        self._invalidate_tasks_cache(updated_task.owner_id)
        return updated_task

    def delete_task(self, task_id: int, current_user: User):
        task = self.get_task_for_user(task_id, current_user)
        owner_id = task.owner_id
        self.task_repo.delete(task)
        self._invalidate_tasks_cache(owner_id)

# ==========================================================
# DEPENDENCIES
# ==========================================================

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    payload = decode_access_token(token)
    user_id = payload.get("sub")

    if user_id is None:
        raise HTTPException(status_code=401, detail="Токен не содержит пользователя")

    user = UserRepository(db).get_by_id(int(user_id))
    if not user:
        raise HTTPException(status_code=401, detail="Пользователь не найден")

    return user


def get_current_admin(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Доступ только для администратора")
    return current_user

# ==========================================================
# ROUTERS
# ==========================================================

auth_router = APIRouter(prefix="/auth", tags=["Auth"])
tasks_router = APIRouter(prefix="/tasks", tags=["Tasks"])
admin_router = APIRouter(prefix="/admin", tags=["Admin"])


@auth_router.post("/register", response_model=UserOut, status_code=201)
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    service = AuthService(db)
    return service.register_user(data)


@auth_router.post("/login", response_model=LoginResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    service = AuthService(db)
    user = service.authenticate_user(form_data.username, form_data.password)

    if not user:
        raise HTTPException(status_code=401, detail="Неверный логин или пароль")

    token = create_access_token({
        "sub": str(user.id),
        "role": user.role,
        "username": user.username
    })

    return {"access_token": token, "token_type": "bearer"}


@auth_router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user


@tasks_router.post("/", response_model=TaskOut, status_code=201)
def create_task(
    data: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = TaskService(db)
    return service.create_task(current_user.id, data)


@tasks_router.get("/", response_model=List[TaskOut])
def list_tasks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = TaskService(db)
    return service.list_tasks(current_user.id)


@tasks_router.get("/{task_id}", response_model=TaskOut)
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = TaskService(db)
    return service.get_task_for_user(task_id, current_user)


@tasks_router.patch("/{task_id}", response_model=TaskOut)
def update_task(
    task_id: int,
    data: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = TaskService(db)
    return service.update_task(task_id, data, current_user)


@tasks_router.delete("/{task_id}")
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = TaskService(db)
    service.delete_task(task_id, current_user)
    return {"message": "Задача удалена"}


@admin_router.get("/users", response_model=List[UserOut])
def list_users(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin)
):
    return UserRepository(db).list_all()

# ==========================================================
# APP
# ==========================================================

app = FastAPI(title="Task Tracker API", version="1.0.0")

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        repo = UserRepository(db)
        admin = repo.get_by_username("admin")
        if not admin:
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


# ←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←
# ВАЖНО: подключаем роутеры с префиксами!
app.include_router(auth_router, prefix="/auth", tags=["Auth"])
app.include_router(tasks_router, prefix="/tasks", tags=["Tasks"])
app.include_router(admin_router, prefix="/admin", tags=["Admin"])