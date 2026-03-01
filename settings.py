from typing import Optional

from pydantic_ai import ModelSettings
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # Model names
    image_model: str = Field(..., alias="IMAGE_MODEL")
    translation_model: str = Field(..., alias="TRANSLATION_MODEL")

    # Prompts
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

    # Sampler settings for qwen3_instruct (with defaults)
    qwen3_instruct_sampler_temperature: Optional[float] = Field(
        None, alias="QWEN3_INSTRUCT_SAMPLER_TEMPERATURE"
    )
    qwen3_instruct_sampler_top_p: Optional[float] = Field(
        None, alias="QWEN3_INSTRUCT_SAMPLER_TOP_P"
    )
    qwen3_instruct_sampler_top_k: Optional[int] = Field(
        None, alias="QWEN3_INSTRUCT_SAMPLER_TOP_K"
    )
    qwen3_instruct_sampler_repetition_penalty: Optional[float] = Field(
        None, alias="QWEN3_INSTRUCT_SAMPLER_REPETITION_PENALTY"
    )
    qwen3_instruct_sampler_presence_penalty: Optional[float] = Field(
        None, alias="QWEN3_INSTRUCT_SAMPLER_PRESENCE_PENALTY"
    )
    qwen3_instruct_sampler_max_tokens: Optional[int] = Field(
        None, alias="QWEN3_INSTRUCT_SAMPLER_MAX_TOKENS"
    )

    # Sampler settings for qwen3_thinking (with defaults)
    qwen3_thinking_sampler_temperature: Optional[float] = Field(
        None, alias="QWEN3_THINKING_SAMPLER_TEMPERATURE"
    )
    qwen3_thinking_sampler_top_p: Optional[float] = Field(
        None, alias="QWEN3_THINKING_SAMPLER_TOP_P"
    )
    qwen3_thinking_sampler_top_k: Optional[int] = Field(
        None, alias="QWEN3_THINKING_SAMPLER_TOP_K"
    )
    qwen3_thinking_sampler_repetition_penalty: Optional[float] = Field(
        None, alias="QWEN3_THINKING_SAMPLER_REPETITION_PENALTY"
    )
    qwen3_thinking_sampler_presence_penalty: Optional[float] = Field(
        None, alias="QWEN3_THINKING_SAMPLER_PRESENCE_PENALTY"
    )
    qwen3_thinking_sampler_max_tokens: Optional[int] = Field(
        None, alias="QWEN3_THINKING_SAMPLER_MAX_TOKENS"
    )

    # Sampler settings for image_model (with defaults)
    image_model_sampler_temperature: Optional[float] = Field(
        None, alias="IMAGE_MODEL_SAMPLER_TEMPERATURE"
    )
    image_model_sampler_top_p: Optional[float] = Field(
        None, alias="IMAGE_MODEL_SAMPLER_TOP_P"
    )
    image_model_sampler_top_k: Optional[int] = Field(
        None, alias="IMAGE_MODEL_SAMPLER_TOP_K"
    )
    image_model_sampler_repetition_penalty: Optional[float] = Field(
        None, alias="IMAGE_MODEL_SAMPLER_REPETITION_PENALTY"
    )
    image_model_sampler_presence_penalty: Optional[float] = Field(
        None, alias="IMAGE_MODEL_SAMPLER_PRESENCE_PENALTY"
    )
    image_model_sampler_max_tokens: Optional[int] = Field(
        None, alias="IMAGE_MODEL_SAMPLER_MAX_TOKENS"
    )

    # Sampler settings for translation_model (with defaults)
    translation_model_sampler_temperature: Optional[float] = Field(
        None, alias="TRANSLATION_MODEL_SAMPLER_TEMPERATURE"
    )
    translation_model_sampler_top_p: Optional[float] = Field(
        None, alias="TRANSLATION_MODEL_SAMPLER_TOP_P"
    )
    translation_model_sampler_top_k: Optional[int] = Field(
        None, alias="TRANSLATION_MODEL_SAMPLER_TOP_K"
    )
    translation_model_sampler_repetition_penalty: Optional[float] = Field(
        None, alias="TRANSLATION_MODEL_SAMPLER_REPETITION_PENALTY"
    )
    translation_model_sampler_presence_penalty: Optional[float] = Field(
        None, alias="TRANSLATION_MODEL_SAMPLER_PRESENCE_PENALTY"
    )
    translation_model_sampler_max_tokens: Optional[int] = Field(
        None, alias="TRANSLATION_MODEL_SAMPLER_MAX_TOKENS"
    )

    # Model samplers
    image_model_samplers: Optional[ModelSettings] = None
    translation_model_samplers: Optional[ModelSettings] = None

    @property
    def qwen3_instruct_sampler(self) -> ModelSettings:
        """Build qwen3_instruct sampler from env vars with defaults."""
        return ModelSettings(
            temperature=self.qwen3_instruct_sampler_temperature or 0.7,
            extra_body={
                "top_p": self.qwen3_instruct_sampler_top_p or 0.8,
                "top_k": self.qwen3_instruct_sampler_top_k or 20,
                "repetition_penalty": self.qwen3_instruct_sampler_repetition_penalty
                or 1.0,
                "presence_penalty": self.qwen3_instruct_sampler_presence_penalty or 1.5,
                "max_tokens": self.qwen3_instruct_sampler_max_tokens or 16384,
            },
        )

    @property
    def qwen3_thinking_sampler(self) -> ModelSettings:
        """Build qwen3_thinking sampler from env vars with defaults."""
        return ModelSettings(
            temperature=self.qwen3_thinking_sampler_temperature or 1.0,
            extra_body={
                "top_p": self.qwen3_thinking_sampler_top_p or 0.95,
                "top_k": self.qwen3_thinking_sampler_top_k or 20,
                "repetition_penalty": self.qwen3_thinking_sampler_repetition_penalty
                or 1.0,
                "presence_penalty": self.qwen3_thinking_sampler_presence_penalty or 0.0,
                "max_tokens": self.qwen3_thinking_sampler_max_tokens or 40960,
            },
        )

    @property
    def image_model_sampler(self) -> ModelSettings:
        """Build image_model sampler from env vars with defaults."""
        return ModelSettings(
            temperature=self.image_model_sampler_temperature or 0.7,
            extra_body={
                "top_p": self.image_model_sampler_top_p or 0.8,
                "top_k": self.image_model_sampler_top_k or 20,
                "repetition_penalty": self.image_model_sampler_repetition_penalty
                or 1.0,
                "presence_penalty": self.image_model_sampler_presence_penalty or 1.5,
                "max_tokens": self.image_model_sampler_max_tokens or 16384,
            },
        )

    @property
    def translation_model_sampler(self) -> ModelSettings:
        """Build translation_model sampler from env vars with defaults."""
        return ModelSettings(
            temperature=self.translation_model_sampler_temperature or 0.7,
            extra_body={
                "top_p": self.translation_model_sampler_top_p or 0.8,
                "top_k": self.translation_model_sampler_top_k or 20,
                "repetition_penalty": self.translation_model_sampler_repetition_penalty
                or 1.0,
                "presence_penalty": self.translation_model_sampler_presence_penalty
                or 1.5,
                "max_tokens": self.translation_model_sampler_max_tokens or 16384,
            },
        )
