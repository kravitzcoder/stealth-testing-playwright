# src/utils/logging_config.py

import logging
import sys

# Optional: Try to import colorlog for colored output
try:
    from colorlog import ColoredFormatter
    COLORLOG_AVAILABLE = True
except ImportError:
    COLORLOG_AVAILABLE = False

def setup_logging(level=logging.INFO):
    """
    Sets up a standardized logger for the application.
    
    If colorlog is available, it provides colored output for better readability.
    Otherwise, it falls back to a standard formatter.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Prevent duplicate handlers if this function is called multiple times
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    # Define a standard format
    log_format = (
        "%(asctime)s - "
        "%(name)s - "
        "%(levelname)s - "
        "%(message)s"
    )
    
    # Define a colored format if colorlog is installed
    color_log_format = (
        "%(log_color)s%(asctime)s - "
        "%(name)s - "
        "%(levelname)s - "
        "%(message)s"
    )

    # Use ColoredFormatter if available, otherwise fall back to standard Formatter
    if COLORLOG_AVAILABLE:
        formatter = ColoredFormatter(
            color_log_format,
            datefmt="%Y-%m-%d %H:%M:%S",
            reset=True,
            log_colors={
                'DEBUG':    'cyan',
                'INFO':     'green',
                'WARNING':  'yellow',
                'ERROR':    'red',
                'CRITICAL': 'red,bg_white',
            },
            secondary_log_colors={},
            style='%'
        )
    else:
        formatter = logging.Formatter(log_format, datefmt="%Y-%m-%d %H:%M:%S")

    # Create a handler to write to the console (stdout)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    
    # Add the handler to the root logger
    root_logger.addHandler(handler)

    # Silence overly verbose libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("websockets").setLevel(logging.WARNING)

    # Get the root logger for the main application part
    logger = logging.getLogger(__name__)
    if not COLORLOG_AVAILABLE:
        logger.warning("`colorlog` package not found. Logging will not be colored.")
        logger.warning("Install with: pip install colorlog")
