"""
Logger utility for structured logging
"""

import logging
import sys
import json
from datetime import datetime
from typing import Optional, Dict, Any
from logging.handlers import RotatingFileHandler

def setup_logger(
    name: str,
    level: str = "INFO",
    log_file: Optional[str] = None,
    json_format: bool = False
) -> logging.Logger:
    """
    Set up a logger with specified configuration
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    
    # Remove existing handlers
    logger.handlers = []
    
    # Create formatter
    if json_format:
        formatter = JsonFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        try:
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=10 * 1024 * 1024,  # 10MB
                backupCount=5
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            logger.warning(f"Could not create file handler: {e}")
    
    return logger


class JsonFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON
        """
        log_obj = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields if present
        if hasattr(record, 'extra_fields'):
            log_obj.update(record.extra_fields)
        
        return json.dumps(log_obj)


class StructuredLogger:
    """
    Logger with structured logging support
    """
    
    def __init__(self, name: str):
        self.logger = setup_logger(name)
    
    def debug(self, message: str, **kwargs):
        """Log debug message with extra fields"""
        self._log(logging.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message with extra fields"""
        self._log(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message with extra fields"""
        self._log(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message with extra fields"""
        self._log(logging.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log critical message with extra fields"""
        self._log(logging.CRITICAL, message, **kwargs)
    
    def _log(self, level: int, message: str, **kwargs):
        """
        Internal logging method with extra fields
        """
        extra = {"extra_fields": kwargs} if kwargs else {}
        self.logger.log(level, message, extra=extra)


# Request/Response logging utilities
class RequestLogger:
    """
    Logger for API requests and responses
    """
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
    
    def log_request(
        self,
        method: str,
        path: str,
        headers: Dict[str, str],
        body: Optional[Any] = None
    ):
        """
        Log incoming request
        """
        self.logger.info(
            f"Request: {method} {path}",
            extra={
                "extra_fields": {
                    "request_method": method,
                    "request_path": path,
                    "request_headers": self._sanitize_headers(headers),
                    "request_body": self._truncate_body(body)
                }
            }
        )
    
    def log_response(
        self,
        status_code: int,
        duration: float,
        body: Optional[Any] = None
    ):
        """
        Log outgoing response
        """
        self.logger.info(
            f"Response: {status_code} in {duration:.3f}s",
            extra={
                "extra_fields": {
                    "response_status": status_code,
                    "response_duration": duration,
                    "response_body": self._truncate_body(body)
                }
            }
        )
    
    def _sanitize_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """
        Remove sensitive headers
        """
        sensitive_headers = ['authorization', 'api-key', 'x-api-key', 'cookie']
        sanitized = {}
        
        for key, value in headers.items():
            if key.lower() in sensitive_headers:
                sanitized[key] = "***"
            else:
                sanitized[key] = value
        
        return sanitized
    
    def _truncate_body(self, body: Any, max_length: int = 1000) -> Any:
        """
        Truncate body for logging
        """
        if body is None:
            return None
        
        body_str = str(body)
        if len(body_str) > max_length:
            return body_str[:max_length] + "..."
        
        return body