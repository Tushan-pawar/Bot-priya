"""Enhanced structured logging system with observability improvements."""
import logging
import sys
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path
from collections import defaultdict, deque

class ObservabilityLogger:
    """Enhanced logging with metrics tracking."""
    
    def __init__(self):
        self.metrics = {
            "response_latency": deque(maxlen=1000),
            "token_usage": defaultdict(int),
            "error_counts": defaultdict(int),
            "request_counts": defaultdict(int),
            "model_usage": defaultdict(int)
        }
        self.start_time = time.time()
    
    def log_response_latency(self, operation: str, duration: float, model: str = None):
        """Log response latency."""
        self.metrics["response_latency"].append({
            "operation": operation,
            "duration": duration,
            "model": model,
            "timestamp": time.time()
        })
        
        if model:
            self.metrics["model_usage"][model] += 1
    
    def log_token_usage(self, model: str, input_tokens: int, output_tokens: int):
        """Log token usage."""
        self.metrics["token_usage"][f"{model}_input"] += input_tokens
        self.metrics["token_usage"][f"{model}_output"] += output_tokens
        self.metrics["token_usage"]["total"] += input_tokens + output_tokens
    
    def log_error(self, error_type: str, context: Dict[str, Any] = None):
        """Log categorized error."""
        self.metrics["error_counts"][error_type] += 1
        
        # Log with context
        logger.error(f"Error: {error_type}", extra={
            "error_type": error_type,
            "context": context or {}
        })
    
    def log_request(self, request_type: str, user_id: str = None):
        """Log request."""
        self.metrics["request_counts"][request_type] += 1
        
        if user_id:
            self.metrics["request_counts"][f"user_{user_id}"] += 1
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get metrics summary."""
        now = time.time()
        uptime = now - self.start_time
        
        # Calculate average latency
        recent_latencies = [
            entry["duration"] for entry in self.metrics["response_latency"]
            if now - entry["timestamp"] < 3600  # Last hour
        ]
        avg_latency = sum(recent_latencies) / len(recent_latencies) if recent_latencies else 0
        
        return {
            "uptime_seconds": uptime,
            "total_requests": sum(self.metrics["request_counts"].values()),
            "total_errors": sum(self.metrics["error_counts"].values()),
            "avg_response_latency": avg_latency,
            "total_tokens": self.metrics["token_usage"]["total"],
            "error_rate": sum(self.metrics["error_counts"].values()) / max(1, sum(self.metrics["request_counts"].values())),
            "top_models": dict(sorted(self.metrics["model_usage"].items(), key=lambda x: x[1], reverse=True)[:5])
        }

class StructuredFormatter(logging.Formatter):
    """Enhanced JSON structured log formatter."""
    
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
        if hasattr(record, 'context'):
            log_entry['context'] = record.context
        if hasattr(record, 'tokens_used'):
            log_entry['tokens_used'] = record.tokens_used
        if hasattr(record, 'operation'):
            log_entry['operation'] = record.operation
            
        return json.dumps(log_entry)

def setup_logging(log_level: str = "INFO", log_file: str = "priya.log") -> logging.Logger:
    """Setup enhanced structured logging."""
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
    """Enhanced performance monitoring and logging."""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.observability = ObservabilityLogger()
    
    def log_request(self, user_id: str, model: str, duration: float, success: bool, 
                   tokens_used: int = 0, operation: str = "chat"):
        """Log request performance with enhanced metrics."""
        self.logger.info(
            f"Request completed: model={model}, success={success}",
            extra={
                'user_id': user_id,
                'model': model,
                'duration': duration * 1000,  # Convert to ms
                'success': success,
                'tokens_used': tokens_used,
                'operation': operation
            }
        )
        
        # Update observability metrics
        self.observability.log_response_latency(operation, duration, model)
        self.observability.log_request(operation, user_id)
        
        if tokens_used > 0:
            # Estimate input/output tokens (simplified)
            input_tokens = int(tokens_used * 0.7)
            output_tokens = tokens_used - input_tokens
            self.observability.log_token_usage(model, input_tokens, output_tokens)
    
    def log_error(self, error: Exception, context: Dict[str, Any]):
        """Log error with enhanced categorization."""
        error_type = type(error).__name__
        
        # Categorize errors
        if "timeout" in str(error).lower():
            error_category = "timeout_error"
        elif "rate" in str(error).lower() or "limit" in str(error).lower():
            error_category = "rate_limit_error"
        elif "connection" in str(error).lower() or "network" in str(error).lower():
            error_category = "network_error"
        elif "memory" in str(error).lower():
            error_category = "memory_error"
        elif "permission" in str(error).lower() or "auth" in str(error).lower():
            error_category = "auth_error"
        else:
            error_category = "general_error"
        
        self.observability.log_error(error_category, {
            "error_type": error_type,
            "error_message": str(error),
            **context
        })
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get comprehensive performance metrics."""
        return self.observability.get_metrics_summary()

# Global logger instance
logger = setup_logging()
perf_logger = PerformanceLogger(logger)