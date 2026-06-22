# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Dockerized Flask web app that converts text to speech via two interchangeable backends: **Azure OpenAI TTS** and **Azure Speech Service**. UI and voices are bilingual (Danish + UK English). The app runs in production behind an Nginx SSL reverse proxy with Gunicorn.

## Commands

Local development:
```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python app.py                 # Flask dev server on http://localhost:5000 (debug on unless FLASK_ENV=production)
```

Tests (pytest + pytest-mock):
```bash
pytest                        # run all
pytest tests/test_security.py # single file
pytest tests/test_app.py::test_name   # single test
```

Docker:
```bash
docker compose up -d          # production stack: nginx (SSL) + gunicorn app, https://localhost
docker compose -f dev/docker-compose.yml up   # dev: pulls ghcr.io image, hot-reload, auth disabled, port 5000
```

Config comes from a `.env` file (copy from `.env.example`). Without Azure credentials the app starts in **DEMO mode** — routes work but `/generate-speech` returns 503.

## Architecture

Three Python modules, no framework scaffolding:

- **`app.py`** — the entire web layer: config loading, all routes, security headers, audio cleanup. Single Flask app object; no blueprints.
- **`auth.py`** — SQLite user store (`data/users.db`). `init_db()` runs on import and creates the `users` table. Local users have salted Werkzeug password hashes; Azure AD users have `is_azure_ad=1` and no password.
- **`wsgi.py`** — Gunicorn entry point (`wsgi:app`). The Dockerfile CMD points here, not at `app.py`.

Key cross-cutting behaviors to understand before editing:

- **Authentication is conditional.** `REQUIRE_AUTHENTICATION` (env) toggles Flask-Login entirely. The `@conditional_login_required` decorator (not `@login_required`) wraps protected routes so they stay open when auth is off. When adding a protected route, use this decorator — never `@login_required` directly. Flask-Login's `LoginManager` and `@user_loader` are only initialized when auth is enabled.
- **Two auth paths.** Local username/password (`/login`, `/register`) and Azure AD OAuth via MSAL (`/login/azure` → `/login/azure/callback`, fetches profile from Microsoft Graph). `create_azure_ad_user` upserts by email.
- **TTS service dispatch** is inside `generate_speech` (`service` field: `openai` or `speech`). OpenAI path uses the `AzureOpenAI` SDK client; Speech path POSTs hand-built SSML to the regional REST endpoint. Speed maps differently per service (OpenAI takes `speed` directly; Speech converts to an SSML `prosody rate` percentage).
- **Voice lists** are defined as defaults in `app.py` and overridable via `SPEECH_SERVICE_VOICES` / `OPENAI_VOICES` env vars (JSON). Invalid JSON falls back to defaults with a warning.
- **Audio lifecycle.** Files are written to `data/audio/<uuid>.mp3`. `cleanup_old_audio_files()` deletes files older than `MAX_FILE_AGE_SECONDS` (default 1h) and runs on startup and after each generation. WAV downloads are produced on demand by shelling out to `ffmpeg` (must be present — it's installed in the Docker image).
- **Persistence is the `data/` directory** (gitignored): both `users.db` and `audio/` live there and are bind-mounted as a Docker volume so they survive container restarts.

## Security conventions (the app is security-focused; preserve these)

- Strict security headers (CSP, HSTS, X-Frame-Options, etc.) are applied globally via `@app.after_request`. The CSP is restrictive (`script-src 'self'`) — inline scripts will break.
- Open-redirect protection: post-login redirects pass through `is_safe_url()`. Reuse it for any new redirect that honors a `next` param.
- Audio-serving routes validate filenames against `^[a-f0-9\-]+\.mp3$` to prevent path traversal.
- Rate limiting via Flask-Limiter: global defaults plus `5 per minute` on `/generate-speech`. Storage is in-memory (`memory://`) — limits are per-process, so they reset on restart and aren't shared across Gunicorn workers.
- SSML text is HTML-escaped before interpolation; keep user input escaped when building SSML.

Snyk "security at inception" rules apply (`.agent/rules/snyk_rules.md`): run a Snyk code scan on newly generated first-party code, fix findings, and rescan until clean.

## Notes

- Many user-facing flash messages are in **Danish** — match that when editing login/register flows.
- The `users` table has no migration tooling; schema changes mean editing the `CREATE TABLE` in `init_db()` and handling existing DBs manually.
- See `DOCKER.md` for SSL cert setup and deployment details.
