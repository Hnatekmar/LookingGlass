"""
Gemma-OCR Client - OpenAI-compatible API integration.

Replaces GLM-OCR with a general-purpose vision-language model (Gemma 12B)
running on an OpenAI-compatible endpoint. Sends images directly to the
model with an OCR-specific prompt and parses structured JSON output.

Usage:
    from app.gemma_ocr_client import GemmaOCRService

    service = GemmaOCRService()
    result = await service.extract_text_with_bboxes(image_bytes)
"""

import asyncio
import base64
import json
from typing import List, Dict, Any

import httpx

from app.schema import Label, AnnotationResponse
from app.config import get_settings
from app.common import logger


# Default system prompt for Gemma OCR - optimized for text detection
GEMMA_OCR_SYSTEM_PROMPT = """You are an expert OCR (Optical Character Recognition) system.

**Task:** Detect ALL text regions in the image and extract the text content.
Return a JSON object with a "labels" array.

**CRITICAL REQUIREMENTS:**
1. Detect EVERY text region - completeness is the highest priority
2. Extract text accurately, preserving original formatting
3. Handle multiple languages (Japanese, Chinese, Korean, English, etc.)
4. Process vertical and horizontal text correctly

**Detection Scope:**
- Speech bubbles, dialogue, captions
- Vertical text columns (keep each column as ONE region)
- Signs, labels, buttons, UI elements
- Background text, posters, screens
- Handwritten and stylized text
- Text at ALL edges (left, right, top, bottom)
- Small text (minimum 8px height)

**Output Format:**
Return a JSON object with this exact structure:
{"labels": [{"x1": float, "y1": float, "x2": float, "y2": float, "text": "..."}]}

- Coordinates are normalized to 0-1000 scale (divide by 1000.0 before using)
- x1,y1 = top-left corner, x2,y2 = bottom-right corner
- Include ALL detected text regions
- Do not miss any text - false positives are acceptable

**Special Handling:**
- Vertical text: ONE box per column, top to bottom
- Curved text: Use tight bounding box
- Faded/low-contrast text: Still detect and extract
- Partially occluded text: Detect visible portions

Scan systematically: left→right, top→bottom. Verify all edges before responding."""


