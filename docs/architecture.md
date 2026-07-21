# Architecture

## Overview

LookingGlass is a FastAPI-based OCR + image translation service. It detects text
regions in images using a configurable OCR backend, then translates the detected
text using a language model.

## Data Flow

```
Client (curl/browser/Tampermonkey)
       │
       ▼
  ┌────────────┐
  │  FastAPI    │  Routes: /v1/image/annotate/, /v1/translate/, /v1/health
  │  (v1/*.py)  │  Middleware: CORS, optional API key auth
  └─────┬──────┘
        │
        ▼
  ┌──────────────┐
  │ image_       │  Image preprocessing, tile computation, deduplication
  │ processing   │  Routes between OCR providers
  └──────┬───────┘
         │
         ├─── ENABLE_GLM_OCR=true ────► GLMOCRService (glmocr SDK)
         │
         └─── ENABLE_GLM_OCR=false ───► VLM fallback (pydantic_ai Agent)
                                         └──► OpenAI-compatible API at IMAGE_MODEL_URL
                                                 │
                                                 ▼
                                          ┌────────────┐
                                          │ LLM / vLLM │
                                          │ Server     │
                                          └────────────┘
         │
         ▼
  ┌──────────────┐
  │ translation  │  Batch translation via pydantic_ai Agent
  │              │  Supports individual fallback for batch failures
  └──────┬───────┘
         │
         ▼
  ┌──────────────┐
  │ cache        │  TTL-based in-memory cache (image + translation)
  │              │  CacheStats for monitoring
  └──────────────┘
         │
         ▼
  Client receives AnnotationResponse (labels + coordinates)
```

## Component Breakdown

### `app/config.py`
- Pydantic-settings `Settings` class, loaded from environment variables
- Immutable singleton, lazily created on first `get_settings()` call
- All env vars documented in `.env.example`

### `app/common.py`
- Shared logging configuration (level from `LOG_LEVEL` env var via Settings)
- Exports the `logger` instance used across the app

### `app/schema.py`
- Pydantic models for request/response types:
  - `Label`: bounding box + text
  - `AnnotationResponse`: list of labels
  - `SSE*EventData`: streaming event types
  - `LabelResult` / `TranslationResult`: inner response types

### `app/image_processing.py`
- Entry point for text detection in images
- Routes to the configured OCR provider (GLM-OCR SDK or VLM fallback)
- Tile-based processing for large images:
  - `TILE_SIZE=1024` px
  - `TILE_OVERLAP=64` px overlap
- Deduplication of overlapping labels via IOU threshold
- Caching via `image_annotation_cache`

### `app/glm_ocr_client.py`
- Wraps the `glmocr` SDK for text detection
- `GLMOCRService` class with `extract_text_with_bboxes()`
- Imported lazily — GLM-OCR mode must be explicitly enabled

### `app/translation.py`
- Batch translation via `pydantic_ai` Agent with structured output
- Falls back to individual parallel translation on batch validation failure
- Caching via `translation_cache` (keyed by image hash + language)

### `app/dependencies.py`
- Shared HTTP client pool (separate pools for OCR and translation timeouts)
- `build_chat_agent()` factory for creating `pydantic_ai` Agents
- Timeout tracking on agent runs

### `app/v1/__main__.py`
- FastAPI application setup (CORS middleware, API key auth, routes)
- Health check at `/v1/health`
- Versioned route registration

### `app/cache.py`
- In-memory `TTLCache` with configurable TTL and max size
- Statistics tracking (hits, misses, evictions, hit rate)
- Pre-configured instances for image annotations and translations

## Streaming Architecture

The `/v1/image/annotate/stream` endpoint uses Server-Sent Events (SSE) to
deliver labels progressively as tiles are processed:

1. Image is split into tiles
2. Each tile is processed through the OCR pipeline
3. Labels are emitted as `labels` SSE events per tile
4. After all tiles complete, a `translate` event is emitted (if enabled)
5. A `complete` event signals the end

Error events (`error`) can be emitted mid-stream without breaking the connection.

## Configuration

All configuration is via environment variables. See `.env.example` for the
complete reference. Key settings:

| Variable | Required | Default | Description |
|---|---|---|---|
| `IMAGE_MODEL` | Yes | — | Vision/OCR model name |
| `TRANSLATION_MODEL` | Yes | — | Translation model name |
| `IMAGE_MODEL_URL` | Yes | — | OpenAI-compatible API URL for image model |
| `TRANSLATION_MODEL_URL` | Yes | — | OpenAI-compatible API URL for translation model |
| `ENABLE_GLM_OCR` | No | `false` | Use GLM-OCR SDK instead of VLM fallback |
| `PORT` | No | `8000` | Server port |
| `CORS_ORIGINS` | No | `*` | CORS allowed origins (comma-separated) |
| `API_KEY` | No | — | Enable API key authentication |
| `LOG_LEVEL` | No | `INFO` | Logging level |

## Production Deployment

Production deployment uses Podman Quadlets + systemd. See `docs/deployment/` for
details on Docker, systemd, and Kubernetes (future) approaches.

## Adding a New Vision Model

1. Implement the OCR interface (currently done via `_extract_labels_from_image` in
   `image_processing.py`)
2. Add config fields to `Settings` in `config.py`
3. Update `.env.example` with new env vars
4. Add import routing in `_extract_labels_from_image()`
5. Write tests in `tests/`
6. Update docs
