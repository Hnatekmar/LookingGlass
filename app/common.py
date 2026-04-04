import logging
from app.config import settings

# Import configuration from Settings instance
LLM_BASE_URL = settings.llm_base_url
IMAGE_MODEL = settings.image_model
TRANSLATION_MODEL = settings.translation_model
LABEL_PROMPT = settings.label_prompt

# Import model samplers from Settings instance
qwen3_instruct_sampler = settings.qwen3_instruct_sampler
qwen3_thinking_sampler = settings.qwen3_thinking_sampler

image_model_samplers = settings.image_model_samplers
translation_model_samplers = settings.translation_model_samplers

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# Create a logger instance
logger = logging.getLogger(__name__)
