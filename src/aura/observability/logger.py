"""Structured logging for AURA runtime."""
import logging


def get_logger(name: str) -> logging.Logger:
    """Get a configured logger for an AURA component."""
    return logging.getLogger(f"aura.{name}")
