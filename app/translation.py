import hashlib
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

import json

from pydantic import BaseModel

from app.common import logger
from app.config import get_settings
from app.container import get_chat_agent
from app.schema import Label


class TranslatedItem(BaseModel):
    """Translated item with original ID."""

    id: int
    translated_text: str


# In-memory cache for translations
# Structure: {cache_key: {"labels": List[Label], "timestamp": float}}
_translation_cache: Dict[str, Dict[str, Any]] = {}
_cache_ttl_seconds = 3600  # 1 hour default TTL
_max_cache_size = 1000  # Maximum number of cached items


@dataclass
class TranslationCacheStats:
    """Translation cache statistics."""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    
    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0


_translation_cache_stats = TranslationCacheStats()


def get_translation_cache_key(image_hash: str, language: str) -> str:
    """Generate a cache key for translation results.
    
    Args:
        image_hash: SHA256 hash of the source image
        language: Target translation language
        
    Returns:
        Cache key string
    """
    return f"translation:{image_hash}:{language}"


def _clean_translation_cache():
    """Remove expired entries from the translation cache."""
    current_time = time.time()
    expired_keys = [
        key for key, value in _translation_cache.items()
        if current_time - value["timestamp"] > _cache_ttl_seconds
    ]
    for key in expired_keys:
        del _translation_cache[key]
        _translation_cache_stats.evictions += 1
    
    # Also enforce max size
    if len(_translation_cache) > _max_cache_size:
        # Remove oldest entries
        sorted_keys = sorted(
            _translation_cache.keys(),
            key=lambda k: _translation_cache[k]["timestamp"]
        )
        keys_to_remove = sorted_keys[:len(_translation_cache) - _max_cache_size]
        for key in keys_to_remove:
            del _translation_cache[key]
            _translation_cache_stats.evictions += 1


async def translate_labels_with_cache(
    labels: List[Label],
    translate_language: str,
    image_hash: str
) -> List[Label]:
    """Translate labels with caching support.
    
    Args:
        labels: List of labels to translate
        translate_language: Target language for translation
        image_hash: SHA256 hash of the source image
        
    Returns:
        List of labels with translated text
    """
    global _translation_cache_stats
    
    # Generate cache key
    cache_key = get_translation_cache_key(image_hash, translate_language)
    
    # Clean expired entries periodically
    if len(_translation_cache) % 100 == 0:
        _clean_translation_cache()
    
    # Check cache
    if cache_key in _translation_cache:
        cached = _translation_cache[cache_key]
        if time.time() - cached["timestamp"] <= _cache_ttl_seconds:
            _translation_cache_stats.hits += 1
            logger.info(f"Cache hit for translation to {translate_language} (hash: {image_hash[:16]}...)")
            # Return a copy to prevent mutation of cached data
            cached_labels = cached["labels"]
            return [Label(text=l.text, x1=l.x1, x2=l.x2, y1=l.y1, y2=l.y2) for l in cached_labels]
    
    # Cache miss - perform translation
    _translation_cache_stats.misses += 1
    logger.info(f"Cache miss for translation to {translate_language} (hash: {image_hash[:16]}...)")
    
    translated_labels = await _translate_labels_batch(labels, translate_language)
    
    # Store in cache (store a copy to prevent mutation)
    _translation_cache[cache_key] = {
        "labels": [Label(text=l.text, x1=l.x1, x2=l.x2, y1=l.y1, y2=l.y2) for l in translated_labels],
        "timestamp": time.time()
    }
    
    return translated_labels


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
    """
    Translate all label texts individually using parallel API calls.

    This is less efficient than batch translation:
    - N API calls (one per label) instead of 1
    - Higher latency due to sequential processing
    - Inconsistent translation context across labels
    """
    if not labels:
        return labels

    logger.info(
        f"Individual translation requested for {len(labels)} labels to {translate_language}"
    )

    # Translate each label individually
    for label in labels:
        label.text = await _translate_text(label.text, translate_language)

    logger.info(f"Updated {len(labels)} labels with individual translations")
    return labels



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
