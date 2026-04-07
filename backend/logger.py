import os
import sys

from loguru import logger


def configure_logging() -> None:
    logger.remove()

    level = os.getenv("LOG_LEVEL", "INFO").upper()
    log_file = os.getenv("LOG_FILE", "")

    logger.add(
        sys.stdout,
        level=level,
        colorize=True,
        backtrace=False,
        diagnose=False,
        enqueue=False,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> "
            "| <level>{level: <8}</level> "
            "| <cyan>{name}:{function}:{line}</cyan> "
            "- <level>{message}</level>"
        ),
    )

    if log_file:
        logger.add(
            log_file,
            level=level,
            rotation="10 MB",
            retention="7 days",
            compression="zip",
            backtrace=False,
            diagnose=False,
            enqueue=True,
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
        )
