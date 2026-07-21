# Deployment

LookingGlass can be deployed via Docker, systemd, or Podman Quadlets.

## Docker

### Build and Run

```bash
# Build the image
docker build -t looking-glass:latest .

# Run with environment variables
docker run -d \
  --name lookingglass \
  -p 8000:8000 \
  -e IMAGE_MODEL=your-model \
  -e TRANSLATION_MODEL=your-model \
  -e IMAGE_MODEL_URL=http://your-vllm-server:8000/v1 \
  -e TRANSLATION_MODEL_URL=http://your-translation-server:8001/v1 \
  looking-glass:latest
```

### Docker Compose

The `docker-compose.yml` includes both the LookingGlass app and a vLLM server
for GLM-OCR:

```bash
docker compose up --build
```

This is the recommended approach for local development.

### CI/CD Build

The repository has a CI workflow (`build-docker-images.yml`) that:
- Builds and pushes to `gitea.hnatekmar.xyz/public/looking-glass`
- Tags with `:latest` (on main) and `:sha-<short>` (all pushes)
- Tags with `:v<semver>` on version tags
- Uses BuildKit caching for faster builds

## Systemd / Podman Quadlets

The production deployment uses Podman Quadlets with systemd service files.
The `lookingglass.service` file is provided as a reference.

1. Copy the service file:
   ```bash
   sudo cp lookingglass.service /etc/systemd/system/
   ```

2. Edit the service to set your environment variables and paths

3. Start the service:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable --now lookingglass
   ```

## Configuration

All configuration is via environment variables. Copy `.env.example` to `.env`
and customize:

```bash
cp .env.example .env
# EDIT .env with your values
```

Required variables:
- `IMAGE_MODEL` — Vision/OCR model name
- `TRANSLATION_MODEL` — Translation model name
- `IMAGE_MODEL_URL` — OpenAI-compatible API endpoint
- `TRANSLATION_MODEL_URL` — Translation model API endpoint

## Health Check

The service exposes a health check at `/v1/health`:

```bash
curl http://localhost:8000/v1/health
# {"status":"healthy","service":"Image Annotator Backend","version":"1.0.0"}
```

## Notes

- The default port is 8000 (configurable via `PORT` env var)
- API key authentication is optional (set `API_KEY` to enable)
- CORS is wide-open by default (`*`); restrict `CORS_ORIGINS` in production
