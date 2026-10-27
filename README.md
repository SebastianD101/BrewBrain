# ☕ BrewBrain

[![CI](https://github.com/SebastianD101/BrewBrain/actions/workflows/ci.yml/badge.svg)](https://github.com/SebastianD101/BrewBrain/actions/workflows/ci.yml)
![Python 3.12](https://img.shields.io/badge/python-3.12-blue)
![Django 5.2](https://img.shields.io/badge/django-5.2%20LTS-0C4B33)

**BrewBrain is an espresso shot journal that learns from your own shots.** Log the recipe
(grind, dose, time and temperature) along with how the shot tasted. BrewBrain then trains a
model on your history to predict how a new recipe will taste and to suggest the grind and
shot time most likely to come out balanced.

Dialling in espresso usually means changing one variable at a time and wasting beans. BrewBrain
uses the shots you've already pulled to make that search shorter.

## Features

- **Shot log**: record shots with server-side validation. The form is pre-filled from your last
  shot, since recipes usually change a little at a time. Shots show their brew ratio and stack
  into cards on mobile.
- **Outcome prediction**: enter a recipe to get its predicted yield, its sour↔bitter balance and its strength.
- **Dial-in suggestions**: keeping your dose and water temperature fixed, the app searches the grind
  sizes and shot times you've used for the recipe predicted closest to balanced.
- **Model transparency**: the app shows 5-fold cross-validated error and which recipe variables
  matter most in *your* data.
- **CSV import/export**: imports report errors row by row and skip bad rows. Imports also read
  files from the original 2024 version of BrewBrain.
- **Demo data**: `seed_demo_shots` creates realistic synthetic shots so you can try the
  predictor right away.

## How the model works

| Inputs (what you control) | Outputs (what it predicts) |
| --- | --- |
| Grind size, dose (g), extraction time (s), water temp (°C) | Yield (g), taste (1 sour – 5 bitter), strength (1 weak – 5 strong) |

A multi-output `RandomForestRegressor` from scikit-learn is trained on the user's logged shots.
Random forests suit this problem because home datasets are small (tens of shots), the
relationships are non-linear (grind affects taste through shot time), and no feature scaling is
needed.

- The model is retrained on every visit to the prediction page, so a newly logged shot counts
  straight away. At home-barista data sizes this takes well under a second.
- Predictions unlock after 5 shots. Cross-validated error is shown from 10 shots on.
- Dial-in suggestions come from a 25×25 grid search over grind size and shot time. The search
  stays **within the range you've actually brewed**, because tree models can't extrapolate.

All of this lives in [`espresso_log/ml.py`](espresso_log/ml.py) and is unit-tested on its own,
separate from Django views.

## Tech stack

Python 3.12 · Django 5.2 LTS · scikit-learn · NumPy · Bootstrap 5 · SQLite · pytest · Ruff ·
uv · GitHub Actions · Docker + Gunicorn + WhiteNoise

## Getting started

Requires [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/SebastianD101/BrewBrain.git
cd BrewBrain
cp .env.example .env                       # local dev settings (DEBUG on)
uv sync
uv run python manage.py migrate
uv run python manage.py seed_demo_shots    # optional: 60 synthetic shots
uv run python manage.py runserver
```

Open http://127.0.0.1:8000. Run `uv run python manage.py createsuperuser` to use the Django
admin at `/admin/`.

### Tests and linting

```bash
uv run pytest            # unit + view tests with coverage
uv run ruff check .
uv run ruff format --check .
```

CI runs all of the above on every push and pull request, and also checks for missing migrations.

### Docker

```bash
docker build -t brewbrain .
docker run -p 8000:8000 -e DJANGO_SECRET_KEY=$(openssl rand -hex 32) \
  -e DJANGO_ALLOWED_HOSTS=localhost -e DJANGO_SECURE_SSL_REDIRECT=0 \
  -v brewbrain-data:/data brewbrain
```

## Configuration

All settings come from environment variables (or `.env`):

| Variable | Default | Purpose |
| --- | --- | --- |
| `DJANGO_DEBUG` | `0` | Development mode |
| `DJANGO_SECRET_KEY` | — | Required when debug is off |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1` | Comma-separated hostnames |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | — | e.g. `https://brewbrain.example.com` |
| `DJANGO_DB_PATH` | `./db.sqlite3` | SQLite database location |
| `DJANGO_SECURE_SSL_REDIRECT` | `1` | Redirect HTTP to HTTPS when debug is off |
| `DJANGO_HSTS_SECONDS` | `0` | HSTS max-age once HTTPS is confirmed |

## Project structure

```
config/                  Django project settings, URLs, WSGI/ASGI
espresso_log/
├── models.py            EspressoShot model with validation
├── ml.py                training, prediction and dial-in search
├── csv_io.py            CSV import (current + legacy formats) and export
├── views.py, forms.py   server-rendered pages
├── templates/, static/
├── management/commands/seed_demo_shots.py
└── tests/               pytest suite for the ML, CSV and views
```

## Roadmap

- User accounts, so each person has their own shot history and model
- Tracking beans as their own records, with roast date (bean age has a big effect on extraction)
- Charts of taste versus shot time for each bean
