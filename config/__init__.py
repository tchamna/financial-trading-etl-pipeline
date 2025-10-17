"""
Configuration Package for Financial Trading ETL Pipeline
====================================================

This package centralizes all configuration for the project.

- `settings.py`: Core system configuration (database, S3, APIs, etc.)
- `user.py`: User-facing settings (symbols, intervals, features)

The `get_config()` function in `settings.py` is the main entry point
to access the combined configuration.
"""

from .settings import get_config, PipelineConfig
from .user import (
    STOCK_SYMBOLS,
    CRYPTO_SYMBOLS,
    # Add other user-configurable variables here as needed
)

__all__ = [
    "get_config",
    "PipelineConfig",
    "STOCK_SYMBOLS",
    "CRYPTO_SYMBOLS",
]
