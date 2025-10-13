# Schema management package
"""
Database schema management for SyFi AI.

Provides schema versioning, validation, and safe database operations
that gracefully handle different database configurations.
"""

from .schema_manager import (
    SchemaManager, SchemaVersion, SCHEMA_DEFINITIONS,
    get_schema_manager
)
from .schema_aware_db import (
    SchemaAwareConnection, SchemaAwareMetricsCalculator
)

__all__ = [
    'SchemaManager',
    'SchemaVersion', 
    'SCHEMA_DEFINITIONS',
    'get_schema_manager',
    'SchemaAwareConnection',
    'SchemaAwareMetricsCalculator'
]