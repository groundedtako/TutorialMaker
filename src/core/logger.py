"""
Centralized logging configuration for TutorialMaker
Provides consistent logging across all modules with proper log levels
"""

import logging
import sys
from pathlib import Path
from typing import Optional
import os
from datetime import datetime


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

        # Check environment variable for log level
        env_level = os.getenv('TUTORIALMAKER_LOG_LEVEL', 'INFO').upper()
        level_map = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }
        default_level = level_map.get(env_level, logging.INFO)

        # Console handler with formatting
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(default_level)

        # Create detailed formatter for console
        console_formatter = logging.Formatter(
            fmt='%(asctime)s [%(name)s] %(levelname)s: %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)

        # Add console handler to logger
        self.logger.addHandler(console_handler)

        # File handler for persistent logging
        try:
            # Create logs directory if it doesn't exist
            log_dir = Path('logs')
            log_dir.mkdir(exist_ok=True)
            
            # Create log file with timestamp
            log_file = log_dir / f"tutorialmaker_{datetime.now().strftime('%Y%m%d')}.log"
            
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)  # Log everything to file
            
            # More detailed formatter for file
            file_formatter = logging.Formatter(
                fmt='%(asctime)s [%(name)s] %(levelname)s: %(message)s (%(filename)s:%(lineno)d)',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_formatter)
            
            self.logger.addHandler(file_handler)
            self.file_handler = file_handler
            
        except Exception as e:
            # If file logging fails, continue with console only
            console_handler.setLevel(logging.DEBUG)
            self.logger.warning(f"Could not set up file logging: {e}")
            self.file_handler = None

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

def set_log_level(level: str):
    """
    Set logging level globally
    
    Args:
        level: Logging level ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
    """
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = TutorialMakerLogger()
    
    import logging
    level_map = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING, 
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }
    
    if level.upper() in level_map:
        _logger_instance.console_handler.setLevel(level_map[level.upper()])
        if level.upper() == 'DEBUG':
            _logger_instance.set_debug_mode(True)
        _logger_instance.logger.info(f"Logging level set to {level.upper()}")
    else:
        _logger_instance.logger.warning(f"Invalid log level: {level}. Using INFO.")

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

def exception(message: str):
    """Log an exception with traceback"""
    get_logger().exception(message)

def critical(message: str):
    """Log a critical message"""
    get_logger().critical(message)