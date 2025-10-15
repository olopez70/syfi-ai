"""
Structured Logging Framework for SyFi AI

Provides enterprise-grade structured logging with JSON formatting,
correlation IDs, performance metrics, and comprehensive audit trails.
"""
import json
import logging
import logging.config
import sys
import time
import uuid
from datetime import datetime
from typing import Any, Dict, Optional, Union, List
from pathlib import Path
from contextlib import contextmanager
from functools import wraps
import threading
from dataclasses import dataclass, asdict
from enum import Enum

try:
    from ..exceptions import SyFiException
except ImportError:
    SyFiException = Exception


class LogLevel(Enum):
    """Standard log levels."""
    CRITICAL = "CRITICAL"
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"
    DEBUG = "DEBUG"


class LogCategory(Enum):
    """Log categories for better organization."""
    SYSTEM = "system"
    DATABASE = "database"
    SECURITY = "security"
    PERFORMANCE = "performance"
    AUDIT = "audit"
    DATA_GENERATION = "data_generation"
    EXPORT = "export"
    VALIDATION = "validation"
    USER_ACTION = "user_action"


@dataclass
class CorrelationContext:
    """Context for tracking requests across system components."""
    correlation_id: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    operation: Optional[str] = None
    request_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging."""
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class PerformanceMetrics:
    """Performance metrics for operations."""
    operation: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_ms: Optional[float] = None
    memory_usage_mb: Optional[float] = None
    cpu_percent: Optional[float] = None
    records_processed: Optional[int] = None
    
    def finalize(self):
        """Finalize metrics calculation."""
        if self.end_time is None:
            self.end_time = datetime.now()
        
        if self.duration_ms is None and self.start_time and self.end_time:
            delta = self.end_time - self.start_time
            self.duration_ms = delta.total_seconds() * 1000
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging."""
        result = {}
        for key, value in asdict(self).items():
            if value is not None:
                if isinstance(value, datetime):
                    result[key] = value.isoformat()
                else:
                    result[key] = value
        return result


class StructuredJSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""
    
    def __init__(self, include_extra: bool = True):
        super().__init__()
        self.include_extra = include_extra
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON."""
        # Base log structure
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'thread': record.thread,
            'thread_name': record.threadName,
            'process': record.process
        }
        
        # Add exception information if present
        if record.exc_info:
            log_entry['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': self.formatException(record.exc_info)
            }
        
        # Add extra fields from the record
        if self.include_extra and hasattr(record, '__dict__'):
            extra_fields = {}
            for key, value in record.__dict__.items():
                if key not in logging.LogRecord.__dict__ and not key.startswith('_'):
                    # Handle special objects
                    if isinstance(value, (CorrelationContext, PerformanceMetrics)):
                        extra_fields[key] = value.to_dict()
                    elif isinstance(value, (dict, list, str, int, float, bool, type(None))):
                        extra_fields[key] = value
                    else:
                        extra_fields[key] = str(value)
            
            if extra_fields:
                log_entry['extra'] = extra_fields
        
        return json.dumps(log_entry, ensure_ascii=False, separators=(',', ':'))


class CorrelationContextManager:
    """Thread-local correlation context management."""
    
    def __init__(self):
        self._local = threading.local()
    
    def set_context(self, context: CorrelationContext):
        """Set correlation context for current thread."""
        self._local.context = context
    
    def get_context(self) -> Optional[CorrelationContext]:
        """Get correlation context for current thread."""
        return getattr(self._local, 'context', None)
    
    def clear_context(self):
        """Clear correlation context for current thread."""
        if hasattr(self._local, 'context'):
            delattr(self._local, 'context')
    
    def generate_correlation_id(self) -> str:
        """Generate a new correlation ID."""
        return str(uuid.uuid4())
    
    @contextmanager
    def correlation_scope(self, **kwargs):
        """Context manager for correlation scope."""
        correlation_id = kwargs.get('correlation_id') or self.generate_correlation_id()
        
        context = CorrelationContext(
            correlation_id=correlation_id,
            **{k: v for k, v in kwargs.items() if k != 'correlation_id'}
        )
        
        # Store previous context
        previous_context = self.get_context()
        
        try:
            self.set_context(context)
            yield context
        finally:
            # Restore previous context
            if previous_context:
                self.set_context(previous_context)
            else:
                self.clear_context()


# Global correlation context manager
correlation_manager = CorrelationContextManager()


class SyFiLogger:
    """
    Enhanced logger with structured logging, correlation tracking,
    and performance monitoring capabilities.
    """
    
    def __init__(self, name: str, category: LogCategory = LogCategory.SYSTEM):
        self.name = name
        self.category = category
        self.logger = logging.getLogger(name)
        self._setup_logger()
    
    def _setup_logger(self):
        """Setup logger with structured formatting."""
        # Avoid duplicate handlers
        if self.logger.handlers:
            return
        
        # Console handler with JSON formatting
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(StructuredJSONFormatter())
        self.logger.addHandler(console_handler)
        
        # Set default level
        self.logger.setLevel(logging.INFO)
    
    def _enrich_log_data(self, extra_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich log data with context and category."""
        enriched = {
            'category': self.category.value,
            **extra_data
        }
        
        # Add correlation context if available
        context = correlation_manager.get_context()
        if context:
            enriched['correlation'] = context.to_dict()
        
        return enriched
    
    def debug(self, message: str, **kwargs):
        """Log debug message with structured data."""
        extra_data = self._enrich_log_data(kwargs)
        self.logger.debug(message, extra=extra_data)
    
    def info(self, message: str, **kwargs):
        """Log info message with structured data."""
        extra_data = self._enrich_log_data(kwargs)
        self.logger.info(message, extra=extra_data)
    
    def warning(self, message: str, **kwargs):
        """Log warning message with structured data."""
        extra_data = self._enrich_log_data(kwargs)
        self.logger.warning(message, extra=extra_data)
    
    def error(self, message: str, **kwargs):
        """Log error message with structured data."""
        extra_data = self._enrich_log_data(kwargs)
        self.logger.error(message, extra=extra_data)
    
    def critical(self, message: str, **kwargs):
        """Log critical message with structured data."""
        extra_data = self._enrich_log_data(kwargs)
        self.logger.critical(message, extra=extra_data)
    
    def audit(self, action: str, **kwargs):
        """Log audit event with structured data."""
        extra_data = self._enrich_log_data({
            'audit_action': action,
            'audit_timestamp': datetime.now().isoformat(),
            **kwargs
        })
        self.logger.info(f"AUDIT: {action}", extra=extra_data)
    
    def performance(self, metrics: PerformanceMetrics, **kwargs):
        """Log performance metrics."""
        metrics.finalize()
        extra_data = self._enrich_log_data({
            'performance': metrics.to_dict(),
            **kwargs
        })
        
        # Determine log level based on performance
        if metrics.duration_ms and metrics.duration_ms > 5000:  # 5 seconds
            level = 'warning'
            message = f"SLOW OPERATION: {metrics.operation} took {metrics.duration_ms:.1f}ms"
        else:
            level = 'info'
            message = f"PERFORMANCE: {metrics.operation} completed in {metrics.duration_ms:.1f}ms"
        
        getattr(self.logger, level)(message, extra=extra_data)
    
    def database_operation(self, operation: str, query: str = None, 
                          params: tuple = None, **kwargs):
        """Log database operation with security considerations."""
        # Sanitize query for logging (remove sensitive data)
        safe_query = self._sanitize_query(query) if query else None
        
        extra_data = self._enrich_log_data({
            'database_operation': operation,
            'query': safe_query,
            'param_count': len(params) if params else 0,
            **kwargs
        })
        
        self.logger.info(f"DATABASE: {operation}", extra=extra_data)
    
    def security_event(self, event_type: str, severity: str = "info", **kwargs):
        """Log security-related events."""
        extra_data = self._enrich_log_data({
            'security_event': event_type,
            'security_severity': severity,
            'security_timestamp': datetime.now().isoformat(),
            **kwargs
        })
        
        message = f"SECURITY: {event_type}"
        
        # Map severity to log level
        level_map = {
            'critical': 'critical',
            'high': 'error',
            'medium': 'warning',
            'low': 'info',
            'info': 'info'
        }
        
        level = level_map.get(severity.lower(), 'info')
        getattr(self.logger, level)(message, extra=extra_data)
    
    def _sanitize_query(self, query: str) -> str:
        """Sanitize SQL query for safe logging."""
        if not query:
            return None
        
        # Remove potential sensitive data patterns
        import re
        
        # Replace string literals with placeholders
        sanitized = re.sub(r"'[^']*'", "'***'", query)
        sanitized = re.sub(r'"[^"]*"', '"***"', sanitized)
        
        # Truncate very long queries
        if len(sanitized) > 200:
            sanitized = sanitized[:200] + "..."
        
        return sanitized


