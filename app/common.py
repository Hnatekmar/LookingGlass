import logging

from app.config import get_settings

# Get log level from Settings
settings = get_settings()
log_level = settings.log_level.upper()
log_level_value = getattr(logging, log_level, logging.INFO)

# Configure basic logging - set root logger level explicitly
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# Set the root logger level (this ensures all child loggers inherit it)
logging.getLogger().setLevel(log_level_value)

# Create a logger instance
logger = logging.getLogger(__name__)
logger.setLevel(log_level_value)