class GemmaOCRService:
    """
    OCR service using a vision-language model via OpenAI-compatible API.

    Sends images to the model endpoint with a structured OCR prompt and
    parses the JSON response into AnnotationResponse format.

    Configuration loaded from .env:
        - GEMMA_OCR_URL: API endpoint URL
        - GEMMA_OCR_MODEL: Model name (default: gemma-12b)
        - GEMMA_OCR_TIMEOUT: Request timeout in seconds
    """

    def __init__(self):
        settings = get_settings()
        self.api_url = settings.gemma_ocr_url.rstrip("/") + "/chat/completions"
        self.model = settings.gemma_ocr_model
        self.timeout = settings.gemma_ocr_timeout
        self.max_tokens = settings.gemma_ocr_max_tokens

        # Create a dedicated HTTP client for Gemma OCR
        self._http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout, connect=15.0),
            limits=httpx.Limits(
                max_keepalive_connections=5,
                max_connections=10,
                keepalive_expiry=30.0,
            ),
            follow_redirects=True,
        )

        logger.info(
            f"Gemma OCR initialized: {self.api_url} (model: {self.model})"
        )

    async def extract_text_with_bboxes(self, image_bytes: bytes) -> AnnotationResponse:
        """
        Extract text and bounding boxes from an image using Gemma vision model.

        Args:
            image_bytes: Raw image bytes

        Returns:
            AnnotationResponse with detected text regions
        """
        # Encode image as base64 data URI
        image_b64 = base64.b64encode(image_bytes).decode("utf-8")
        image_data_uri = f"data:image/jpeg;base64,{image_b64}"

        # Build the request payload
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": GEMMA_OCR_SYSTEM_PROMPT,
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_data_uri,
                                "detail": "auto",
                            },
                        },
                    ],
                },
            ],
            "max_tokens": self.max_tokens,
            "temperature": 0.1,  # Low temperature for deterministic OCR
            "response_format": {"type": "json_object"},
        }

        try:
            response = await self._http_client.post(
                self.api_url,
                json=payload,
            )
            response.raise_for_status()
            result = response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Gemma OCR HTTP error: {e.response.status_code} - {e.response.text[:500]}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Gemma OCR request failed: {e}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Gemma OCR invalid JSON response: {e}")
            raise

        # Parse the response
        labels = self._parse_response(result)
        logger.info(f"Gemma OCR extracted {len(labels)} text regions")
        return AnnotationResponse(labels=labels)

    def _parse_response(self, response_data: Dict[str, Any]) -> List[Label]:
        """
        Parse the OpenAI-compatible API response into Label objects.

        Expected response structure:
        {
            "choices": [
                {
                    "message": {
                        "content": '{"labels": [{"x1": 0, "y1": 0, "x2": 1000, "y2": 1000, "text": "..."}]}'
                    }
                }
            ]
        }
        """
        labels = []

        try:
            content = response_data["choices"][0]["message"]["content"]

            # Try to parse as JSON
            parsed = json.loads(content)

            # Handle different possible structures
            label_list = None
            if isinstance(parsed, dict):
                if "labels" in parsed:
                    label_list = parsed["labels"]
                elif "regions" in parsed:
                    label_list = parsed["regions"]
                elif "boxes" in parsed:
                    label_list = parsed["boxes"]
            elif isinstance(parsed, list):
                label_list = parsed

            if label_list and isinstance(label_list, list):
                for item in label_list:
                    if isinstance(item, dict):
                        x1 = self._safe_float(item.get("x1", item.get("left", 0)))
                        y1 = self._safe_float(item.get("y1", item.get("top", 0)))
                        x2 = self._safe_float(item.get("x2", item.get("right", 0)))
                        y2 = self._safe_float(item.get("y2", item.get("bottom", 0)))
                        text = str(item.get("text", item.get("content", item.get("transcription", ""))))

                        # Normalize coordinates from 0-1000 to 0-1
                        labels.append(Label(
                            x1=x1 / 1000.0,
                            y1=y1 / 1000.0,
                            x2=x2 / 1000.0,
                            y2=y2 / 1000.0,
                            text=text,
                        ))

        except (KeyError, IndexError, json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Gemma OCR failed to parse response: {e}")
            # Return empty result instead of crashing
            return []

        return labels

    @staticmethod
    def _safe_float(value: Any, default: float = 0.0) -> float:
        """Safely convert a value to float, returning default on failure."""
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    async def close(self):
        """Close the HTTP client and release resources."""
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()


# Convenience function for building the OCR agent via pydantic_ai
# (alternative approach using structured outputs)
def build_gemma_ocr_agent(settings_obj=None):
    """
    Build a pydantic_ai Agent configured for Gemma OCR.

    This provides an alternative approach using pydantic_ai's structured
    output support, which may give better parsing reliability on some models.

    Usage:
        agent = build_gemma_ocr_agent()
        result = await agent.run([BinaryContent(data=image_bytes, media_type="image/jpeg")])
    """
    if settings_obj is None:
        from app.config import get_settings
        settings_obj = get_settings()

    from pydantic_ai import Agent
    from pydantic_ai.models.openai import OpenAIChatModel
    from pydantic_ai.providers.openai import OpenAIProvider

    chat_model = OpenAIChatModel(
        model_name=settings_obj.gemma_ocr_model,
        provider=OpenAIProvider(
            base_url=settings_obj.gemma_ocr_url,
        ),
    )

    return Agent(
        model=chat_model,
        system_prompt=GEMMA_OCR_SYSTEM_PROMPT,
        output_type=list[Label],
        retries=3,
    )
