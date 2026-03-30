"""Logging helpers for the CLI."""

import logging

LOGGER_NAME = "adb_bug_report_generator"


def setup_logging(verbose=False):
    """Configure and return the project logger."""
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)

    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
        logger.addHandler(handler)

    logger.propagate = False
    return logger
