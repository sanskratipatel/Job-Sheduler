import logging

from settings import settings


logger = logging.getLogger(settings.app_name)

if not logger.handlers:
    handler = logging.StreamHandler()

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    handler.setFormatter(formatter)
    logger.addHandler(handler)

logger.setLevel(
    logging.DEBUG
    if settings.environment == "dev"
    else logging.INFO
)

logger.propagate = False