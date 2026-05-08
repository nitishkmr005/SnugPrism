import sys
from loguru import logger
from config.settings import get_settings


def setup_logging() -> None:
    settings = get_settings()
    logger.remove()
    logger.add(sys.stderr, level=settings.log_level, colorize=True)
    settings.logs_dir.mkdir(parents=True, exist_ok=True)
    logger.add(
        str(settings.logs_dir / "app_{time}.json"),
        rotation="10 MB",
        retention=5,
        serialize=True,
        level="INFO",
    )
