import logging
import sys


def configure_logging() -> None:
    """
    Sets up structured, consistent logging for the whole application.
    Called once, at application startup, from main.py.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )