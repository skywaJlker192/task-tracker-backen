from pydantic_settings import BaseSettingss
# Конфигурация проекта
# Здесь хранятся все настройки: база данных, секретный ключ, Redis и т.д.
class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./app.db"
    SECRET_KEY: str = "super_secret_key_for_demo_project_change_me"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 50
    REDIS_URL: str = "redis://localhost:6379/0"

settings = Settings()