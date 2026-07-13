from contextlib import contextmanager
from requests import exceptions

import logger

logger = logger.setup_logging(__name__)


@contextmanager
def fail_on_error():
    try:
        yield
    except (exceptions.RequestException, OSError, RuntimeError, AttributeError) as e:
        logger.error(f"Error: {e}")
