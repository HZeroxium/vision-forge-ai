# app/utils/logger.py
import logging
import sys
from logging.handlers import RotatingFileHandler
import colorlog


def setup_logger():
    """Configure the root logger with colored output for console and file logging."""

    # Define a color formatter for console logs
    log_colors = {
        "DEBUG": "cyan",
        "INFO": "green",
        "WARNING": "yellow",
        "ERROR": "red",
        "CRITICAL": "bold_red",
    }

    color_formatter = colorlog.ColoredFormatter(
        "%(log_color)s%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        log_colors=log_colors,
        reset=True,
        style="%",
    )

    # Define a normal formatter for file logging
    file_formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s - %(message)s"
    )

    # Configure file handler with UTF-8 encoding
    file_handler = RotatingFileHandler(
        "app.log", maxBytes=10**6, backupCount=3, encoding="utf-8"
    )
    file_handler.setFormatter(file_formatter)

    # Configure console handler with UTF-8 encoding and color output
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(color_formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)  # Ensure all log levels are captured

    if not root_logger.hasHandlers():  # Prevent duplicate handlers
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)

    root_logger.info(
        "Logger is set up successfully with UTF-8 support and color output"
    )


def get_logger(name: str) -> logging.Logger:
    """Helper to get logger with a specific name."""
    return logging.getLogger(name)
