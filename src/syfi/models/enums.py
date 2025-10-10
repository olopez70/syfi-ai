"""
Banking domain enumerations for SyFi AI.

This module defines enums for account types, transaction types, and categories.
"""

from enum import Enum


class AccountType(Enum):
    """Types of bank accounts."""
    CHECKING = "checking"
    SAVINGS = "savings" 
    CREDIT = "credit"
    INVESTMENT = "investment"
    LOAN = "loan"


class TransactionType(Enum):
    """Types of banking transactions."""
    DEBIT = "debit"
    CREDIT = "credit"
    TRANSFER = "transfer"
    WITHDRAWAL = "withdrawal"
    DEPOSIT = "deposit"
    PAYMENT = "payment"
    FEE = "fee"


class TransactionCategory(Enum):
    """Categories for transaction classification."""
    SALARY = "salary"
    GROCERY = "grocery"
    GAS = "gas"
    UTILITIES = "utilities"
    ENTERTAINMENT = "entertainment"
    HEALTHCARE = "healthcare"
    SHOPPING = "shopping"
    RESTAURANT = "restaurant"
    ATM = "atm"
    TRANSFER = "transfer"
    FEE = "fee"
    OTHER = "other"