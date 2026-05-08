import logging
import json
import sys
from datetime import datetime
from config.settings import settings

class EnterpriseJSONFormatter(logging.Formatter):
    """Custom formatter to output logs as strictly structured JSON."""
    def format(self, record):
        log_record = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "module": record.module,
            "message": record.getMessage(),
        }
        
        # Automatically append stack traces if an exception occurs
        if record.exc_info:
            log_record["error_trace"] = self.formatException(record.exc_info)
            
        # Append extra context if passed dynamically (e.g., user_id, correlation_id)
        if hasattr(record, "extra_context"):
            log_record.update(record.extra_context)
            
        return json.dumps(log_record)

def setup_logger():
    logger = logging.getLogger("RubikaOSINT")
    
    # Map the string log level from .env to Python's logging constants
    level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    logger.setLevel(level)

    # Prevent duplicate logs if the logger is imported multiple times
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(EnterpriseJSONFormatter())
        logger.addHandler(handler)
        
    logger.propagate = False
    return logger

# Expose the configured logger
logger = setup_logger()