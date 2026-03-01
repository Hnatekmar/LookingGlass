import time
from typing import Optional, Type

from pydantic_ai import ModelSettings, Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from .config import Settings  # type hint for injected settings
from .common import logger  # logger will be injected explicitly
from .schema import AnnotationResponse, Label


def build_chat_agent(
    model: str,
    prompt: str,
    output_type: Type = AnnotationResponse,
    *,
    settings_obj: Settings,
    logger_obj,
    settings_override: Optional[ModelSettings] = None,
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

    chat_model = OpenAIChatModel(
        model_name=model,
        provider=OpenAIProvider(
            base_url=base_url,
        ),
    )

    agent_kwargs = {
        "model": chat_model,
        "retries": 32,
        "system_prompt": prompt,
        "output_type": output_type,
    }

    if settings_override is None:
        if model == settings_obj.image_model:
            agent_kwargs["model_settings"] = (
                settings_obj.image_model_samplers or settings_obj.qwen3_instruct_sampler
            )
        elif model == settings_obj.translation_model:
            agent_kwargs["model_settings"] = (
                settings_obj.translation_model_samplers
                or settings_obj.qwen3_instruct_sampler
            )
    else:
        agent_kwargs["model_settings"] = settings_override

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
