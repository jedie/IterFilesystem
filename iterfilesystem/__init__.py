__version__ = '1.4.2'

import logging
import sys

log = logging.getLogger(__name__)


def log_configured(logger=None):
    if logger is None:
        logger = logging.getLogger()

    try:
        handler = logger.handlers[0]
    except IndexError:
        return False
    else:
        if handler.level == logging.NOTSET:
            return False

    return True


def setup_logging():
    """
    Log to stdout if logger not configured, yet.
    """
    if log_configured(logger=log):
        # logger is configured -> do nothing
        return

    # Activate logging to stdout

    handler = logging.StreamHandler(stream=sys.stdout)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(message)s')
    handler.setFormatter(formatter)

    log.propagate = False
    log.setLevel(logging.INFO)
    log.addHandler(handler)
