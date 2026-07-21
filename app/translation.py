"""
Translation utilities for Looking Glass.

Provides batch translation with caching support.
"""

import asyncio
import json
from typing import List

from pydantic import BaseModel

from app.common import logger
from app.config import get_settings
from app.container import get_chat_agent
from app.schema import Label
from app.cache import translation_cache


class TranslatedLabel(Label):
    """Label with translated text."""
    translated_text: str


async def translate_labels_with_cache(
    labels: List[Label],
    translate_language: str,
    image_hash: str,
) -> List[Label]:
    """
    Translate labels with caching support.
    
    Args:
        labels: List of labels to translate
        translate_language: Target language for translation
        image_hash: SHA256 hash of the source image
        
    Returns:
        List of labels with translated text
    """
    # Generate cache key
    cache_key = f"translation:{image_hash}:{translate_language}"
    
    # Check cache
    cached = translation_cache.get(cache_key)
    if cached is not None:
        logger.info(f"Cache hit for translation to {translate_language}")
        # Return a copy to prevent mutation
        return [
            Label(text=l.text, x1=l.x1, x2=l.x2, y1=l.y1, y2=l.y2)
            for l in cached
        ]
    
    # Cache miss - perform translation
    logger.info(f"Cache miss for translation to {translate_language}")
    translated_labels = await _translate_labels_batch(labels, translate_language)
    
    # Store in cache (copy to prevent mutation)
    translation_cache.set(
        cache_key,
        [Label(text=l.text, x1=l.x1, x2=l.x2, y1=l.y1, y2=l.y2) for l in translated_labels]
    )
    
    return translated_labels


async def _translate_text(text: str, translate_language: str) -> str:
    """Translate a single text string."""
    settings = get_settings()
    translate_prompt = settings.translate_prompt_template.format(language=translate_language)
    translator = get_chat_agent(
        model=settings.translation_model,
        prompt=translate_prompt,
        output_type=str,
    )
    
    result = await translator.run(text)
    return result.output.lstrip()


async def _translate_labels_batch(
    labels: List[Label],
    translate_language: str,
) -> List[Label]:
    """
    Batch translate all label texts in a single request.
    
    Uses Pydantic structured output for consistent results.
    """
    if not labels:
        return labels
    
    logger.info(f"Batch translation for {len(labels)} labels to {translate_language}")
    
    # Extract just the text strings for translation
    texts = [label.text for label in labels]
    batch_input_str = json.dumps(texts, ensure_ascii=False)
    
    logger.info(f"Translation input: {batch_input_str[:500]}{'...' if len(batch_input_str) > 500 else ''}")
    
    settings = get_settings()
    batch_prompt = settings.batch_translate_prompt_template.format(language=translate_language)
    
    # Use structured output with TranslatedLabel
    translator = get_chat_agent(
        model=settings.translation_model,
        prompt=batch_prompt,
        output_type=List[TranslatedLabel],
    )
    
    result = await translator.run(batch_input_str)
    translated_labels: List[TranslatedLabel] = result.output
    
    # Validate: ensure we got back the same number of labels
    if len(translated_labels) != len(labels):
        logger.warning(
            f"Translation returned {len(translated_labels)} labels, expected {len(labels)}. "
            "Falling back to individual translation."
        )
        return await _translate_labels_individual(labels, translate_language)
    
    # Update original labels with translated text
    for original, translated in zip(labels, translated_labels):
        original.text = translated.translated_text
    
    logger.info(f"Batch translation completed for {len(labels)} labels")
    return labels


async def _translate_labels_individual(
    labels: List[Label],
    translate_language: str,
) -> List[Label]:
    """Fallback: Translate each label individually, parallelized with asyncio.gather."""
    if not labels:
        return labels

    logger.info(f"Individual translation for {len(labels)} labels")

    tasks = [asyncio.create_task(_translate_text(label.text, translate_language)) for label in labels]
    translated_texts = await asyncio.gather(*tasks)
    for label, translated in zip(labels, translated_texts):
        label.text = translated

    return labels
