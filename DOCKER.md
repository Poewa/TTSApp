# Docker Deployment Guide

## Quick Start

```bash
# 1. Setup environment
cp .env.example .env
# Edit .env with your Azure credentials

# 2. Start with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f
```

The app will be available at `http://localhost:5000`

### Using Docker Directly

```bash
docker build -t tts-poc .
docker run -d --name tts-poc -p 5000:5000 \
  -e AZURE_OPENAI_API_KEY="your-key" \
  -e AZURE_OPENAI_ENDPOINT="your-endpoint" \
  -e AZURE_SPEECH_KEY="your-speech-key" \
  -e AZURE_SPEECH_REGION="swedencentral" \
  tts-poc
```

## Security & Configuration

**Built-in Security:**
- Non-root user (UID 1000), Gunicorn WSGI server, rate limiting
- Security headers, 16MB request limit, SSL support, minimal image

**Environment Variables:**
- `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT` (required for OpenAI TTS)
- `AZURE_SPEECH_KEY`, `AZURE_SPEECH_REGION` (required for Speech Service)
- `AZURE_OPENAI_API_VERSION` (optional, defaults to 2025-03-01-preview)

**Production Recommendations:**
- Use Docker secrets instead of .env files
- Deploy behind HTTPS reverse proxy (Nginx/Traefik)
- Configure firewall rules and monitoring
- Set resource limits (see below)



## Resource Limits

Add to `docker-compose.yml`:

```yaml
services:
  web:
    # ... other config
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
```

## Troubleshooting

```bash
# Container won't start - check logs
docker-compose logs web

# Verify environment variables
docker-compose exec web env | grep AZURE

# Monitor resource usage
docker stats tts-poc

# View errors
docker-compose logs -f web | grep ERROR
```

**Common Issues:**
- Missing environment variables → Check .env file
- Port 5000 in use → Change port in docker-compose.yml
- High memory usage → Increase limits in docker-compose.yml
