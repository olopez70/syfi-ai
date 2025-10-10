"""
Data profiling package for SyFi AI.

This package provides comprehensive data profiling capabilities specifically
designed for synthetic banking data, including customer demographics,
account relationships, and transaction patterns.
"""

from .analyzer import BankingDataProfiler
from .banking_metrics import BankingMetricsCalculator
from .reporters import ProfileReporter

__all__ = [
    'BankingDataProfiler',
    'BankingMetricsCalculator', 
    'ProfileReporter'
]