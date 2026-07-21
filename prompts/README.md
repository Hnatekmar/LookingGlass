# Prompt Templates

This directory contains LLM prompt templates used by the LookingGlass translation pipeline.
Prompts are loaded at runtime via `app/prompts.py` (`get_prompt()`).

## Files

### `label_detection.md` — Text Region Detection

- **Purpose:** Instructs the VLM to identify and localize all text regions in an image.
- **Coordinate scale:** 0–1000 (normalized). The output coordinates are divided by 1000.0 in `app/image_processing.py` to convert to 0–1 range for downstream processing.
- **Output format:** JSON array of `{"x1": float, "y1": float, "x2": float, "y2": float, "text": str}`.
- **Used by:** `app/image_processing.py` (via `get_prompt("label_detection.md")`).

### `translation_single.md` — Single Text Translation

- **Purpose:** Translates one text string into the target language.
- **Language placeholder:** `{language}` is replaced at runtime with the target language name (e.g., `"english"`, `"french"`).
- **Output format:** Plain text — the translated string only.
- **Used by:** `app/translation.py` → `_translate_text()`.

### `translation_batch.md` — Batch Text Translation

- **Purpose:** Translates multiple text strings in a single request, preserving order.
- **Language placeholder:** `{language}` is replaced at runtime.
- **Input placeholder:** `{{input}}` is replaced with the JSON array of text strings. Note the double-brace `{{ }}` — this avoids conflict with Python's `.format()` since the prompt is formatted with `.format(language=...)` before the `{{input}}` is available. After the `.format()` call, the double braces become single braces `{input}`, which the LLM receives as a literal placeholder.
- **Output format:** Structured via Pydantic (`List[TranslatedLabel]`), not by the prompt text. The prompt focuses on translation quality.
- **Used by:** `app/translation.py` → `_translate_labels_batch()`.

## How to Customize

1. **Edit a prompt file directly.** Changes take effect on the next process restart — no code changes needed.
2. **If you change the coordinate scale** in `label_detection.md` (e.g., from 0–1000 to 0–1), update the normalization divisor in `app/image_processing.py` to match.
3. **If you add a new prompt**:
   - Create a new `.md` file in this directory.
   - Load it with `get_prompt("your_file.md")`.
4. **If you rename or move a prompt file**, update the filename argument in the corresponding `get_prompt()` call.

## Format Contract

| File | Input | Output |
|---|---|---|
| `label_detection.md` | Image (binary/jpeg) | `list[Label]` — JSON with x1, y1, x2, y2, text |
| `translation_single.md` | Text string | Plain string translation |
| `translation_batch.md` | JSON array of strings | `list[TranslatedLabel]` — one per input |

All prompts are loaded fresh from disk on each call (no caching), so editing a prompt file and restarting the server is sufficient to pick up changes.