class LoggingConfigManager:
    """Manages logging configuration for different environments."""
    
    @staticmethod
    def setup_production_logging(
        log_level: str = "INFO",
        log_file: Optional[str] = None,
        max_file_size: int = 100 * 1024 * 1024,  # 100MB
        backup_count: int = 5
    ):
        """Setup production logging configuration."""
        
        config = {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'structured_json': {
                    '()': StructuredJSONFormatter,
                    'include_extra': True
                }
            },
            'handlers': {
                'console': {
                    'class': 'logging.StreamHandler',
                    'level': log_level,
                    'formatter': 'structured_json',
                    'stream': 'ext://sys.stdout'
                }
            },
            'root': {
                'level': log_level,
                'handlers': ['console']
            },
            'loggers': {
                'syfi': {
                    'level': log_level,
                    'handlers': ['console'],
                    'propagate': False
                }
            }
        }
        
        # Add file handler if specified
        if log_file:
            Path(log_file).parent.mkdir(parents=True, exist_ok=True)
            
            config['handlers']['file'] = {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': log_level,
                'formatter': 'structured_json',
                'filename': log_file,
                'maxBytes': max_file_size,
                'backupCount': backup_count,
                'encoding': 'utf-8'
            }
            
            # Add file handler to root and syfi loggers
            config['root']['handlers'].append('file')
            config['loggers']['syfi']['handlers'].append('file')
        
        logging.config.dictConfig(config)
    
    @staticmethod
    def setup_development_logging(log_level: str = "DEBUG"):
        """Setup development logging with readable format."""
        
        config = {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'development': {
                    'format': '%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s',
                    'datefmt': '%Y-%m-%d %H:%M:%S'
                }
            },
            'handlers': {
                'console': {
                    'class': 'logging.StreamHandler',
                    'level': log_level,
                    'formatter': 'development',
                    'stream': 'ext://sys.stdout'
                }
            },
            'root': {
                'level': log_level,
                'handlers': ['console']
            }
        }
        
        logging.config.dictConfig(config)


# Performance monitoring decorators

def log_performance(operation_name: str = None, logger: SyFiLogger = None):
    """
    Decorator to automatically log performance metrics for functions.
    
    Args:
        operation_name: Name of the operation (defaults to function name)
        logger: Logger instance (creates default if not provided)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal logger
            if logger is None:
                logger = SyFiLogger(f"{func.__module__}.{func.__name__}", LogCategory.PERFORMANCE)
            
            op_name = operation_name or f"{func.__module__}.{func.__name__}"
            
            # Start performance tracking
            metrics = PerformanceMetrics(
                operation=op_name,
                start_time=datetime.now()
            )
            
            try:
                # Get memory usage before operation
                import psutil
                process = psutil.Process()
                initial_memory = process.memory_info().rss / 1024 / 1024  # MB
                
                result = func(*args, **kwargs)
                
                # Calculate final metrics
                final_memory = process.memory_info().rss / 1024 / 1024  # MB
                metrics.memory_usage_mb = final_memory - initial_memory
                metrics.cpu_percent = process.cpu_percent()
                
                # Log successful completion
                logger.performance(metrics, success=True)
                
                return result
                
            except Exception as e:
                # Log failed operation
                logger.performance(metrics, success=False, error=str(e))
                raise
            
        return wrapper
    return decorator


def log_audit(action: str, logger: SyFiLogger = None):
    """
    Decorator to automatically log audit events for functions.
    
    Args:
        action: Audit action description
        logger: Logger instance (creates default if not provided)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal logger
            if logger is None:
                logger = SyFiLogger(f"{func.__module__}.{func.__name__}", LogCategory.AUDIT)
            
            # Extract context from args/kwargs if available
            audit_context = {}
            
            # Try to extract user context
            for arg in args:
                if hasattr(arg, 'user_id'):
                    audit_context['user_id'] = arg.user_id
                    break
            
            try:
                result = func(*args, **kwargs)
                
                # Log successful audit event
                logger.audit(action, success=True, **audit_context)
                
                return result
                
            except Exception as e:
                # Log failed audit event
                logger.audit(action, success=False, error=str(e), **audit_context)
                raise
            
        return wrapper
    return decorator


