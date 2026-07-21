# LookingGlass

OCR + image translation service using LLMs. Detects text regions in images via
GLM-OCR or vision-language models and translates them using language models.

## Features

- **Text Detection**: GLM-OCR SDK or vision-language model fallback
- **Batch Translation**: Efficient batch translation via LLM API with caching
- **Streaming SSE**: Progressive label delivery as tiles are processed
- **Tampermonkey Extension**: Browser userscript for inline image annotation
- **REST API**: Versioned FastAPI endpoints at `/v1/`
- **In-Memory Caching**: TTL-based caching with hit-rate monitoring

## Quick Start

### Prerequisites
- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager

### Setup

```bash
git clone https://github.com/Hnatekmar/LookingGlass.git
cd LookingGlass
cp .env.example .env
# Edit .env with your model endpoints (IMAGE_MODEL_URL, TRANSLATION_MODEL_URL, etc.)
uv sync
uv run python3 main.py
```

The API will be available at `http://localhost:8000`.

### Docker

```bash
docker compose up --build
```

## API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/v1/` | GET | Service info |
| `/v1/health` | GET | Health check |
| `/v1/translate/` | POST | Translate text |
| `/v1/image/annotate/` | POST | Detect and annotate text in images |
| `/v1/image/annotate/stream` | POST | Streaming annotation (SSE) |
| `/v1/image/cache/stats` | GET | Cache statistics |
| `/v1/image/cache` | DELETE | Clear caches |

## Configuration

All configuration is via environment variables. See `.env.example` for the
complete reference. Key settings:

| Variable | Required | Description |
|---|---|---|
| `IMAGE_MODEL` | Yes | Vision/OCR model name |
| `TRANSLATION_MODEL` | Yes | Translation model name |
| `IMAGE_MODEL_URL` | Yes | OpenAI-compatible API URL for the image model |
| `TRANSLATION_MODEL_URL` | Yes | OpenAI-compatible API URL for the translation model |
| `ENABLE_GLM_OCR` | No | Set `true` to use GLM-OCR SDK pipeline (default: `false`) |
| `ENABLE_GEMMA_OCR` | No | Set `true` to use Gemma 12b as OCR backend (default: `false`) |
| `CORS_ORIGINS` | No | Comma-separated allowed origins (default: `*`) |
| `API_KEY` | No | Enable API key authentication (default: disabled) |

## Project Structure

```
lookingglass/
├── app/                     # Backend application
│   ├── cache.py             # TTL-based in-memory caching
│   ├── common.py            # Shared logging
│   ├── config.py            # Pydantic-settings (env-based)
│   ├── container.py         # Dependency injection
│   ├── dependencies.py      # HTTP pools, agent factory
│   ├── glm_ocr_client.py    # GLM-OCR SDK integration
│   ├── image_processing.py  # OCR pipeline, tiling, dedup
│   ├── schema.py            # Pydantic models
│   ├── translation.py       # Batch + individual translation
│   └── v1/                  # API routes
├── docs/                    # Documentation
│   ├── architecture.md      # Data flow and component design
│   ├── configuration.md     # Complete env var reference
│   ├── development.md       # Dev setup, testing, contributing
│   └── deployment/          # Deployment guides
├── tampermonkey-extension/  # Browser userscript (TypeScript)
├── tests/                   # Test suite
├── Dockerfile
└── docker-compose.yml
```

## Architecture

```
Client → FastAPI (v1/) → image_processing.py → OCR Provider (GLM-OCR / VLM)
                                                   │
                                              translation.py → LLM API
                                                   │
                                              cache.py (TTL)
                                                   │
                                              Client ← Response
```

See [docs/architecture.md](docs/architecture.md) for the complete data flow.

## Development

```bash
# Install with dev dependencies
uv sync --dev

# Run tests
uv run pytest

# Run with auto-reload
uv run uvicorn app:app --reload --port 8000
```

### Tampermonkey Extension

```bash
cd tampermonkey-extension
npm install
npm run build
# Output: dist/image-annotator.user.js
```

Install the built `.user.js` in Tampermonkey/Violentmonkey.

## License

MIT
