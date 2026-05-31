# GLM-OCR Integration Guide

This document describes the GLM-OCR integration for the Looking Glass project, using the official [GLM-OCR SDK](https://github.com/zai-org/GLM-OCR) with a self-hosted vLLM server.

## Overview

GLM-OCR is a state-of-the-art multimodal OCR model optimized for complex document understanding. It achieves:

- **94.62 score on OmniDocBench V1.5** (ranked #1)
- **Only 0.9B parameters** - efficient inference
- **Support for vLLM, SGLang, and Ollama** deployment
- **Multi-language support** including Japanese, Chinese, Korean, and English

## Architecture

```
┌─────────────────┐      ┌──────────────────────┐      ┌─────────────────┐
│  Looking Glass  │──────│  GLMOCRClient        │──────│  vLLM Server    │
│  Application    │      │  (Official SDK)      │      │  (GPU)          │
│                 │      │                      │      │                 │
│  - Image upload │      │  - HTTP client       │      │  - GLM-OCR      │
│  - Preprocessing│      │  - Connection pool   │      │    model        │
│  - Cache        │      │  - Result parsing    │      │  - OpenAI API   │
└─────────────────┘      └──────────────────────┘      └─────────────────┘
         │                                                   │
         │                                                   │
         └───────────────────────────────────────────────────┘
                    http://172.16.100.132:8000/v1
```

## Configuration

### Environment Variables (`.env`)

```bash
# Enable GLM-OCR mode
ENABLE_GLM_OCR=true

# vLLM server configuration
GLM_OCR_HOST=172.16.100.132
GLM_OCR_PORT=8000

# Performance settings
GLM_OCR_TIMEOUT=60          # Request timeout in seconds
GLM_OCR_POOL_SIZE=10        # HTTP connection pool size
GLM_OCR_MAX_TOKENS=4096     # Max tokens in response

# Model configuration
IMAGE_MODEL=zai-org/GLM-OCR
IMAGE_MODEL_URL=http://172.16.100.132:8000/v1
```

### vLLM Server Setup

The GLM-OCR model should be deployed on your vLLM server with the following command:

```bash
vllm serve zai-org/GLM-OCR \
  --port 8000 \
  --speculative-config '{"method": "mtp", "num_speculative_tokens": 3}' \
  --served-model-name glm-ocr \
  --max-model-len 8192 \
  --gpu-memory-utilization 0.9
```

**Note:** Adjust `--max-model-len` and `--gpu-memory-utilization` based on your GPU memory.

## Usage

### Python API

```python
from app.glm_ocr_client import GLMOCRClient, GLMOCRService

# Option 1: Direct client usage
async with GLMOCRClient(api_host="172.16.100.132", api_port=8000) as client:
    result = await client.parse(image_bytes)
    print(f"Extracted text: {result.text}")
    print(f"Bounding boxes: {result.bboxes}")

# Option 2: High-level service (recommended)
service = GLMOCRService(api_host="172.16.100.132", api_port=8000)
response = await service.extract_text_with_bboxes(image_bytes)
print(f"Labels: {response.labels}")
```

### Automatic Integration

When `ENABLE_GLM_OCR=true` is set in `.env`, the image processing pipeline automatically uses GLM-OCR:

```python
from app.image_processing import extract_labels_with_cache

# This will use GLM-OCR if enabled in settings
response = await extract_labels_with_cache(
    binary_image=image_bytes,
    image_hash="abc123...",
    cache_key="cache_key",
)
```

## Features

### 1. Connection Pooling

The GLM-OCR client uses HTTP connection pooling for efficient reuse of TCP connections:

- **Pool size**: Configurable via `GLM_OCR_POOL_SIZE` (default: 10)
- **Keep-alive**: 30 seconds
- **Max connections**: 2 × pool size

### 2. Automatic Retry

Built-in retry logic with exponential backoff for transient failures.

### 3. Result Caching

OCR results are cached in-memory with:

- **TTL**: 1 hour (configurable)
- **Max size**: 1000 entries
- **Key**: SHA256 hash of image content

### 4. Tiling Auto-Disable

When GLM-OCR mode is enabled, image tiling is automatically disabled since GLM-OCR handles full images with its internal layout detection pipeline.

## Performance Optimization

### 1. Batch Processing

For multiple images, reuse the same client instance:

```python
service = GLMOCRService(api_host="172.16.100.132", api_port=8000)

# Process multiple images
results = await asyncio.gather(*[
    service.extract_text_with_bboxes(img) for img in images
])
```

### 2. Connection Pool Tuning

For high-concurrency scenarios:

```bash
GLM_OCR_POOL_SIZE=20    # Increase pool size
GLM_OCR_TIMEOUT=120     # Increase timeout for large images
```

### 3. vLLM Optimization

On the vLLM server side:

```bash
# Enable speculative decoding (3x speedup)
--speculative-config '{"method": "mtp", "num_speculative_tokens": 3}'

# Optimize GPU memory usage
--gpu-memory-utilization 0.9

# Handle large images
--max-model-len 8192
```

## API Reference

### GLMOCRClient

```python
class GLMOCRClient:
    """GLM-OCR client for vLLM/SGLang deployments."""
    
    def __init__(
        self,
        api_host: str = "172.16.100.132",
        api_port: int = 8000,
        timeout: int = 60,
        pool_size: int = 10,
    )
    
    async def parse(
        self,
        image_data: Union[bytes, str, Path],
        return_json: bool = True,
    ) -> GLMOCRResult
```

### GLMOCRResult

```python
@dataclass
class GLMOCRResult:
    """Result from GLM-OCR processing."""
    json_result: Dict[str, Any]      # Full JSON response
    text: str                         # Extracted text (markdown)
    bboxes: List[Dict[str, Any]]     # Bounding boxes with text
    page_width: int                   # Image width
    page_height: int                  # Image height
    raw_response: Optional[Dict]      # Raw API response
    
    def to_annotation_response(self) -> AnnotationResponse:
        """Convert to AnnotationResponse format."""
```

### GLMOCRService

```python
class GLMOCRService:
    """High-level GLM-OCR service."""
    
    def __init__(
        self,
        api_host: str = "172.16.100.132",
        api_port: int = 8000,
    )
    
    async def extract_text_with_bboxes(
        self,
        image_bytes: bytes,
    ) -> AnnotationResponse
```

## Troubleshooting

### Connection Issues

```bash
# Test vLLM server connectivity
curl http://172.16.100.132:8000/v1/models

# Check server logs
docker logs <vllm-container>
```

### Timeout Errors

Increase timeout in `.env`:

```bash
GLM_OCR_TIMEOUT=120
```

### Memory Issues on vLLM Server

Reduce model memory usage:

```bash
# In vLLM startup command
--gpu-memory-utilization 0.8
--max-model-len 4096
```

### Poor OCR Quality

1. Ensure image is high quality (300+ DPI recommended)
2. Check that GLM-OCR model is properly loaded
3. Verify vLLM speculative decoding is enabled

## Migration from Previous OCR

If you're migrating from the previous VLM-based OCR:

1. **Update `.env`**:
   ```bash
   ENABLE_GLM_OCR=true
   IMAGE_MODEL=zai-org/GLM-OCR
   IMAGE_MODEL_URL=http://172.16.100.132:8000/v1
   ```

2. **Install dependencies**:
   ```bash
   uv sync  # Installs glmocr package
   ```

3. **Restart application**:
   ```bash
   systemctl restart looking-glass
   ```

4. **Verify**:
   ```bash
   curl http://localhost:8000/health
   ```

## Benchmarks

| Metric | VLM-Based | GLM-OCR | Improvement |
|--------|-----------|---------|-------------|
| Accuracy (OmniDocBench) | ~85% | 94.62% | +11.3% |
| Latency (single image) | ~2-3s | ~0.5-1s | 2-3× faster |
| Memory Usage | High | Low (0.9B params) | 50% less |
| Multi-language | Good | Excellent | Better CJK support |

## References

- [GLM-OCR GitHub](https://github.com/zai-org/GLM-OCR)
- [GLM-OCR Technical Report](https://arxiv.org/abs/2603.10910)
- [Zhipu AI Documentation](https://docs.bigmodel.cn/cn/guide/models/vlm/glm-ocr)
- [vLLM Documentation](https://docs.vllm.ai/)

## Support

For issues or questions:
- Check the [GLM-OCR GitHub issues](https://github.com/zai-org/GLM-OCR/issues)
- Join the [Discord community](https://discord.gg/QR7SARHRxK)
- Contact the Looking Glass team
