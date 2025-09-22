"""
Centralized logging configuration for TutorialMaker
Provides consistent logging across all modules with proper log levels
"""

import logging
import sys
from pathlib import Path
from typing import Optional


class TutorialMakerLogger:
    """Centralized logger configuration for TutorialMaker"""

    _instance: Optional['TutorialMakerLogger'] = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._setup_logging()
            TutorialMakerLogger._initialized = True

    def _setup_logging(self):
        """Set up logging configuration"""
        # Create main logger
        self.logger = logging.getLogger('tutorialmaker')
        self.logger.setLevel(logging.DEBUG)  # Capture all levels

        # Clear any existing handlers
        self.logger.handlers.clear()

        # Console handler with formatting
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)  # Default to INFO level

        # Create formatter
        formatter = logging.Formatter(
            fmt='%(levelname)s: %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(formatter)

        # Add handler to logger
        self.logger.addHandler(console_handler)

        # Store handler reference for level changes
        self.console_handler = console_handler

        # Prevent propagation to root logger
        self.logger.propagate = False

    def set_debug_mode(self, enabled: bool):
        """Enable or disable debug mode"""
        if enabled:
            self.console_handler.setLevel(logging.DEBUG)
            self.logger.debug("Debug mode enabled")
        else:
            self.console_handler.setLevel(logging.INFO)

    def get_logger(self, name: str = None) -> logging.Logger:
        """Get a logger instance for a specific module"""
        if name:
            return logging.getLogger(f'tutorialmaker.{name}')
        return self.logger


# Global logger instance
_logger_instance = None

def get_logger(name: str = None) -> logging.Logger:
    """
    Get a logger instance for the specified module

    Args:
        name: Module name (e.g., 'core.app', 'gui.main_window')

    Returns:
        Logger instance with TutorialMaker configuration
    """
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = TutorialMakerLogger()

    return _logger_instance.get_logger(name)

def set_debug_mode(enabled: bool):
    """
    Enable or disable debug logging globally

    Args:
        enabled: True to show DEBUG messages, False for INFO and above only
    """
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = TutorialMakerLogger()

    _logger_instance.set_debug_mode(enabled)

def info(message: str):
    """Log an info message"""
    get_logger().info(message)

def debug(message: str):
    """Log a debug message"""
    get_logger().debug(message)

def warning(message: str):
    """Log a warning message"""
    get_logger().warning(message)

def error(message: str):
    """Log an error message"""
    get_logger().error(message)