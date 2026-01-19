# Text-to-Speech Application

A secure, Dockerized web application for converting text to speech using Azure OpenAI TTS and Azure Speech Service.

## Features

- 🎙️ **Dual TTS Services** - Azure OpenAI TTS & Azure Speech Service
- 🇩🇰 **Danish & UK English Support** - Bilingual UI & Voices
- 🔒 **Secure by Design** - SQLite storage, Flask-Limiter, Non-root containers
- ⏱️ **Rate Limiting** - 5 requests/min per user to protect API quotas
- 🐳 **Production Ready** - Docker Compose with Nginx SSL reverse proxy
- 💾 **Auto-Cleanup** - Audio files deleted after 1 hour

## Quick Start

### 1. Configure Credentials

Create a `.env` file from the example:

```bash
cp .env.example .env
```

Fill in your Azure credentials and preferred settings:
- `AZURE_OPENAI_API_KEY` / `AZURE_SPEECH_KEY`
- `REQUIRE_AUTHENTICATION=true`
- `ALLOW_REGISTRATION=true` (Disable after creating admin user)

### 2. Run with Docker

```bash
docker compose up -d
```

Access the app at `https://localhost` (or your configured domain).

*See [DOCKER.md](DOCKER.md) for detailed deployment and SSL instructions.*

## Development Setup (Local)

1. **Install Dependencies:**
   ```bash
   python3 -m venv venv && source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Run App:**
   ```bash
   python app.py
   ```
   Access at `http://localhost:5000`.

## Architecture

- **Backend:** Flask (Python 3.13) + Gunicorn
- **Database:** SQLite (`data/users.db`)
- **Frontend:** Vanilla JS + CSS
- **Proxy:** Nginx (Alpine) for SSL termination

## Security

- **Authentication:** Local (SQLite + Salted Hash) & Azure AD (Optional)
- **Rate Limiting:** Global and per-endpoint limits configured via Flask-Limiter
- **Container Security:** Non-root user execution, read-only root filesystem compatible

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.