# GameStore (BBGame)

GameStore is a Django web application for browsing games, adding them to favorites/cart, creating orders, and using a JSON API.

## Current Scope

- Catalog: games, publishers, genres, platforms, tags.
- User flows: registration, login/logout, profile, favorites, reviews.
- Commerce flows: cart, checkout, orders, manager order processing.
- Content: news pages, FAQ, static pages.
- API (`api_app`): health, games list/detail, genres/platforms, favorite/review actions.

## Tech Stack

- Python 3
- Django 6
- SQLite (local)
- Cloudinary (`django-cloudinary-storage`) for media files
- Gunicorn (for production process)

## Apps

- `core`
- `pages`
- `taxonomy`
- `catalog`
- `accounts`
- `favorites`
- `reviews`
- `cart`
- `orders`
- `api_app`

## Local Run

1. Create and activate virtual environment:

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/macOS
source venv/bin/activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Apply migrations:

```bash
python manage.py makemigrations
python manage.py migrate
```

4. Create admin user:

```bash
python manage.py createsuperuser
```

5. (Optional) Fill test data:

```bash
python manage.py seed
```

6. Run server:

```bash
python manage.py runserver
```

## Environment Variables

Create `.env` from `.env.example`.

Minimal variables:

- `SECRET_KEY`
- `DEBUG`
- `ALLOWED_HOSTS`
- `CSRF_TRUSTED_ORIGINS`
- `DATABASE_URL` (optional for PostgreSQL)
- `DB_SSL_REQUIRE` (optional)
- `CLOUDINARY_CLOUD_NAME`
- `CLOUDINARY_API_KEY`
- `CLOUDINARY_API_SECRET`

## Main URLs

- `/` home
- `/shop/` catalog
- `/product/<slug>/` product details
- `/favorites/`
- `/cart/`
- `/orders/`
- `/profile/`
- `/faq/`

## API Endpoints

- `GET /api/health/`
- `GET /api/games/`
- `GET /api/games/<slug>/`
- `GET /api/genres/`
- `GET /api/platforms/`
- `POST /api/games/<slug>/favorite/` (auth)
- `POST /api/games/<slug>/review/` (auth)
- `DELETE /api/games/<slug>/review/` (auth)

JSON format:

```json
{"ok": true, "data": {}, "error": null}
```

## Roles and Access

- `client`: default user role.
- `manager`: order management permissions.
- `superuser`: full access (admin + manager capabilities).

## Deployment (Render / Railway / VPS)

`Procfile`:

```text
web: gunicorn config.wsgi:application
```

Production checklist:

1. Set `DEBUG=False`.
2. Configure `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS`.
3. Configure production database (recommended: PostgreSQL).
4. Run migrations on server:

```bash
python manage.py migrate
```

5. Collect static files:

```bash
python manage.py collectstatic --noinput
```

6. Start app with Gunicorn:

```bash
gunicorn config.wsgi:application
```

## Logs and Monitoring

### Local

- Run: `python manage.py runserver`
- Logs are printed to console.

### VPS with systemd + Gunicorn (example)

- App logs:

```bash
journalctl -u gunicorn -f
```

- Nginx logs:

```bash
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

### Render / Railway

- Use platform dashboard logs section.

## Backup Strategy

### SQLite (local/dev)

Backup:

```bash
copy db.sqlite3 db.sqlite3.bak
```

Restore:

```bash
copy /Y db.sqlite3.bak db.sqlite3
```

### PostgreSQL (production)

Backup:

```bash
pg_dump "$DATABASE_URL" > backup.sql
```

Restore:

```bash
psql "$DATABASE_URL" < backup.sql
```

Recommended practice:

- Keep regular backups (daily/weekly depending on activity).
- Store backups outside the app server.
- Periodically test restore on a staging environment.

## Useful Commands

```bash
python manage.py check
python manage.py showmigrations
python manage.py shell
```

## Notes

- If static or media is not displayed, verify `STATICFILES_DIRS`, Cloudinary variables, and collectstatic step.
- If SQLite reports `disk I/O error`, check file permissions, disk health, and avoid cloud-sync locking on DB file.
