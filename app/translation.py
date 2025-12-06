import asyncio
from typing import List

from app.common import logger, TRANSLATION_MODEL, translation_model_samplers, LLM_BASE_URL
from app.dependencies import build_chat_agent
from app.schema import Label


async def _translate_labels(
    labels: List[Label],
    translate_language: str
) -> List[Label]:
    """Translate text in labels to the specified language."""
    logger.info(f"Translation requested to {translate_language}")
    TRANSLATE_PROMPT_TEMPLATE = f"""
    You are a professional translator specializing in accurate and natural translations.

    **Task:** Translate the given text into {translate_language}.

    **Requirements:**
    - Provide ONLY the translated text without any explanations or additional commentary
    - Preserve the original meaning, tone, and intent
    - Ensure the translation sounds natural and fluent to native speakers
    - Maintain any formatting, punctuation, or special characters where appropriate
    - If the text is already in {translate_language}, return it exactly as provided
    - For proper nouns (names, places, brands), use standard transliterations if applicable

    **Input:** Text to be translated
    **Output:** Translated text only
    """
    translate_prompt = TRANSLATE_PROMPT_TEMPLATE.format(language=translate_language)
    translator = build_chat_agent(
        f"{LLM_BASE_URL}/{TRANSLATION_MODEL}/v1",
        TRANSLATION_MODEL,
        translate_prompt,
        settings=translation_model_samplers,
        output_type=str
    )
    logger.info("Translator agent built successfully")

    # Create translation tasks
    translation_tasks = [
        translator.run(label.text) for label in labels
    ]
    logger.info(f"Created {len(translation_tasks)} translation tasks")

    # Execute all translations concurrently
    translated_results = await asyncio.gather(*translation_tasks)
    logger.info("All translation tasks completed")

    # Update labels with translated text
    for label, result in zip(labels, translated_results):
        label.text = result.output.lstrip()
    logger.info("Translated results added to labels")
    return labels
