"""Structured logging system with performance monitoring."""
import logging
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

class StructuredFormatter(logging.Formatter):
    """JSON structured log formatter."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'message': record.getMessage()
        }
        
        # Add extra fields if present
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        if hasattr(record, 'duration'):
            log_entry['duration_ms'] = record.duration
        if hasattr(record, 'model'):
            log_entry['model'] = record.model
        if hasattr(record, 'error_type'):
            log_entry['error_type'] = record.error_type
            
        return json.dumps(log_entry)

def setup_logging(log_level: str = "INFO", log_file: str = "priya.log") -> logging.Logger:
    """Setup structured logging."""
    logger = logging.getLogger("priya")
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(StructuredFormatter())
    logger.addHandler(console_handler)
    
    # File handler
    log_path = Path(log_file)
    log_path.parent.mkdir(exist_ok=True)
    file_handler = logging.FileHandler(log_path)
    file_handler.setFormatter(StructuredFormatter())
    logger.addHandler(file_handler)
    
    return logger

class PerformanceLogger:
    """Performance monitoring and logging."""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.metrics = {}
    
    def log_request(self, user_id: str, model: str, duration: float, success: bool):
        """Log request performance."""
        self.logger.info(
            f"Request completed: model={model}, success={success}",
            extra={
                'user_id': user_id,
                'model': model,
                'duration': duration * 1000,  # Convert to ms
                'success': success
            }
        )
        
        # Update metrics
        key = f"{model}_{'success' if success else 'failure'}"
        if key not in self.metrics:
            self.metrics[key] = {'count': 0, 'total_time': 0}
        
        self.metrics[key]['count'] += 1
        if success:
            self.metrics[key]['total_time'] += duration
    
    def log_error(self, error: Exception, context: Dict[str, Any]):
        """Log error with context."""
        self.logger.error(
            f"Error occurred: {str(error)}",
            extra={
                'error_type': type(error).__name__,
                **context
            }
        )
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics."""
        return self.metrics.copy()

# Global logger instance
logger = setup_logging()
perf_logger = PerformanceLogger(logger)