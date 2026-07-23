# LookingGlass

OCR + image translation service using LLMs. Detects text regions in images via OCR and translates them using language models.

## Features

- **Text Detection**: Uses GLM-OCR or vision-language models to detect text regions in images
- **Batch Translation**: Efficient batch translation of detected text via LLM API
- **Tampermonkey Extension**: Browser userscript for annotating and translating images on any webpage
- **REST API**: Versioned FastAPI endpoints (`/v1/`) for integration
- **Health Checks**: Built-in monitoring endpoint
- **Docker Support**: Containerized deployment with Dockerfile and docker-compose

## Architecture

```
lookingglass/
├── app/                    # Backend application
│   ├── cache.py            # TTL-based in-memory caching
│   ├── common.py           # Shared logging configuration
│   ├── config.py           # Pydantic settings (env-based configuration)
│   ├── container.py        # Dependency injection container
│   ├── dependencies.py     # FastAPI dependency injection
│   ├── glm_ocr_client.py   # GLM-OCR SDK integration
│   ├── image_processing.py # Image preprocessing and annotation
│   ├── schema.py           # Pydantic models
│   ├── translation.py      # Translation logic (batch + individual)
│   └── v1/                 # Version 1 API routes
├── docs/                   # Documentation
├── tampermonkey-extension/ # Browser userscript source
├── tests/                  # Test suite
├── Dockerfile              # Production container image
└── docker-compose.yml      # Local development stack
```

## Quick Start

### Prerequisites
- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager

### Setup

```bash
# Clone and enter the repo
git clone https://github.com/Hnatekmar/LookingGlass.git
cd LookingGlass

# Copy environment configuration
cp .env.example .env
# Edit .env with your model endpoints and settings

# Install dependencies
uv sync

# Run the server
uv run python3 main.py
```

The API will be available at `http://localhost:8090`.

### Docker

```bash
# Docker compose configures all required defaults in docker-compose.yml.
# Override any setting via shell environment variables:
#   TRANSLATION_MODEL_URL=http://my-translator:8000/v1 docker compose up --build
#
# No .env file is needed for Docker usage — everything is pre-configured.
docker compose up --build
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/` | GET | Service info |
| `/v1/health` | GET | Health check |
| `/v1/translate/` | POST | Translate text |
| `/v1/image/annotate/` | POST | Detect and annotate text in images |

## Configuration

All configuration is via environment variables (see `.env.example`):

- **`IMAGE_MODEL`**: Vision/OCR model name (e.g., `qwen3-8b-instruct`)
- **`TRANSLATION_MODEL`**: Translation model name (e.g., `nemotron-3-nano`)
- **`IMAGE_MODEL_URL`**: OpenAI-compatible API endpoint for the image model
- **`TRANSLATION_MODEL_URL`**: OpenAI-compatible API endpoint for the translation model
- **`ENABLE_GLM_OCR`**: Set to `true` to use the GLM-OCR SDK pipeline

## Development

### Running Tests

```bash
uv run pytest
```

### Project Conventions

- Python code follows [PEP 8](https://peps.python.org/pep-0008/) with type hints
- API routes are versioned under `/v1/`
- Configuration is immutable and loaded from environment variables
- Caching uses TTL-based in-memory stores with statistics tracking

## License

MIT
