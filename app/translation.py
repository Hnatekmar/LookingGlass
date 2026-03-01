import asyncio
from typing import List

from app.common import logger
from app.config import get_settings
from app.container import get_chat_agent
from app.schema import Label


async def _translate_text(text: str, translate_language: str) -> str:
    """Translate a single text string to the specified language."""
    logger.info(f"Translation requested to {translate_language}")
    settings = get_settings()
    translate_prompt = settings.translate_prompt_template.format(
        language=translate_language
    )
    translator = get_chat_agent(
        model=settings.translation_model,
        prompt=translate_prompt,
        output_type=str,
        settings_override=settings.translation_model_samplers,
    )
    logger.info("Translator agent built successfully")

    result = await translator.run(text)
    logger.info("Translation task completed")

    return result.output.lstrip()


async def _translate_labels(
    labels: List[Label], translate_language: str
) -> List[Label]:
    """Translate text in labels to the specified language."""
    logger.info(f"Translation requested to {translate_language}")
    settings = get_settings()
    translate_prompt = settings.translate_prompt_template.format(
        language=translate_language
    )
    translator = get_chat_agent(
        model=settings.translation_model,
        prompt=translate_prompt,
        output_type=str,
        settings_override=settings.translation_model_samplers,
    )
    logger.info("Translator agent built successfully")

    # Create translation tasks
    translation_tasks = [translator.run(label.text) for label in labels]
    logger.info(f"Created {len(translation_tasks)} translation tasks")

    # Execute all translations concurrently
    translated_results = await asyncio.gather(*translation_tasks)
    logger.info("All translation tasks completed")

    # Update labels with translated text
    for label, result in zip(labels, translated_results):
        label.text = result.output.lstrip()
    logger.info("Translated results added to labels")
    return labels
