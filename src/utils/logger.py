"""Logging configuration using loguru."""

import sys

from loguru import logger as _logger

from .config import settings

# Remove default handler
_logger.remove()

# Console handler with rich formatting
_logger.add(
    sys.stdout,
    format=(
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    ),
    level="DEBUG" if settings.app_debug else "INFO",
    colorize=True,
)

# File handler for persistent logs
_logger.add(
    "logs/seo_tool_{time:YYYY-MM-DD}.log",
    rotation="1 day",
    retention="30 days",
    compression="zip",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
    level="DEBUG",
    enqueue=True,
)

logger = _logger
