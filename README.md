# Django Game Store

Проект интернет-магазина игр на Django с веб-интерфейсом и JSON API.

## Что реализовано
- Каталог игр (жанры, платформы, теги, издатели, карточка игры).
- Отзывы и избранное.
- Корзина и оформление заказа.
- Роли через группы (`client`, `manager`) и менеджерское управление заказами.
- JSON API в `api_app`.

## Технологии
- Python
- Django
- SQLite / PostgreSQL
- Gunicorn

## Быстрый старт (локально)
1. `python -m venv venv`
2. `venv\Scripts\activate` (Windows) или `source venv/bin/activate` (Linux/macOS)
3. `pip install -r requirements.txt`
4. `python manage.py migrate`
5. `python manage.py runserver`

## Переменные окружения
Пример смотри в `.env.example`.

Основные:
- `SECRET_KEY`
- `DEBUG`
- `ALLOWED_HOSTS`
- `CSRF_TRUSTED_ORIGINS`
- `DATABASE_URL` (опционально, для PostgreSQL)

Если `DATABASE_URL` не задана, используется SQLite.

## API Endpoints
- `GET /api/health/`
- `GET /api/games/`
- `GET /api/games/<slug>/`
- `GET /api/genres/`
- `GET /api/platforms/`
- `POST /api/games/<slug>/favorite/` (auth)
- `POST /api/games/<slug>/review/` (auth)
- `DELETE /api/games/<slug>/review/` (auth)

Формат ответа:
`{"ok": true/false, "data": ..., "error": ...}`

## Роли
- `client`: базовая роль пользователя.
- `manager`: управление заказами.
- `superuser`: полный доступ.

## Деплой (Render/Railway/VPS)
- Используется `Procfile`: `web: gunicorn config.wsgi:application`
- Перед запуском:
  - применить миграции
  - выполнить сбор статики
