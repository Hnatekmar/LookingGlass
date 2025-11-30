import time

from pydantic_ai import ModelSettings, Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from app.common import logger
from app.schema import AnnotationResponse


def build_chat_agent(url: str, model: str, prompt: str, output_type=AnnotationResponse, settings=ModelSettings(
    temperature=0.6,
    extra_body={
        "top_p": 0.95,
        "top_k": 20,
        "presence_penalty": 0.0,
        "repetition_penalty": 1.0
    }
)) -> Agent:
    # Create a custom SSL context to prevent SSL errors
    chat_model = OpenAIChatModel(
        model_name=model,
        provider=OpenAIProvider(
            base_url=url,
        )
    )
    agent = Agent(
        model=chat_model,
        retries=32,
        system_prompt=prompt,
        output_type=output_type,
        model_settings=settings
    )

    # Wrap the agent's run method to add timing
    original_run = agent.run

    async def timed_run(*args, **kwargs):
        start_time = time.perf_counter()
        try:
            result = await original_run(*args, **kwargs)
            end_time = time.perf_counter()
            logger.info(f"Agent '{model}' call completed in {end_time - start_time:.3f}s")
            return result
        except Exception as e:
            end_time = time.perf_counter()
            logger.error(f"Agent '{model}' call failed after {end_time - start_time:.3f}s: {str(e)}")
            raise

    # Replace the run method with our timed version
    agent.run = timed_run

    return agent
