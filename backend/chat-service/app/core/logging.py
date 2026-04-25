import logging
import sys
from app.core.config import settings


def setup_logging():
    """
    Configure application logging.
    """
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("aioredis").setLevel(logging.WARNING)
    
    return logging.getLogger(__name__)


logger = setup_logging()
