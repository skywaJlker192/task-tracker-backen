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
![img.png](swagger.png)
### 2. Успешная регистрация
![img_1.png](register.png)
### 3. Успешный вход и токен
![img_2.png](login.png)
### 4. GET /auth/me
![img_3.png](me.png)
### 5. Создание задачи
![img_4.png](task_create.png)
### 6. Список задач
![img_5.png](task_list.png)
### 7. Админка /admin/users
![img_6.png](adminka.png)
### 8. Docker контейнеры
![img_7.png](docker.png)
### Как запустить

**Обычный запуск:**
```bash
pip install -r requirements.txt
python -m uvicorn app.main:app --reload