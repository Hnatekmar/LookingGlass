# GLM-OCR Quick Start

## 1. Install Dependencies

```bash
cd /data/documents/work/LookingGlass
uv sync
```

This installs the `glmocr` package (official GLM-OCR SDK) and all other dependencies.

## 2. Configure Environment

Edit `.env`:

```bash
# Enable GLM-OCR
ENABLE_GLM_OCR=true

# Your vLLM server
GLM_OCR_HOST=172.16.100.132
GLM_OCR_PORT=8000

# Model configuration
IMAGE_MODEL=zai-org/GLM-OCR
IMAGE_MODEL_URL=http://172.16.100.132:8000/v1
```

## 3. Verify vLLM Server

Make sure your vLLM server is running with GLM-OCR:

```bash
# Test connectivity
curl http://172.16.100.132:8000/v1/models

# Should return GLM-OCR model info
```

Expected vLLM startup command:
```bash
vllm serve zai-org/GLM-OCR \
  --port 8000 \
  --speculative-config '{"method": "mtp", "num_speculative_tokens": 3}' \
  --served-model-name glm-ocr \
  --max-model-len 8192 \
  --gpu-memory-utilization 0.9
```

## 4. Start Looking Glass

```bash
# Using systemd
sudo systemctl restart looking-glass

# Or manually
./start-lookingglass.sh
```

## 5. Test OCR

```bash
# Upload an image for OCR processing
curl -X POST http://localhost:8000/v1/image/annotate \
  -H "Content-Type: multipart/form-data" \
  -F "image=@test_image.jpg"
```

## 6. Monitor Performance

Check server logs:
```bash
journalctl -u looking-glass -f
```

Look for:
- `GLM-OCR mode enabled` - confirms GLM-OCR is active
- `GLM-OCR service initialized` - confirms connection to vLLM
- Request latency metrics

## Key Benefits

| Feature | Before (VLM) | After (GLM-OCR) |
|---------|--------------|-----------------|
| Accuracy | ~85% | 94.62% (#1 on OmniDocBench) |
| Latency | 2-3s | 0.5-1s |
| Model Size | Large (100B+) | Small (0.9B) |
| CJK Support | Good | Excellent |
| Tiling Required | Yes (for large images) | No (handles full images) |

## Troubleshooting

### Connection Refused
```bash
# Check vLLM server is running
curl http://172.16.100.132:8000/v1/models

# Check firewall rules
sudo ufw status
```

### Timeout Errors
Increase timeout in `.env`:
```bash
GLM_OCR_TIMEOUT=120
```

### Poor OCR Quality
1. Ensure image is high quality (300+ DPI)
2. Verify vLLM speculative decoding is enabled
3. Check GLM-OCR model is properly loaded

## Next Steps

- See [docs/GLM_OCR.md](docs/GLM_OCR.md) for detailed documentation
- See [tests/test_glm_ocr.py](tests/test_glm_ocr.py) for usage examples
- See [app/glm_ocr_client.py](app/glm_ocr_client.py) for API reference
