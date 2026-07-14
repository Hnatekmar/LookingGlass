# app/config.py
"""
Central configuration entry point.

- Loads all settings from environment variables (via pydantic‑settings).
- Exposes a frozen, immutable Settings instance.
- Provides a `get_settings()` accessor for dependency‑injection.
"""

import os
from pathlib import Path
from urllib.parse import urlparse

from pydantic import (
    Field,
    ConfigDict,
)  # Import Pydantic base classes for settings management
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)  # Import BaseSettings from pydantic-settings package

# Determine the project root directory (parent of app/)
PROJECT_ROOT = Path(__file__).parent.parent


class Settings(BaseSettings):  # Define Settings class inheriting from BaseSettings
    # Model names
    image_model: str = Field(
        ..., alias="IMAGE_MODEL"
    )  # Image model name from environment variable
    translation_model: str = Field(
        ..., alias="TRANSLATION_MODEL"
    )  # Translation model name from environment variable

    # Prompts
    label_prompt: str = """  # Label detection prompt template string
    # NOTE: Coordinate normalization (÷1000) assumes labels use a 0-1000 scale
    # as specified in this prompt. If you change the prompt's coordinate scale
    # (e.g., to 0-1), update app/image_processing.py normalization accordingly.
    You are a text region detection agent for machine translation workflows.
    
    **Task:** Identify and localize ALL text regions in the input image.
    
    **Input:** A single image containing text (e.g., speech bubbles, paragraphs, captions, signs, vertical Japanese/Chinese/Korean text).
    
    **CRITICAL RULES:**
    1. Do not miss ANY text regions — missing text is a CRITICAL ERROR
    2. ALWAYS detect text at image edges (left edge, right edge, top, bottom)
    3. For vertical text columns: each column is ONE region, do NOT split vertically
    4. Missing text is worse than false positives — bias toward over-detection
    
    **Output Requirements:**
    - Return a COMPLETE list of bounding boxes, one for each distinct text region
    - Each bounding box must use normalized coordinates in the format:
      - x1, y1: top-left corner coordinates
      - x2, y2: bottom-right corner coordinates  
      - All coordinates are normalized to a 0-1000 scale
    - Output ALL detected regions — do not truncate or skip any
    
    **Detection Guidelines:**
    - Detect ALL visible text in the image, including:
      - Speech bubbles and dialogue text (main AND small/secondary bubbles)
      - Paragraphs and continuous text blocks
      - Vertical text columns (Japanese/Chinese/Korean) — each column is ONE box
      - Signs, labels, and captions (including small footnotes)
      - Overlaid text and watermarks
      - Background text (posters, screens, books within the image)
      - Handwritten text and stylized fonts
      - Text at image edges and corners (ESPECIALLY leftmost and rightmost edges)
      - Small text (even 8-10px height)
    - For vertical text: create ONE bounding box per column (top to bottom)
    - For horizontal text: create ONE bounding box per paragraph/line group
    - Bounding boxes should tightly fit around the text with minimal padding
    - Group text that logically belongs together (e.g., text within the same speech bubble)
    - Do not overlap bounding boxes unless text regions actually overlap in the image
    - When in doubt, include the region — completeness is the priority
    
    **Common Mistakes to AVOID:**
    - ❌ Missing the leftmost text column (ALWAYS check the left edge)
    - ❌ Missing the rightmost text column (ALWAYS check the right edge)
    - ❌ Splitting one vertical column into multiple boxes (keep it as ONE box)
    - ❌ Skipping small text or text at edges
    
    **Output Format:**
    - Return a JSON array of label objects
    - Each label: {"x1": float, "y1": float, "x2": float, "y2": float, "text": "extracted text"}
    - Ensure the array is complete before responding
    - Scan the ENTIRE image from left to right, edge to edge
    """  # End of label prompt template

    # GLM-OCR optimized prompt - leverages GLM-OCR's native OCR capabilities
    glm_ocr_prompt: str = """You are an expert OCR (Optical Character Recognition) system.
    
    **Task:** Detect ALL text regions in the image and extract the text content.
    
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
    - JSON array of objects with: x1, y1, x2, y2 (normalized 0-1000), text
    - Coordinates: x1,y1 = top-left, x2,y2 = bottom-right
    - Include ALL detected text regions
    - Do not miss any text - false positives are acceptable
    
    **Special Handling:**
    - Vertical text: ONE box per column, top to bottom
    - Curved text: Use tight bounding box
    - Faded/low-contrast text: Still detect and extract
    - Partially occluded text: Detect visible portions
    
    Scan systematically: left→right, top→bottom. Verify all edges before responding."""

    # API endpoints
    image_model_url: str = Field(
        ..., alias="IMAGE_MODEL_URL"
    )  # Image model API URL from environment variable
    translation_model_url: str = Field(
        ..., alias="TRANSLATION_MODEL_URL"
    )  # Translation model API URL from environment variable

    # Canvas dimensions
    canvas_width: int = Field(
        1000, alias="CANVAS_WIDTH"
    )  # Canvas width for image processing
    canvas_height: int = Field(
        1000, alias="CANVAS_HEIGHT"
    )  # Canvas height for image processing

    # Translation prompt template (for individual text)
    translate_prompt_template: str = """You are a translator. Translate the following text into natural, idiomatic {language}.

**Your approach:**
- Make it sound like a native speaker wrote it—natural, not literal
- Match the tone: casual stays casual, formal stays formal
- Keep contractions, slang, and personality where they fit
- Preserve all formatting, punctuation, emojis, and special characters
- Proper nouns stay as-is (unless there's a well-known English version)

**Output:** Only the translation. No notes, no explanations.

If it's already in {language}, just return it unchanged."""

    # Batch translation prompt template (for multiple texts at once using JSON)
    # Note: Output format is handled by Pydantic structured output - this prompt focuses on translation quality
    # Input: JSON array of strings ["text1", "text2", ...]
    # Output: List of TranslatedLabel objects with translated_text field
    batch_translate_prompt_template: str = """You are a translator. Translate each text string into natural, idiomatic {language}.

**Input:** A JSON array of text strings from an image (speech bubbles, signs, captions, etc.).

**Your approach:**
- Make each translation sound natural and native—not literal or robotic
- Match the original tone (casual, formal, dramatic, playful, etc.)
- Preserve formatting, punctuation, emojis, and special characters
- Keep proper nouns as-is (unless there's a common localized version)
- Maintain the order: translate string 1, then 2, then 3, etc.

**Output:** Return one translation per input string, in the same order.
If a string is already in {language}, return it unchanged.

Input: {{input}}"""

    # Default translation language
    default_translate_language: str = Field(
        "english", alias="DEFAULT_TRANSLATE_LANGUAGE"
    )

    # Optional generic LLM base URL (fallback for models not explicitly configured)
    llm_base_url: str | None = (
        None  # Generic LLM base URL (optional, falls back to specific model URLs)
    )

    # Redis Configuration
    # Redis URL for caching (optional)
    # Format: redis://host:port/db or rediss://host:port/db for TLS
    # Example: redis://localhost:6379/0 or redis://user:pass@redis.example.com:6379/0
    redis_url: str | None = Field(None, alias="REDIS_URL")

    # GLM-OCR Specific Configuration (Official SDK)
    # Enable GLM-OCR mode (uses official GLM-OCR SDK pipeline)
    enable_glm_ocr: bool = Field(False, alias="ENABLE_GLM_OCR")
    # GLM-OCR request timeout (seconds)
    glm_ocr_timeout: int = Field(60, alias="GLM_OCR_TIMEOUT")
    # Translation model timeout (seconds) - higher for thinking mode
    translation_timeout: int = Field(600, alias="TRANSLATION_TIMEOUT")
    # GLM-OCR HTTP connection pool size
    glm_ocr_pool_size: int = Field(10, alias="GLM_OCR_POOL_SIZE")
    # GLM-OCR max tokens in response
    glm_ocr_max_tokens: int = Field(4096, alias="GLM_OCR_MAX_TOKENS")

    # Gemma OCR Configuration (OpenAI-compatible API)
    # Enable Gemma OCR mode (uses vision-language model via OpenAI-compatible API)
    enable_gemma_ocr: bool = Field(False, alias="ENABLE_GEMMA_OCR")
    # Gemma OCR API endpoint URL
    # Default points to the remote Gemma 12b endpoint
    gemma_ocr_url: str = Field(
        "http://172.16.100.189:8010/v1", alias="GEMMA_OCR_URL"
    )
    # Gemma OCR model name
    gemma_ocr_model: str = Field("gemma-12b", alias="GEMMA_OCR_MODEL")
    # Gemma OCR request timeout (seconds)
    gemma_ocr_timeout: int = Field(120, alias="GEMMA_OCR_TIMEOUT")
    # Gemma OCR max tokens in response
    gemma_ocr_max_tokens: int = Field(4096, alias="GEMMA_OCR_MAX_TOKENS")

    @property
    def glm_ocr_host(self) -> str:
        """Extract GLM-OCR host from IMAGE_MODEL_URL."""
        parsed = urlparse(self.image_model_url)
        return parsed.hostname or "localhost"

    @property
    def glm_ocr_port(self) -> int:
        """Extract GLM-OCR port from IMAGE_MODEL_URL."""
        parsed = urlparse(self.image_model_url)
        return parsed.port or 8000

    # Make Settings immutable – aligns with 12‑factor & code‑quality immutability
    model_config = SettingsConfigDict(
        frozen=True,
        extra="ignore",
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
    )


# Lazy singleton: instantiated on first call to get_settings()
_settings: Settings | None = None


def get_settings() -> Settings:  # Function definition with return type hint
    """Return the shared immutable Settings instance (lazily created).

    This function is the canonical way to retrieve configuration throughout the
    codebase, enabling explicit dependency injection and easier testing.
    The Settings object is created on first access, so tests can set
    environment variables before any code calls ``get_settings()``.
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
