import logging

from pydantic_ai import ModelSettings

LLM_BASE_URL = "https://llm.hnatekmar.dev"

IMAGE_MODEL = "qwen3-8b-instruct"
TRANSLATION_MODEL = "hy-mt"
LABEL_PROMPT = """
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
"""

qwen3_instruct_sampler = ModelSettings(
    temperature=0.2,
    extra_body={
        "top_p": 0.8,
        "top_k": 20,
        "frequency_penalty": 1.5,
        "presence_penalty": 1.5,
        "max_completion_tokens": 16384
    }
)

qwen3_thinking_sampler = ModelSettings(
    temperature=1.0,
    extra_body={
        "top_p": 0.95,
        "top_k": 20,
        "presence_penalty": 0.0,
        "repetition_penalty": 1.0,
        "max_tokens": 40960
    }
)

deepseek_ocr_sampler = ModelSettings(
    temperature=0.0,
    extra_body={
        "skip_special_tokens": False,
        # args used to control custom logits processor
        "max_tokens": 4096,
        "vllm_xargs": {
            "ngram_size": 30,
            "window_size": 90,
            # whitelist: <td>, </td>
            "whitelist_token_ids": [128821, 128822],
        },
    }
)

image_model_samplers =  qwen3_instruct_sampler

translation_model_samplers = ModelSettings(
    temperature=0.7,
    extra_body={
        "top_p": 0.6,
        "top_k": 20,
        "frequency_penalty": 1.05,
        "max_completion_tokens": 8096
    }

)
# ModelSettings(
#     temperature=1,
#     extra_body={
#         "top_p": 1,
#         "chat_template_kwargs": {"enable_thinking": True},
#         "max_completion_tokens": 1024
#     }
# ) # qwen3_instruct_sampler

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# Create a logger instance
logger = logging.getLogger(__name__)
