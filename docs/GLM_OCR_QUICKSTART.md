# GLM-OCR Quick Start

## 1. Install Dependencies

```bash
cd LookingGlass
uv sync
```

This installs the `glmocr` package (official GLM-OCR SDK) and all other dependencies.

## 2. Configure Environment

Edit `.env`:

```bash
# Enable GLM-OCR
ENABLE_GLM_OCR=true

# Your vLLM server running GLM-OCR
IMAGE_MODEL_URL=http://your-vllm-server:8000/v1
IMAGE_MODEL=glm-ocr

# Translation model (separate endpoint)
TRANSLATION_MODEL_URL=http://your-translation-server:8001/v1
TRANSLATION_MODEL=your-translation-model
```

## 3. Start the Server

```bash
uv run python3 main.py
```

## 4. Test

```bash
curl -X POST http://localhost:8000/v1/health
```

## Docker Compose (with built-in vLLM)

```bash
docker compose up --build
```

This starts both the LookingGlass app and a vLLM server running GLM-OCR.

## Troubleshooting

- **Connection refused**: Ensure your vLLM server is running and accessible
- **Timeout**: Increase `GLM_OCR_TIMEOUT` (default: 60s)
- **Import error**: Run `uv sync` to ensure `glmocr` is installed
- **GPU memory**: GLM-OCR needs ~2GB VRAM; adjust `--max-model-len` accordingly
