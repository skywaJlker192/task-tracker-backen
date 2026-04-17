## Task Tracker API

Простой бэкенд для управления задачами на FastAPI.

Я взял огромный монолитный main.py и разбил его по папкам, как  вы просили на практике.

### Что внутри
- Регистрация и логин
- JWT авторизация
- CRUD задач
- Redis кэширование списка задач
- Админка (GET /admin/users)
Сделал 8 коммитов во время рефакторинга :)
### Свагер
<img width="1261" height="664" alt="image" src="https://github.com/user-attachments/assets/c1e2d22c-460f-4f36-b684-d893539d6cc5" />
### 2. Успешная регистрация
<img width="809" height="815" alt="image" src="https://github.com/user-attachments/assets/50bb2d5b-1e07-4771-8911-6b453e3215af" />

### 3. Успешный вход и токен
<img width="882" height="814" alt="image" src="https://github.com/user-attachments/assets/aae419c7-9010-436b-9ac3-fb8d2b2752ba" />

### 4. GET /auth/me
<img width="915" height="478" alt="image" src="https://github.com/user-attachments/assets/09212d17-7fa9-4647-abc2-9ecf3bcdc1fc" />

### 5. Создание задачи
<img width="906" height="543" alt="image" src="https://github.com/user-attachments/assets/3743ced5-8bca-443a-8d5d-b6bb5705cca1" />

### 6. Список задач
<img width="834" height="815" alt="image" src="https://github.com/user-attachments/assets/a71e1bd2-5ae2-4b0f-8438-44d82403dcb9" />

### 7. Админка /admin/users
<img width="918" height="540" alt="image" src="https://github.com/user-attachments/assets/5540f7ca-a030-4c70-a60b-d49e5c73e2a5" />

### 8. Docker контейнеры
<img width="1263" height="718" alt="image" src="https://github.com/user-attachments/assets/adddffa4-d216-419e-82ad-c544a7b9b50f" />

### История коммитов
Сделал больше 15 коммитов во время рефакторинга монолита в нормальную структуру.

Проект полностью готов к сдаче:
- Нормальная файловая структура
- Запуск через Docker
- Все маршруты работают
- Swagger открыт
### Как запустить

**Обычный запуск:**
```bash
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
