# AI Agent Instructions

## Project overview
- This is a minimal Django project scaffold created with `django-admin startproject config .`.
- The root entrypoint is `manage.py`.
- The Django settings live in `config/settings.py` and currently use SQLite (`db.sqlite3`) and `DEBUG = True`.
- There are no custom Django apps registered in `INSTALLED_APPS` yet.

## Environment & dependencies
- Target Python version: `3.13`.
- Use a local virtual environment in `.venv`.
- Install dependencies from `requirements.txt`.

## Recommended local workflow
- Create the venv: `python -m venv .venv`
- Activate on Windows: `./.venv/Scripts/activate`
- Install requirements: `python -m pip install -r requirements.txt`
- Apply migrations: `python manage.py migrate`
- Run local server: `python manage.py runserver`

## Key files
- `manage.py` - Django CLI entrypoint.
- `config/settings.py` - application settings and installed apps.
- `config/urls.py` - URL routing entrypoint.
- `config/wsgi.py` / `config/asgi.py` - deployment interfaces.
- `requirements.txt` - dependency list.
- `README.md` - project summary and installation instructions.

## How to contribute
- If adding features, create new Django apps with `python manage.py startapp <app_name>` and register them in `INSTALLED_APPS`.
- Keep changes consistent with Django conventions: models in `models.py`, views in `views.py`, urls in `urls.py`, templates under app `templates/` if needed.
- Avoid hardcoding production secrets in `config/settings.py`.

## Notes for AI agents
- The repo is currently a base Django project rather than a completed application.
- Prefer minimal, safe changes that preserve Django defaults until a custom app structure is established.
- Do not assume additional configuration files, linting, or test frameworks exist beyond standard Django.
