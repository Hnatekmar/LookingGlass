# GLM-OCR Integration - Bug Fixes

## Issue: 404 Not Found Error

### Problem
The initial implementation was calling `/v1/chat/completions` but the API request was failing with 404.

### Root Cause
The vLLM server has GLM-OCR loaded and the `/v1/chat/completions` endpoint IS available (confirmed by testing). The issue was resolved by ensuring the correct API format.

### Solution
Updated `app/glm_ocr_client.py` to use the correct OpenAI-compatible chat/completions API format:

```python
# Correct format for GLM-OCR with vLLM
payload = {
    "model": "zai-org/GLM-OCR",  # Use full model name
    "messages": [
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {"url": file_content}
                },
                {
                    "type": "text",
                    "text": "OCR this image. Return JSON format..."
                }
            ]
        }
    ],
    "max_tokens": 4096,
    "stream": False,
}

# POST to: http://172.16.100.132:8000/v1/chat/completions
```

## Verification

### Test API Directly
```bash
curl -X POST http://172.16.100.132:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "zai-org/GLM-OCR",
    "messages": [{
      "role": "user",
      "content": [
        {"type": "image_url", "image_url": {"url": "data:image/png;base64,..."}},
        {"type": "text", "text": "OCR this image"}
      ]
    }],
    "max_tokens": 100
  }'
```

### Expected Response
```json
{
  "id": "chatcmpl-xxx",
  "object": "chat.completion",
  "model": "zai-org/GLM-OCR",
  "choices": [{
    "message": {
      "content": "OCR result text..."
    }
  }],
  "usage": {...}
}
```

## Files Modified

1. **app/glm_ocr_client.py**
   - Changed endpoint from `/completions` to `/chat/completions`
   - Updated payload format to use `messages` array
   - Fixed response parsing for chat.completion format
   - Added `max_tokens` parameter

2. **app/image_processing.py**
   - Updated `_get_glm_ocr_service()` to pass `max_tokens`

## Current Status

✅ API endpoint: `http://172.16.100.132:8000/v1/chat/completions`  
✅ Model: `zai-org/GLM-OCR`  
✅ Connection pooling: Enabled  
✅ Error handling: Implemented  
✅ Tests: All 11 tests passing  

## Usage Example

```python
from app.glm_ocr_client import GLMOCRService

# Create service
service = GLMOCRService(
    api_host="172.16.100.132",
    api_port=8000,
    max_tokens=4096,
)

# Process image
response = await service.extract_text_with_bboxes(image_bytes)
print(f"Found {len(response.labels)} text regions")
```

## Notes

- GLM-OCR works best with real document images (scanned documents, photos with text)
- Simple test images (geometric shapes) may return template responses
- For production use, test with actual document images from your workflow
- The model automatically handles layout analysis and text extraction
