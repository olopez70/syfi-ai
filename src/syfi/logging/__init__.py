"""
Logging package for SyFi AI.

Provides enterprise-grade structured logging with JSON formatting,
correlation IDs, performance metrics, and audit trails.
"""

from .structured_logging import (
    SyFiLogger, LogLevel, LogCategory, CorrelationContext, PerformanceMetrics,
    LoggingConfigManager, get_logger, get_database_logger, get_security_logger,
    get_performance_logger, correlation_context, audit_context, initialize_logging,
    log_performance, log_audit, correlation_manager
)

__all__ = [
    'SyFiLogger',
    'LogLevel', 
    'LogCategory',
    'CorrelationContext',
    'PerformanceMetrics',
    'LoggingConfigManager',
    'get_logger',
    'get_database_logger', 
    'get_security_logger',
    'get_performance_logger',
    'correlation_context',
    'audit_context',
    'initialize_logging',
    'log_performance',
    'log_audit',
    'correlation_manager'
]