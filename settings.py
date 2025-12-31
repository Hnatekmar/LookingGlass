from typing import Optional

from pydantic_ai import ModelSettings
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Model names
    image_model: str = "qwen3-8b-instruct"
    translation_model: str = "nemotron-3-nano"

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

    # Model settings
    qwen3_instruct_sampler: ModelSettings = ModelSettings(
        temperature=0.7,
        extra_body={
            "top_p": 0.8,
            "top_k": 20,
            "repetition_penalty": 1.0,
            "presence_penalty": 1.5,
            "max_tokens": 16384
        }
    )

    qwen3_thinking_sampler: ModelSettings = ModelSettings(
        temperature=1.0,
        extra_body={
            "top_p": 0.95,
            "top_k": 20,
            "presence_penalty": 0.0,
            "repetition_penalty": 1.0,
            "max_tokens": 40960
        }
    )

    # API endpoints
    image_model_url: str = "https://llm.hnatekmar.dev/qwen3-8b-instruct/v1"
    translation_model_url: str = "https://llm.hnatekmar.dev/qwen-next-instruct/v1"

    # Coordinate mapping constants
    canvas_width: int = 1000
    canvas_height: int = 1000

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
    default_translate_language: str = "english"

    # Model samplers
    image_model_samplers: Optional[ModelSettings] = None
    translation_model_samplers: Optional[ModelSettings] = None
