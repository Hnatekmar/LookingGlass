import logging
import os

# Get log level from environment variable, default to INFO
log_level = os.getenv("LOG_LEVEL", "DEBUG").upper()
log_level_value = getattr(logging, log_level, logging.DEBUG)

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
