"""
Logging utilities for KubeTimer operator.

Provides structured logging with support for JSON and text formats.
Uses structlog for structured, contextual logging.
"""

import logging
import sys

import structlog

from kubetimer.config.settings import get_settings

# Could we use lcu cache?
def setup_logging():
    """
    Configure logging for the operator.
    
    Sets up structlog with processors for structured logging.
    Supports both JSON (for production) and colored text (for development).
    
    Returns:
        A configured structlog logger instance
    """
    settings = get_settings()
    
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.log_level.upper()),
    )
    
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]
    
    if settings.log_format == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer(colors=True))

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    return structlog.get_logger()


def get_logger(name: str = None) -> structlog.stdlib.BoundLogger:
    """
    Args:
        name: Optional logger name (typically __name__ of the module)
    
    Returns:
        A structlog logger instance
    """
    return structlog.get_logger(name)
