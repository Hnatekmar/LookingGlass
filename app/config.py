# app/config.py
"""
Central configuration entry point.

- Loads all settings from environment variables (via pydantic‑settings).
- Exposes a frozen, immutable Settings instance.
- Provides a `get_settings()` accessor for dependency‑injection.
"""

import os
from pathlib import Path

from pydantic import (
    Field,
    ConfigDict,
)  # Import Pydantic base classes for settings management
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)  # Import BaseSettings from pydantic-settings package
from pydantic_ai import ModelSettings  # Import ModelSettings for AI model configuration

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
    """  # End of label prompt template

    # Model settings (defaults – can be overridden by env vars)
    qwen3_instruct_sampler: ModelSettings = (
        ModelSettings(  # Qwen3 instruction model sampler configuration
            temperature=0.7,  # Model temperature setting
            extra_body={  # Additional model parameters
                "top_p": 0.8,  # Nucleus sampling parameter
                "top_k": 20,  # Top-k sampling parameter
                "repetition_penalty": 1.0,  # Repetition penalty
                "presence_penalty": 1.5,  # Presence penalty
                "max_tokens": 16384,  # Maximum tokens to generate
            },
        )  # End of ModelSettings for instruct sampler
    )

    qwen3_thinking_sampler: ModelSettings = (
        ModelSettings(  # Qwen3 thinking model sampler configuration
            temperature=1.0,  # Model temperature setting
            extra_body={  # Additional model parameters
                "top_p": 0.95,  # Nucleus sampling parameter
                "top_k": 20,  # Top-k sampling parameter
                "presence_penalty": 0.0,  # Presence penalty
                "repetition_penalty": 1.0,  # Repetition penalty
                "max_tokens": 40960,  # Maximum tokens to generate
            },
        )
    )  # End of ModelSettings for thinking sampler

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
    translate_prompt_template: str = """  # Translation prompt template string
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

    # Batch translation prompt template (for multiple texts at once using JSON)
    batch_translate_prompt_template: str = """  # Batch translation prompt template string
    You are a professional translator specializing in accurate and natural translations.
    
    **Task:** Translate all texts in the JSON array into {language}.
    
    **Input Format:**
    - JSON array of objects with "id" and "text" fields
    - Example: `[{{"id": 0, "text": "Hello"}}, {{"id": 1, "text": "World"}}]`
    
    **Output Requirements:**
    - Return a JSON array with the SAME structure
    - Each object must have "id" (unchanged) and "translated_text" fields
    - Example: `[{{"id": 0, "translated_text": "Bonjour"}}, {{"id": 1, "translated_text": "Monde"}}]`
    
    **Translation Rules:**
    - Preserve the original meaning, tone, and intent for each item
    - Ensure translations sound natural and fluent
    - Maintain formatting, punctuation, or special characters where appropriate
    - If any text is already in {language}, return it exactly as provided
    - Match the input array length exactly (same number of items)
    - Keep the same order and IDs as the input
    
    **Important:**
    - Output must be VALID JSON only (no markdown, no explanations)
    - Use double quotes for all strings
    - Escape special characters properly in JSON
    
    Now translate the following texts into {language}:
    """

    # Default translation language
    default_translate_language: str = Field(
        "english", alias="DEFAULT_TRANSLATE_LANGUAGE"
    )

    # Optional sampler overrides (can be supplied via env vars as JSON strings)
    image_model_samplers: ModelSettings | None = ModelSettings(
        temperature=0.7,
        max_tokens=32768,
        top_p=0.8,
        presence_penalty=1.5,
        extra_body={
            "top_k": 20,
            "chat_template_kwargs": {"enable_thinking": False},
        },
    )

    translation_model_samplers: ModelSettings | None = ModelSettings(
        temperature=0.7,
        max_tokens=32768,
        top_p=0.8,
        presence_penalty=1.5,
        extra_body={
            "top_k": 20,
            "chat_template_kwargs": {"enable_thinking": False},
        },
    )

    # Optional generic LLM base URL (fallback for models not explicitly configured)
    llm_base_url: str | None = (
        None  # Generic LLM base URL (optional, falls back to specific model URLs)
    )

    # OAuth2 Configuration
    # OpenID Connect Discovery (preferred) - provide only issuer URL
    oauth2_issuer: str | None = Field(None, alias="OAUTH2_ISSUER")

    # Manual configuration (fallback) - explicit endpoints
    oauth2_authorize_url: str | None = Field(None, alias="OAUTH2_AUTHORIZE_URL")
    oauth2_token_url: str | None = Field(None, alias="OAUTH2_TOKEN_URL")
    oauth2_jwks_url: str | None = Field(None, alias="OAUTH2_JWKS_URL")

    # Common OAuth2 settings (optional - only required when OAuth2 is enabled)
    oauth2_client_id: str | None = Field(None, alias="OAUTH2_CLIENT_ID")
    oauth2_client_secret: str | None = Field(None, alias="OAUTH2_CLIENT_SECRET")
    oauth2_redirect_uri: str | None = Field(None, alias="OAUTH2_REDIRECT_URI")
    oauth2_scopes: str = Field("openid profile email", alias="OAUTH2_SCOPES")
    # Session secret key for cookie-based session management (required for OAuth2 state)
    # Generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"
    # WARNING: Using a default development key - DO NOT use in production!
    session_secret_key: str = Field(

        "dev-secret-key-change-in-production", alias="SESSION_SECRET_KEY"

    )

    # Redis Configuration
    # Redis URL for persistent access code storage (optional, falls back to in-memory)
    # Format: redis://host:port/db or rediss://host:port/db for TLS
    # Example: redis://localhost:6379/0 or redis://user:pass@redis.example.com:6379/0
    redis_url: str | None = Field(None, alias="REDIS_URL")

    # Access code TTL in seconds (default: 24 hours = 86400)
    # How long access codes remain valid before expiring
    access_code_ttl: int = Field(86400, alias="ACCESS_CODE_TTL")


    # Make Settings immutable – aligns with 12‑factor & code‑quality immutability
    model_config = SettingsConfigDict(
        frozen=True,
        extra="ignore",
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
    )

# Instantiate a singleton Settings object at import time (process start)
settings = Settings()  # Create singleton Settings instance


def get_settings() -> Settings:  # Function definition with return type hint
    """Return the shared immutable Settings instance.

    This function is the canonical way to retrieve configuration throughout the
    codebase, enabling explicit dependency injection and easier testing.
    """
    return settings  # Return the singleton settings instance
