# Grocery App

An existing Django recipe catalog and grocery-list builder, being modernized on
`development`. The original `master` branch is preserved.

- [Project requirements](PROJECT_REQUIREMENTS.md)
- [Fresh WSL Ubuntu development setup](docs/DEVELOPMENT.md)
- [Repository assessment and remaining Phase 1 work](docs/REPOSITORY_ASSESSMENT.md)
- [Preserving and recovering legacy data](docs/DATA_RECOVERY.md)

Use Python 3.12–3.14, Django 5.2 LTS, and PostgreSQL 16. Run tests before pushing:

```bash
source .venv/bin/activate
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

These commands require the local environment described in the setup guide. CI
also tests an explicit SQLite fallback. Nothing in this repository deploys to
TrueNAS or production.
