# Docker Deployment Guide

## Quick Start with Docker Compose

### 1. Build and Run

```bash
# Create .env file with your credentials
cp .env.example .env
# Edit .env with your actual credentials

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

# Run the container
docker run -d \
  --name tts-poc \
  -p 5000:5000 \
  -e AZURE_OPENAI_API_KEY="your-key" \
  -e AZURE_OPENAI_ENDPOINT="your-endpoint" \
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

### Environment Variables

**Required:**
- `AZURE_OPENAI_API_KEY` - Your Azure OpenAI API key
- `AZURE_OPENAI_ENDPOINT` - Your Azure OpenAI endpoint

**Optional:**
- `FLASK_ENV=production` - Disable debug mode (recommended)

### Secrets Management

**For Production, use Docker Secrets:**

```yaml
# docker-compose.yml with secrets
services:
  tts-app:
    build: .
    secrets:
      - azure_api_key
      - azure_endpoint
    environment:
      - AZURE_OPENAI_API_KEY_FILE=/run/secrets/azure_api_key
      - AZURE_OPENAI_ENDPOINT_FILE=/run/secrets/azure_endpoint

secrets:
  azure_api_key:
    file: ./secrets/api_key.txt
  azure_endpoint:
    file: ./secrets/endpoint.txt
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
  tts-app:
    build: .
    environment:
      - AZURE_OPENAI_API_KEY=${AZURE_OPENAI_API_KEY}
      - AZURE_OPENAI_ENDPOINT=${AZURE_OPENAI_ENDPOINT}
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
      - tts-app
    networks:
      - internal

networks:
  internal:
    driver: bridge
```

## Production Checklist

- [ ] Set `FLASK_ENV=production`
- [ ] Use strong, unique API keys
- [ ] Store credentials in Docker secrets (not .env)
- [ ] Deploy behind HTTPS reverse proxy
- [ ] Set up rate limiting
- [ ] Configure firewall rules
- [ ] Enable logging and monitoring
- [ ] Set resource limits (CPU/memory)
- [ ] Regular security updates
- [ ] Backup strategy for audio files

## Resource Limits

Add to `docker-compose.yml`:

```yaml
services:
  tts-app:
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

## Health Checks

The app includes a health check endpoint. Monitor with:

```bash
docker inspect --format='{{json .State.Health}}' tts-poc
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
