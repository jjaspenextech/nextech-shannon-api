import logging
import sys
import traceback
from pathlib import Path
from logging.handlers import RotatingFileHandler

# Create logs directory if it doesn't exist
logs_dir = Path("logs")
logs_dir.mkdir(exist_ok=True)

class CustomLogger(logging.Logger):
    def error(self, msg, *args, **kwargs):
        super().error(msg, *args, **kwargs)
        # if we have an exception argument, print the stack trace
        # if 'exc_info' in kwargs and kwargs['exc_info']:
        super().error(f"Stack trace: {traceback.format_exc()}")

# Configure logging
def setup_logger(name: str) -> logging.Logger:
    logger = CustomLogger(name)
    logger.setLevel(logging.ERROR)

    # Format for our log messages
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File Handler
    file_handler = RotatingFileHandler(
        logs_dir / "app.log",
        maxBytes=10485760,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger

logger = setup_logger(__name__)
