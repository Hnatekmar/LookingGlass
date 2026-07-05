"""Tests for the common/logging module."""

import logging
from app.common import logger, log_level


def test_logger_exists():
    """Test that the logger is properly configured."""
    assert logger is not None
    assert isinstance(logger, logging.Logger)


def test_logger_name():
    """Test the logger name matches the module path."""
    assert logger.name == "app.common"


def test_log_level_is_valid():
    """Test that the log level is a valid logging level."""
    valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    assert log_level in valid_levels
