from typing import Optional
from pathlib import Path

from pydantic_ai import ModelSettings
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

# Determine the project root directory (parent of app/)
PROJECT_ROOT = Path(__file__).parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        frozen=True,
    )
    image_model: str = Field(..., alias="IMAGE_MODEL")
    translation_model: str = Field(..., alias="TRANSLATION_MODEL")

    label_prompt: str = """
You are a text region detection agent for machine translation workflows.

**Task:** Identify and localize all text regions in the input image.

**Input:** A single image containing text (e.g., speech bubbles, paragraphs, captions, signs).

**Output Requirements:**
- Return a list of bounding boxes, one for each distinct text region
- Each bounding box must use normalized coordinates in the format:
  - x1, y1: top-left corner coordinates
  - x2, y2: bottom-right corner coordinates
  - All coordinates are normalized to a 0-1000 scale 

**Detection Guidelines:**
- Detect ALL visible text in the image, including:
  - Speech bubbles and dialogue text
  - Paragraphs and continuous text blocks
  - Signs, labels, and captions
  - Overlaid text and watermarks
- Each text region should have its own separate bounding box
- Bounding boxes should tightly fit around the text with minimal padding
- Group text that logically belongs together (e.g., text within the same speech bubble)
- Do not overlap bounding boxes unless text regions actually overlap in the image
"""

    qwen3_instruct_sampler: ModelSettings = ModelSettings(
        temperature=0.7,
        extra_body={
            "top_p": 0.8,
            "top_k": 20,
            "repetition_penalty": 1.0,
            "presence_penalty": 1.5,
            "max_tokens": 16384,
        },
    )

    qwen3_thinking_sampler: ModelSettings = ModelSettings(
        temperature=1.0,
        extra_body={
            "top_p": 0.95,
            "top_k": 20,
            "presence_penalty": 0.0,
            "repetition_penalty": 1.0,
            "max_tokens": 40960,
        },
    )

    image_model_url: str = Field(..., alias="IMAGE_MODEL_URL")
    translation_model_url: str = Field(..., alias="TRANSLATION_MODEL_URL")

    canvas_width: int = Field(1000, alias="CANVAS_WIDTH")
    canvas_height: int = Field(1000, alias="CANVAS_HEIGHT")

    translate_prompt_template: str = """
You are a professional translator specializing in accurate and natural translations.

**Task:** Translate the given text into {language}.

**Requirements:**
- Provide ONLY the translated text without any explanations or additional commentary
- Preserve the original meaning, tone, and intent
- Ensure the translation sounds natural and fluent to native speakers
- Maintain any formatting, punctuation, or special characters where appropriate
- If the text is already in {language}, return it exactly as provided
- For proper nouns (names, places, brands), use standard transliterations if applicable

**Input:** Text to be translated
**Output:** Translated text only
"""

    default_translate_language: str = Field(
        "english", alias="DEFAULT_TRANSLATE_LANGUAGE"
    )

    image_model_samplers: Optional[ModelSettings] = None
    translation_model_samplers: Optional[ModelSettings] = None

    llm_base_url: str = Field("https://llm.hnatekmar.dev", alias="LLM_BASE_URL")
    deepseek_ocr_sampler: ModelSettings = ModelSettings(
        temperature=0.0,
        extra_body={
            "skip_special_tokens": False,
            "max_tokens": 4096,
            "vllm_xargs": {
                "ngram_size": 30,
                "window_size": 90,
                "whitelist_token_ids": [128821, 128822],
            },
        },
    )

    qwen3_thinking_sampler: ModelSettings = ModelSettings(
        temperature=1.0,
        extra_body={
            "top_p": 0.95,
            "top_k": 20,
            "presence_penalty": 0.0,
            "repetition_penalty": 1.0,
            "max_tokens": 40960,
        },
    )

    # API endpoints
    image_model_url: str = Field(..., alias="IMAGE_MODEL_URL")
    translation_model_url: str = Field(..., alias="TRANSLATION_MODEL_URL")

    # Coordinate mapping constants
    canvas_width: int = Field(1000, alias="CANVAS_WIDTH")
    canvas_height: int = Field(1000, alias="CANVAS_HEIGHT")

    # Translation prompt template
    translate_prompt_template: str = """
You are a professional translator specializing in accurate and natural translations.

**Task:** Translate the given text into {language}.

**Requirements:**
- Provide ONLY the translated text without any explanations or additional commentary
- Preserve the original meaning, tone, and intent
- Ensure the translation sounds natural and fluent to native speakers
- Maintain any formatting, punctuation, or special characters where appropriate
- If the text is already in {language}, return it exactly as provided
- For proper nouns (names, places, brands), use standard transliterations if applicable

**Input:** Text to be translated
**Output:** Translated text only
"""

    # Default translation language
    default_translate_language: str = Field(
        "english", alias="DEFAULT_TRANSLATE_LANGUAGE"
    )

    # Model samplers
    image_model_samplers: Optional[ModelSettings] = None
    translation_model_samplers: Optional[ModelSettings] = ModelSettings(
        temperature=0.7,
        max_tokens=32768,
        top_p=0.8,
        presence_penalty=1.5,
        extra_body={
            "chat_template_kwargs": {"enable_thinking": False},
            "top_k": 20,
        },
    )

    # Additional configuration from common.py
    llm_base_url: str = Field("https://llm.hnatekmar.dev", alias="LLM_BASE_URL")
    deepseek_ocr_sampler: ModelSettings = ModelSettings(
        temperature=0.0,
        extra_body={
            "skip_special_tokens": False,
            "max_tokens": 4096,
            "vllm_xargs": {
                "ngram_size": 30,
                "window_size": 90,
                "whitelist_token_ids": [128821, 128822],
            },
        },
    )
