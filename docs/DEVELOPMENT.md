# Development on fresh WSL Ubuntu

Use a dedicated Ubuntu 24.04 WSL distribution or an isolated development machine.
These commands are for a fresh grocery-app environment, not an existing shared
PostgreSQL installation or the Kratos environment.

## Install and clone

In Windows PowerShell, install WSL if needed, then open Ubuntu:

```powershell
wsl --install -d Ubuntu-24.04
```

In Ubuntu:

```bash
sudo apt update
sudo apt install -y git python3 python3-venv python3-pip postgresql postgresql-client
mkdir -p ~/projects
cd ~/projects
git clone https://github.com/LetsCodeNow290/grocery_app.git
cd grocery_app
git switch development
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.lock
cp .env.example .env
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

Edit `.env`. Set `DJANGO_SECRET_KEY` to the generated value, enclosed in single
quotes so dotenv preserves characters such as `#`. Set a new database password.
The committed secret is compromised and must never be reused. Environment
variables override `.env`; never commit this file or credentials.

## Create an isolated PostgreSQL development database

On the fresh WSL installation only:

```bash
sudo service postgresql start
sudo -u postgres createuser --pwprompt --createdb grocery_app_dev
sudo -u postgres createdb --owner=grocery_app_dev grocery_app_dev
```

Use the password entered above for `POSTGRES_PASSWORD` in `.env`. `CREATEDB` is
needed for Django's disposable `test_grocery_app_dev` database in development;
production credentials should not have that privilege. The default connection
is TCP on `127.0.0.1:5432`. Keep it local.

## Run and verify

For a **new empty database**:

```bash
python manage.py check
python manage.py migrate --plan
python manage.py migrate
python manage.py makemigrations --check --dry-run
python manage.py test
python manage.py createsuperuser
python manage.py runserver 127.0.0.1:8000
```

Open <http://localhost:8000> in Windows. Use Manage Database to create a food
category, aisle, foods, and a recipe category before entering recipes. Create a
list, add foods or recipes, edit quantities, and download CSV. `/admin/` provides
Django administration. URL recipe importing is available at `/recipe/import/`;
see [RECIPE_IMPORTER.md](RECIPE_IMPORTER.md) for its review/save workflow and
ingredient limitations. Imported ingredients now have matching controls; see
[INGREDIENT_PROCESSING.md](INGREDIENT_PROCESSING.md). If a site blocks automatic downloads, use **Copy from
browser** on the same page to paste recipe text or supply a saved HTML/text file.
Photo/PDF importing is not available yet.

For an **existing database**, follow [DATA_RECOVERY.md](DATA_RECOVERY.md) before
applying migrations or loading fixtures. Do not run `initialize_data.py` or
`food_fix.py` against valuable data.

If PostgreSQL is unavailable, explicitly set `DB_ENGINE=sqlite` in `.env` and
use a **new** `SQLITE_PATH`. This is a local convenience, not the intended DEV
hosting database. No command here converts an existing database automatically.

## Daily development

```bash
source .venv/bin/activate
git switch development
python -m pip check
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

CI runs the suite on Python 3.12 and 3.14 with SQLite and PostgreSQL 16, checks
migration drift, and smoke-tests fresh migrations/static collection. It does not
deploy. After changing dependencies, resolve within `requirements.txt`, refresh
`requirements.lock` using `python -m pip freeze > requirements.lock` in a clean
venv, and test. `requirements.lock` records the tested exact versions, including
transitive dependencies.

Only the Django admin currently requires authentication; the original application
pages remain local household workflows. Keep the development server on loopback.
Before hosted DEV is established, add access control, TLS/proxy configuration,
media/static serving, and backups. Do not use Django's development server for
hosting. Review phone layouts on real devices; the foundation's responsive CSS
has automated rendering coverage but has not had device/browser acceptance tests.

The owner still needs to identify/back up the authoritative old database and media,
choose a separate DEV host, and configure repository CI/branch protections if
required. No TrueNAS or production deployment is authorized by this setup guide.
