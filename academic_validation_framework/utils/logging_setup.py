"""
Logging setup utilities for Academic Validation Framework.

This module provides utilities to configure logging at the application level,
ensuring proper separation of concerns and avoiding duplicate handlers.
"""

import logging
import sys
from pathlib import Path
from typing import Optional


def setup_framework_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    console_logging: bool = True,
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
) -> None:
    """
    Configure logging for the Academic Validation Framework at application startup.
    
    This function should be called once at the beginning of your application,
    before creating any framework instances.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional path to log file
        console_logging: Whether to enable console logging
        log_format: Format string for log messages
    
    Example:
        >>> from academic_validation_framework.utils.logging_setup import setup_framework_logging
        >>> setup_framework_logging(log_level="DEBUG", log_file="validation.log")
        >>> # Now create framework instances...
    """
    # Get the framework's root logger
    logger = logging.getLogger('academic_validation_framework')
    
    # Set log level
    try:
        level = getattr(logging, log_level.upper())
    except AttributeError:
        print(f"Invalid log level: {log_level}. Using INFO.", file=sys.stderr)
        level = logging.INFO
    
    logger.setLevel(level)
    
    # Clear any existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(log_format)
    
    # Add file handler if log file specified
    if log_file:
        try:
            # Ensure log directory exists
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            print(f"Failed to create log file handler: {e}", file=sys.stderr)
    
    # Add console handler if enabled
    if console_logging:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    # Log initialization
    logger.info(f"Academic Validation Framework logging initialized at {log_level} level")


def get_framework_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module within the framework.
    
    Args:
        name: Module name (e.g., 'validators.prisma_validator')
    
    Returns:
        Configured logger instance
    """
    return logging.getLogger(f'academic_validation_framework.{name}')


def configure_test_logging() -> None:
    """
    Configure logging specifically for testing scenarios.
    
    This sets up minimal logging to avoid cluttering test output.
    """
    setup_framework_logging(
        log_level="WARNING",
        console_logging=True,
        log_file=None
    )