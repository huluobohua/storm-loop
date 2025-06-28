"""
Logging utilities for STORM-Loop
"""
import sys
from loguru import logger
from storm_loop.config import get_config


def setup_logging():
    """Configure logging for STORM-Loop"""
    config = get_config()
    
    # Remove default handler
    logger.remove()
    
    # Add console handler with custom format
    logger.add(
        sys.stdout,
        level=config.log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
               "<level>{level: <8}</level> | "
               "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
               "<level>{message}</level>",
        colorize=True
    )
    
    # Add file handler
    logger.add(
        "logs/storm_loop.log",
        level=config.log_level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        rotation="10 MB",
        retention="1 week",
        compression="zip"
    )
    
    return logger


# Initialize logging
storm_logger = setup_logging()