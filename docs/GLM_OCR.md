# GLM-OCR Integration Guide

This document describes the GLM-OCR integration for LookingGlass, using the
official [GLM-OCR SDK](https://github.com/zai-org/GLM-OCR) with a self-hosted
vLLM server.

## Overview

GLM-OCR is a multimodal OCR model optimized for document understanding.
It achieves high accuracy with only 0.9B parameters and supports multiple
languages including Japanese, Chinese, Korean, and English.

## Architecture

```
LookingGlass App
      │
      ▼
GLMOCRService (app/glm_ocr_client.py)
      │
      ▼
GLM-OCR SDK (glmocr package)
      │
      ▼
vLLM Server (GPU) ─── serving zai-org/GLM-OCR
```

## Configuration

Enable GLM-OCR by setting these environment variables:

```bash
ENABLE_GLM_OCR=true
IMAGE_MODEL_URL=http://your-vllm-server:8000/v1
```

The SDK uses `IMAGE_MODEL_URL` to connect to the vLLM server. Host and port
are extracted automatically from the URL.

## Docker Compose

The `docker-compose.yml` includes a pre-configured vLLM service:

```yaml
image-annotator:
  image: vllm/vllm-openai:nightly
  command: zai-org/GLM-OCR --max-model-len 16192 --gpu-memory-util 0.8
  runtime: nvidia
```

To use it:

```bash
docker compose up --build
```

## How It Works

When `ENABLE_GLM_OCR=true`:

1. Image is prepared (resized to 1280px max, sharpness enhanced)
2. Sent to `GLMOCRService.extract_text_with_bboxes()` via the GLM-OCR SDK
3. SDK communicates with the vLLM server
4. Returns detected text regions with bounding boxes

When `ENABLE_GLM_OCR=false` (default), the app falls back to a generic VLM
via `pydantic_ai` using the model at `IMAGE_MODEL_URL`.

## SDK Details

- Package: `glmocr[layout,selfhosted]`
- Import: lazy — only loads when GLM-OCR mode is enabled
- The SDK manages its own HTTP connections
- Uses the GLM-OCR optimized prompt built into the SDK
