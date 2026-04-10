"""
Logging Utility
Simple logging configuration
"""
import logging
import sys


def setup_logger(name):
    """
    Setup and return a logger
    
    :param name: Logger name
    :return: Logger instance
    """
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        
        # Console handler
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '[%(levelname)s] %(name)s: %(message)s'
        )
        handler.setFormatter(formatter)
        
        logger.addHandler(handler)
    
    return logger
