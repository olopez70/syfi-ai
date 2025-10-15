"""
Database package for SyFi AI.

Provides resilient database operations, connection pooling,
and comprehensive error handling for production environments.
"""

from .resilience import ResilientDatabase, ConnectionPool, CircuitBreaker

__all__ = [
    'ResilientDatabase',
    'ConnectionPool', 
    'CircuitBreaker'
]

# Maintain compatibility with existing DatabaseManager imports
def __getattr__(name):
    if name == 'DatabaseManager':
        from .. import database as db_module
        return db_module.DatabaseManager
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")