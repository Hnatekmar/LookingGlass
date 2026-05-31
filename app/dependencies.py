import time
from typing import Optional, Type
import httpx

from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from .config import Settings  # type hint for injected settings
from .common import logger  # logger will be injected explicitly
from .schema import AnnotationResponse, Label


# Shared HTTP clients with connection pooling for vLLM server
_http_client: Optional[httpx.AsyncClient] = None
_http_client_translation: Optional[httpx.AsyncClient] = None


def get_http_client(settings_obj: Settings, for_translation: bool = False) -> httpx.AsyncClient:
    """Get or create a shared HTTP client with connection pooling.
    
    Optimized for vLLM server communication with:
    - Connection pooling (reuses TCP connections)
    - Appropriate timeouts for OCR/translation requests
    - Retry configuration
    
    Args:
        settings_obj: Settings object for configuration
        for_translation: If True, use translation timeout
    
    Returns:
        Configured async HTTP client
    """
    global _http_client, _http_client_translation
    
    # Use separate client for translation to allow longer timeout
    if for_translation:
        if _http_client_translation is not None and not _http_client_translation.is_closed:
            return _http_client_translation
        
        timeout = getattr(settings_obj, 'translation_timeout', 180)
        _http_client_translation = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout, connect=10.0),
            limits=httpx.Limits(
                max_keepalive_connections=10,
                max_connections=20,
                keepalive_expiry=30.0,
            ),
            follow_redirects=True,
        )
        return _http_client_translation
    else:
        if _http_client is not None and not _http_client.is_closed:
            return _http_client
        
        timeout = getattr(settings_obj, 'glm_ocr_timeout', 60)
        _http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout, connect=10.0),
            limits=httpx.Limits(
                max_keepalive_connections=10,
                max_connections=20,
                keepalive_expiry=30.0,
            ),
            follow_redirects=True,
        )
        return _http_client


def build_chat_agent(
    model: str,
    prompt: str,
    output_type: Type = AnnotationResponse,
    *,
    settings_obj: Settings,
    logger_obj,
    settings_override: Optional[dict] = None,
) -> Agent:
    # Determine the appropriate base URL based on the model being used
    if model == settings_obj.image_model:
        base_url = settings_obj.image_model_url
    elif model == settings_obj.translation_model:
        base_url = settings_obj.translation_model_url
    else:
        # Fallback: try to use a generic LLM_BASE_URL if defined, otherwise raise error
        base_url = getattr(settings_obj, "llm_base_url", None)
        if not base_url:
            raise ValueError(
                f"No URL configured for model '{model}'. "
                f"Set IMAGE_MODEL_URL, TRANSLATION_MODEL_URL, or LLM_BASE_URL."
            )

    # Get shared HTTP client with connection pooling
    # Use longer timeout for translation model
    is_translation = (model == settings_obj.translation_model)
    http_client = get_http_client(settings_obj, for_translation=is_translation)

    chat_model = OpenAIChatModel(
        model_name=model,
        provider=OpenAIProvider(
            base_url=base_url,
            http_client=http_client,
        ),
    )

    # Build model settings - disable thinking for Qwen models to reduce latency
    model_settings = {}
    if is_translation:
        # Disable thinking/reasoning mode for faster translation
        model_settings["extra_body"] = {
            "chat_template_kwargs": {"enable_thinking": False}
        }

    agent_kwargs = {
        "model": chat_model,
        "retries": 32,
        "system_prompt": prompt,
        "output_type": output_type,
        "model_settings": model_settings if model_settings else None,
    }

    # No sampler parameters - use model defaults

    agent = Agent(**agent_kwargs)

    original_run = agent.run

    async def timed_run(*args, **kwargs):
        start_time = time.perf_counter()
        try:
            result = await original_run(*args, **kwargs)
            end_time = time.perf_counter()
            logger_obj.info(
                f"Agent '{model}' call completed in {end_time - start_time:.3f}s"
            )
            return result
        except Exception as e:
            end_time = time.perf_counter()
            logger_obj.error(
                f"Agent '{model}' call failed after {end_time - start_time:.3f}s: {str(e)}"
            )
            raise

    agent.run = timed_run

    return agent
