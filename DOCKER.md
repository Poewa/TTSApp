# Docker Deployment Guide

## Quick Start with Docker Compose

### 1. Build and Run

```bash
# Create .env file with your credentials
cp .env.example .env
# Edit .env with your actual Azure credentials

# Build and start the container
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the container
docker-compose down
```

The app will be available at `http://localhost:5000`

### 2. Using Docker Directly

```bash
# Build the image
docker build -t tts-poc .

# Run with Azure OpenAI TTS
docker run -d \
  --name tts-poc \
  -p 5000:5000 \
  -e AZURE_OPENAI_API_KEY="your-openai-key" \
  -e AZURE_OPENAI_ENDPOINT="your-openai-endpoint" \
  -e AZURE_OPENAI_API_VERSION="2025-03-01-preview" \
  tts-poc

# Run with both TTS services
docker run -d \
  --name tts-poc \
  -p 5000:5000 \
  -e AZURE_OPENAI_API_KEY="your-openai-key" \
  -e AZURE_OPENAI_ENDPOINT="your-openai-endpoint" \
  -e AZURE_OPENAI_API_VERSION="2025-03-01-preview" \
  -e AZURE_SPEECH_KEY="your-speech-key" \
  -e AZURE_SPEECH_REGION="swedencentral" \
  tts-poc

# View logs
docker logs -f tts-poc

# Stop and remove
docker stop tts-poc
docker rm tts-poc
```

## Security Features

### Built-in Security

✅ **Non-root user** - Container runs as unprivileged user (UID 1000)
✅ **Gunicorn** - Production-grade WSGI server instead of Flask dev server
✅ **Security headers** - X-Frame-Options, CSP, XSS protection
✅ **Request size limits** - 16MB max to prevent DoS
✅ **No debug mode** - Debug disabled in production
✅ **Minimal image** - Based on python:3.13-slim
✅ **SSL support** - Includes CA certificates for HTTPS connections

### Environment Variables

**For Azure OpenAI TTS:**
- `AZURE_OPENAI_API_KEY` - Your Azure OpenAI API key (required)
- `AZURE_OPENAI_ENDPOINT` - Your Azure OpenAI endpoint (required)
- `AZURE_OPENAI_API_VERSION` - API version (default: 2025-03-01-preview)

**For Azure Speech Service:**
- `AZURE_SPEECH_KEY` - Your Azure Speech Service API key (required)
- `AZURE_SPEECH_REGION` - Your Speech Service region, e.g., `swedencentral` (required)

**Optional:**
- `FLASK_ENV=production` - Disable debug mode (recommended)

### Secrets Management

**For Production, use Docker Secrets:**

```yaml
# docker-compose.yml with secrets
services:
  web:
    build: .
    secrets:
      - azure_openai_key
      - azure_openai_endpoint
      - azure_speech_key
    environment:
      - AZURE_OPENAI_API_KEY_FILE=/run/secrets/azure_openai_key
      - AZURE_OPENAI_ENDPOINT_FILE=/run/secrets/azure_openai_endpoint
      - AZURE_SPEECH_KEY_FILE=/run/secrets/azure_speech_key
      - AZURE_SPEECH_REGION=swedencentral

secrets:
  azure_openai_key:
    file: ./secrets/openai_key.txt
  azure_openai_endpoint:
    file: ./secrets/openai_endpoint.txt
  azure_speech_key:
    file: ./secrets/speech_key.txt
```

### Additional Security Recommendations

1. **Use HTTPS** - Deploy behind a reverse proxy (Nginx/Traefik) with SSL
2. **Rate limiting** - Add rate limiting to prevent abuse
3. **Firewall** - Restrict access to trusted IPs only
4. **Monitoring** - Set up logging and monitoring
5. **Updates** - Regularly update dependencies

### Example with Nginx Reverse Proxy

```yaml
version: '3.8'

services:
  web:
    build: .
    environment:
      - AZURE_OPENAI_API_KEY=${AZURE_OPENAI_API_KEY}
      - AZURE_OPENAI_ENDPOINT=${AZURE_OPENAI_ENDPOINT}
      - AZURE_OPENAI_API_VERSION=${AZURE_OPENAI_API_VERSION}
      - AZURE_SPEECH_KEY=${AZURE_SPEECH_KEY}
      - AZURE_SPEECH_REGION=${AZURE_SPEECH_REGION}
      - FLASK_ENV=production
    networks:
      - internal

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - web
    networks:
      - internal

networks:
  internal:
    driver: bridge
```

## Production Checklist

- [ ] Set `FLASK_ENV=production`
- [ ] Use strong, unique API keys for both services
- [ ] Store credentials in Docker secrets (not .env)
- [ ] Deploy behind HTTPS reverse proxy
- [ ] Set up rate limiting
- [ ] Configure firewall rules
- [ ] Enable logging and monitoring
- [ ] Set resource limits (CPU/memory)
- [ ] Regular security updates
- [ ] Backup strategy for audio files
- [ ] Deploy `tts-1-hd` model as `tts-hd` in Azure OpenAI
- [ ] Verify Speech Service region matches your resource

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

### Container won't start
```bash
# Check logs
docker-compose logs web

# Common issues:
# - Missing environment variables (check .env file)
# - Port 5000 already in use (change in docker-compose.yml)
# - Permission issues (ensure Dockerfile runs as non-root user)
```

### Environment variables not loading
```bash
# Verify variables inside container
docker-compose exec web env | grep AZURE

# Should see:
# AZURE_OPENAI_API_KEY=...
# AZURE_OPENAI_ENDPOINT=...
# AZURE_SPEECH_KEY=...
# AZURE_SPEECH_REGION=...
```

### Audio generation fails
```bash
# Check if REST API is accessible from container
docker-compose exec web python -c "import requests; print(requests.get('https://swedencentral.tts.speech.microsoft.com').status_code)"

# Test Azure OpenAI connection
docker-compose exec web python -c "import os; print(os.getenv('AZURE_OPENAI_ENDPOINT'))"
```

### High memory usage
- Increase memory limits in docker-compose.yml
- Enable audio file cleanup (automatically removes files >1 hour old)
- Check for memory leaks with: `docker stats tts-poc`

## Health Checks

The app automatically cleans up old audio files. Monitor container health with:

```bash
# Check container status
docker ps

# View resource usage
docker stats tts-poc

# Inspect logs for errors
docker-compose logs -f web | grep ERROR
```

## Troubleshooting

**Container won't start:**
```bash
docker logs tts-poc
```

**Permission issues:**
```bash
# Ensure audio directory is writable
chmod -R 755 static/audio
```

**Out of memory:**
```bash
# Increase memory limit in docker-compose.yml
```