# Convenience functions for common logging patterns

def get_logger(name: str, category: LogCategory = LogCategory.SYSTEM) -> SyFiLogger:
    """Get a SyFi logger instance."""
    return SyFiLogger(name, category)


def get_database_logger(name: str) -> SyFiLogger:
    """Get a database-specific logger."""
    return SyFiLogger(name, LogCategory.DATABASE)


def get_security_logger(name: str) -> SyFiLogger:
    """Get a security-specific logger."""
    return SyFiLogger(name, LogCategory.SECURITY)


def get_performance_logger(name: str) -> SyFiLogger:
    """Get a performance-specific logger."""
    return SyFiLogger(name, LogCategory.PERFORMANCE)


# Context managers for correlation tracking

@contextmanager
def correlation_context(**kwargs):
    """Context manager for correlation tracking."""
    with correlation_manager.correlation_scope(**kwargs) as context:
        yield context


@contextmanager
def audit_context(user_id: str = None, session_id: str = None, operation: str = None):
    """Context manager for audit tracking."""
    correlation_id = correlation_manager.generate_correlation_id()
    
    with correlation_manager.correlation_scope(
        correlation_id=correlation_id,
        user_id=user_id,
        session_id=session_id,
        operation=operation
    ) as context:
        yield context


# Initialize default logging for the package
def initialize_logging(environment: str = "production", **kwargs):
    """
    Initialize logging for the SyFi package.
    
    Args:
        environment: 'production' or 'development'
        **kwargs: Additional configuration options
    """
    if environment.lower() == "development":
        LoggingConfigManager.setup_development_logging(
            log_level=kwargs.get('log_level', 'DEBUG')
        )
    else:
        LoggingConfigManager.setup_production_logging(
            log_level=kwargs.get('log_level', 'INFO'),
            log_file=kwargs.get('log_file'),
            max_file_size=kwargs.get('max_file_size', 100 * 1024 * 1024),
            backup_count=kwargs.get('backup_count', 5)
        )


# Example usage patterns
if __name__ == "__main__":
    # Initialize logging
    initialize_logging("development")
    
    # Create loggers
    app_logger = get_logger(__name__)
    db_logger = get_database_logger("syfi.database")
    security_logger = get_security_logger("syfi.security")
    
    # Basic logging
    app_logger.info("Application started", version="1.0.0", environment="development")
    
    # Correlation context example
    with correlation_context(user_id="user123", operation="data_export"):
        app_logger.info("Starting data export")
        
        # Performance logging
        metrics = PerformanceMetrics("data_export", datetime.now())
        time.sleep(0.1)  # Simulate work
        app_logger.performance(metrics)
        
        # Database logging
        db_logger.database_operation("SELECT", "SELECT * FROM customers LIMIT 10")
        
        # Security logging
        security_logger.security_event("data_access", "low", table="customers")
    
    # Audit logging
    with audit_context(user_id="admin", operation="system_configuration"):
        app_logger.audit("configuration_change", setting="log_level", new_value="DEBUG")