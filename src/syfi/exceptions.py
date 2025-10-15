"""
Custom Exception Hierarchy for SyFi AI

Provides a structured exception framework with context preservation
and proper error categorization for production environments.
"""
import logging
from datetime import datetime
from typing import Dict, Any, Optional


class SyFiException(Exception):
    """
    Base exception class for all SyFi AI specific errors.
    
    Provides common functionality for error context, logging, and debugging.
    """
    
    def __init__(
        self, 
        message: str, 
        error_code: str = None,
        context: Dict[str, Any] = None,
        original_exception: Exception = None
    ):
        """
        Initialize SyFi exception with enhanced context.
        
        Args:
            message: Human-readable error description
            error_code: Unique error code for categorization
            context: Additional context for debugging
            original_exception: Original exception that caused this error
        """
        self.message = message
        self.error_code = error_code or self.__class__.__name__.upper()
        self.context = context or {}
        self.original_exception = original_exception
        self.timestamp = datetime.now()
        
        # Add system context
        self.context.update({
            'timestamp': self.timestamp.isoformat(),
            'exception_type': self.__class__.__name__,
            'error_code': self.error_code
        })
        
        # Log the exception with structured data
        self._log_exception()
        
        super().__init__(self.message)
    
    def _log_exception(self):
        """Log the exception with structured context."""
        logger = logging.getLogger(__name__)
        
        log_data = {
            'error_code': self.error_code,
            'message': self.message,
            'context': self.context,
            'original_exception': str(self.original_exception) if self.original_exception else None
        }
        
        logger.error(f"SyFi Exception: {self.error_code}", extra=log_data)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for serialization."""
        return {
            'error_code': self.error_code,
            'message': self.message,
            'context': self.context,
            'timestamp': self.timestamp.isoformat(),
            'original_exception': str(self.original_exception) if self.original_exception else None
        }


class SyFiDatabaseError(SyFiException):
    """
    Database-related errors including connection failures, 
    schema issues, and query problems.
    """
    
    def __init__(
        self, 
        message: str, 
        query: str = None,
        params: tuple = None,
        database_path: str = None,
        original_exception: Exception = None
    ):
        context = {
            'query': query,
            'params': str(params) if params else None,
            'database_path': database_path
        }
        
        super().__init__(
            message=message,
            error_code="DATABASE_ERROR",
            context=context,
            original_exception=original_exception
        )


class SyFiValidationError(SyFiException):
    """
    Input validation and data integrity errors.
    """
    
    def __init__(
        self, 
        message: str,
        field_name: str = None,
        field_value: Any = None,
        validation_rule: str = None,
        original_exception: Exception = None
    ):
        context = {
            'field_name': field_name,
            'field_value': str(field_value) if field_value is not None else None,
            'validation_rule': validation_rule
        }
        
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR", 
            context=context,
            original_exception=original_exception
        )


class SyFiConfigurationError(SyFiException):
    """
    Configuration and environment setup errors.
    """
    
    def __init__(
        self, 
        message: str,
        config_key: str = None,
        config_value: Any = None,
        environment: str = None,
        original_exception: Exception = None
    ):
        context = {
            'config_key': config_key,
            'config_value': str(config_value) if config_value is not None else None,
            'environment': environment
        }
        
        super().__init__(
            message=message,
            error_code="CONFIGURATION_ERROR",
            context=context,
            original_exception=original_exception
        )


class SyFiSecurityError(SyFiException):
    """
    Security-related errors including authentication,
    authorization, and input sanitization failures.
    """
    
    def __init__(
        self, 
        message: str,
        security_context: str = None,
        user_id: str = None,
        resource: str = None,
        action: str = None,
        original_exception: Exception = None
    ):
        context = {
            'security_context': security_context,
            'user_id': user_id,
            'resource': resource,
            'action': action
        }
        
        super().__init__(
            message=message,
            error_code="SECURITY_ERROR",
            context=context,
            original_exception=original_exception
        )


class SyFiPerformanceError(SyFiException):
    """
    Performance-related errors including timeouts,
    memory issues, and resource exhaustion.
    """
    
    def __init__(
        self, 
        message: str,
        operation: str = None,
        duration_ms: float = None,
        memory_usage_mb: float = None,
        threshold_exceeded: str = None,
        original_exception: Exception = None
    ):
        context = {
            'operation': operation,
            'duration_ms': duration_ms,
            'memory_usage_mb': memory_usage_mb,
            'threshold_exceeded': threshold_exceeded
        }
        
        super().__init__(
            message=message,
            error_code="PERFORMANCE_ERROR",
            context=context,
            original_exception=original_exception
        )


class SyFiExportError(SyFiException):
    """
    Export and data generation errors.
    """
    
    def __init__(
        self, 
        message: str,
        export_format: str = None,
        export_path: str = None,
        record_count: int = None,
        schema_version: str = None,
        original_exception: Exception = None
    ):
        context = {
            'export_format': export_format,
            'export_path': export_path,
            'record_count': record_count,
            'schema_version': schema_version
        }
        
        super().__init__(
            message=message,
            error_code="EXPORT_ERROR",
            context=context,
            original_exception=original_exception
        )


class SyFiSchemaError(SyFiException):
    """
    Database schema management errors including
    version mismatches and compatibility issues.
    """
    
    def __init__(
        self, 
        message: str,
        expected_schema: str = None,
        actual_schema: str = None,
        missing_tables: list = None,
        missing_columns: list = None,
        original_exception: Exception = None
    ):
        context = {
            'expected_schema': expected_schema,
            'actual_schema': actual_schema,
            'missing_tables': missing_tables or [],
            'missing_columns': missing_columns or []
        }
        
        super().__init__(
            message=message,
            error_code="SCHEMA_ERROR",
            context=context,
            original_exception=original_exception
        )


class SyFiUnexpectedError(SyFiException):
    """
    Unexpected errors that don't fit other categories.
    Used as a catch-all for proper error handling.
    """
    
    def __init__(
        self, 
        message: str = "An unexpected error occurred",
        operation: str = None,
        original_exception: Exception = None
    ):
        context = {
            'operation': operation,
            'unexpected': True
        }
        
        super().__init__(
            message=message,
            error_code="UNEXPECTED_ERROR",
            context=context,
            original_exception=original_exception
        )


# Exception handling utilities

class ExceptionHandler:
    """
    Centralized exception handling with recovery strategies.
    """
    
    @staticmethod
    def handle_database_error(
        operation: str,
        original_exception: Exception,
        retry_count: int = 0,
        max_retries: int = 3
    ) -> bool:
        """
        Handle database errors with retry logic.
        
        Returns:
            True if operation should be retried, False otherwise
        """
        if retry_count < max_retries:
            # Log retry attempt
            logger = logging.getLogger(__name__)
            logger.warning(
                f"Database operation failed, retrying ({retry_count + 1}/{max_retries})",
                extra={
                    'operation': operation,
                    'retry_count': retry_count,
                    'error': str(original_exception)
                }
            )
            return True
        
        # Max retries exceeded, raise SyFi exception
        raise SyFiDatabaseError(
            f"Database operation '{operation}' failed after {max_retries} retries",
            original_exception=original_exception
        )
    
    @staticmethod
    def handle_validation_error(
        field_name: str,
        field_value: Any,
        validation_rule: str,
        fallback_value: Any = None
    ) -> Any:
        """
        Handle validation errors with optional fallback values.
        
        Returns:
            Fallback value if provided, otherwise raises SyFiValidationError
        """
        if fallback_value is not None:
            logger = logging.getLogger(__name__)
            logger.warning(
                f"Validation failed for {field_name}, using fallback value",
                extra={
                    'field_name': field_name,
                    'invalid_value': str(field_value),
                    'fallback_value': str(fallback_value),
                    'validation_rule': validation_rule
                }
            )
            return fallback_value
        
        raise SyFiValidationError(
            f"Validation failed for field '{field_name}': {validation_rule}",
            field_name=field_name,
            field_value=field_value,
            validation_rule=validation_rule
        )


# Error recovery decorators

def with_database_retry(max_retries: int = 3, backoff_factor: float = 1.5):
    """
    Decorator for database operations with exponential backoff retry.
    """
    import time
    from functools import wraps
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    if attempt < max_retries:
                        # Calculate backoff time
                        backoff_time = backoff_factor ** attempt
                        
                        logger = logging.getLogger(func.__module__)
                        logger.warning(
                            f"Operation {func.__name__} failed, retrying in {backoff_time:.1f}s",
                            extra={
                                'attempt': attempt + 1,
                                'max_retries': max_retries,
                                'backoff_time': backoff_time,
                                'error': str(e)
                            }
                        )
                        
                        time.sleep(backoff_time)
                    else:
                        # Final attempt failed
                        raise SyFiDatabaseError(
                            f"Operation {func.__name__} failed after {max_retries} retries",
                            original_exception=last_exception
                        )
            
            # Should never reach here, but just in case
            raise SyFiUnexpectedError(
                f"Unexpected state in retry decorator for {func.__name__}",
                original_exception=last_exception
            )
        
        return wrapper
    return decorator


def with_error_context(operation: str):
    """
    Decorator to add operation context to any exceptions.
    """
    from functools import wraps
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except SyFiException:
                # SyFi exceptions already have context, re-raise as-is
                raise
            except Exception as e:
                # Convert generic exceptions to SyFi exceptions with context
                raise SyFiUnexpectedError(
                    f"Unexpected error during {operation}",
                    operation=operation,
                    original_exception=e
                ) from e
        
        return wrapper
    return decorator