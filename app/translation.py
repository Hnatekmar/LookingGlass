from typing import List
from pydantic import BaseModel

from app.common import logger
from app.config import get_settings
from app.container import get_chat_agent
from app.schema import Label


class TranslatedItem(BaseModel):
    """Translated item with original ID."""

    id: int
    translated_text: str


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


async def _translate_labels_batch(
    labels: List[Label], translate_language: str
) -> List[Label]:
    """
    Batch translate all label texts in a single request using JSON format.

    This is more efficient than translating each label individually:
    - Single API call instead of N parallel calls
    - Better token utilization
    - Consistent translation context across all text
    - Structured JSON input/output with Pydantic validation
    """
    if not labels:
        return labels

    logger.info(
        f"Batch translation requested for {len(labels)} labels to {translate_language}"
    )

    # Prepare batched input as JSON string
    import json

    batch_input = [{"id": i, "text": label.text} for i, label in enumerate(labels)]
    batch_input_str = json.dumps(batch_input, ensure_ascii=False)

    settings = get_settings()
    # Use a prompt template that expects JSON input and JSON output
    batch_prompt = settings.batch_translate_prompt_template.format(
        language=translate_language
    )

    translator = get_chat_agent(
        model=settings.translation_model,
        prompt=batch_prompt,
        output_type=List[TranslatedItem],  # Pydantic will parse JSON automatically
        settings_override=settings.translation_model_samplers,
    )
    logger.info("Batch translator agent built successfully")

    # Single translation request for all labels
    result = await translator.run(batch_input_str)
    logger.info("Batch translation completed")

    # Get the parsed list - output_type should handle JSON parsing
    translated_raw = result.output

    # Handle different output formats
    if isinstance(translated_raw, str):
        # Parse JSON string
        import json

        translated_list = json.loads(translated_raw)
        # Convert dicts to TranslatedItem objects
        translated_items = [
            TranslatedItem(id=item["id"], translated_text=item["translated_text"])
            for item in translated_list
        ]
    elif isinstance(translated_raw, list):
        # Already a list, might be dicts or TranslatedItems
        if isinstance(translated_raw[0], dict):
            translated_items = [
                TranslatedItem(id=item["id"], translated_text=item["translated_text"])
                for item in translated_raw
            ]
        else:
            translated_items = translated_raw  # Already TranslatedItem objects
    else:
        raise ValueError(f"Unexpected output type: {type(translated_raw)}")

    # Create a mapping from ID to translated text
    translated_map = {item.id: item.translated_text for item in translated_items}

    # Update labels with translated text based on ID
    for i, label in enumerate(labels):
        if i in translated_map:
            label.text = translated_map[i]

    logger.info(f"Updated {len(labels)} labels with batch translations")
    return labels