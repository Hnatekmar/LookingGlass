"""
GLM-OCR Client - Official SDK Integration

Simplified client for GLM-OCR with self-hosted vLLM/SGLang deployments.

Usage:
    from app.glm_ocr_client import GLMOCRService
    
    service = GLMOCRService()
    result = await service.extract_text_with_bboxes(image_bytes)
"""

import asyncio
from typing import List, Dict, Any

from glmocr import GlmOcr
from app.schema import Label, AnnotationResponse
from app.config import get_settings
from app.common import logger


class GLMOCRService:
    """
    GLM-OCR service using the official SDK.
    
    Configuration is loaded from .env via pydantic-settings:
        - IMAGE_MODEL_URL: vLLM server URL (parsed for host/port)
        - IMAGE_MODEL: Model name (default: zai-org/GLM-OCR)
        - GLM_OCR_TIMEOUT: Request timeout in seconds
    """
    
    def __init__(self):
        settings = get_settings()
        self._parser = GlmOcr(
            mode="selfhosted",
            model=settings.image_model,
            ocr_api_host=settings.glm_ocr_host,
            ocr_api_port=settings.glm_ocr_port,
            timeout=settings.glm_ocr_timeout,
        )
        logger.info(
            f"GLM-OCR initialized: http://{settings.glm_ocr_host}:{settings.glm_ocr_port}/v1"
        )
    
    async def extract_text_with_bboxes(self, image_bytes: bytes) -> AnnotationResponse:
        """
        Extract text and bounding boxes from an image.
        
        Args:
            image_bytes: Raw image bytes
            
        Returns:
            AnnotationResponse with detected text regions
        """
        loop = asyncio.get_event_loop()
        
        def _parse_sync():
            return self._parser.parse(image_bytes)
        
        result = await loop.run_in_executor(None, _parse_sync)
        
        # Parse bounding boxes from GLM-OCR result
        labels = []
        json_result = result.json_result or []
        
        for page_regions in json_result:
            if isinstance(page_regions, list):
                for region in page_regions:
                    if isinstance(region, dict) and "bbox_2d" in region:
                        coords = region["bbox_2d"]
                        if len(coords) == 4:
                            # GLM-OCR returns normalized 0-1000 coordinates
                            labels.append(Label(
                                x1=coords[0] / 1000.0,
                                y1=coords[1] / 1000.0,
                                x2=coords[2] / 1000.0,
                                y2=coords[3] / 1000.0,
                                text=region.get("content") or region.get("text") or "",
                            ))
        
        logger.info(f"GLM-OCR extracted {len(labels)} text regions")
        return AnnotationResponse(labels=labels)
    
    async def close(self):
        """Close the parser and release resources."""
        if self._parser:
            self._parser.close()
