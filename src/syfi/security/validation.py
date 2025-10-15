"""
Input Validation and Security Framework for SyFi AI

Provides comprehensive validation, sanitization, and security
controls for all user inputs and system operations.
"""
import re
import os
import logging
from pathlib import Path
from typing import Any, List, Dict, Optional, Union, Callable
from dataclasses import dataclass
from enum import Enum

from ..exceptions import SyFiValidationError, SyFiSecurityError


class ValidationType(Enum):
    """Types of validation operations."""
    REQUIRED = "required"
    TYPE_CHECK = "type_check"
    RANGE_CHECK = "range_check"
    PATTERN_MATCH = "pattern_match"
    WHITELIST = "whitelist"
    BLACKLIST = "blacklist"
    CUSTOM = "custom"


@dataclass
class ValidationRule:
    """
    Defines a validation rule with context and error messages.
    """
    rule_type: ValidationType
    message: str
    constraint: Any = None
    severity: str = "error"  # error, warning, info
    
    def __post_init__(self):
        """Validate the rule definition itself."""
        if not self.message:
            raise ValueError("Validation rule must have a message")


class InputValidator:
    """
    Comprehensive input validation with security controls.
    """
    
    # Security patterns for common attacks
    SQL_INJECTION_PATTERNS = [
        r"(\bUNION\b|\bSELECT\b|\bINSERT\b|\bUPDATE\b|\bDELETE\b|\bDROP\b)",
        r"(--|\#|\/\*|\*\/)",
        r"(\bOR\b.*=.*\bOR\b|\bAND\b.*=.*\bAND\b)",
        r"(\'.*\'|\".*\")",
        r"(\bEXEC\b|\bEXECUTE\b)"
    ]
    
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe[^>]*>.*?</iframe>",
        r"<object[^>]*>.*?</object>"
    ]
    
    PATH_TRAVERSAL_PATTERNS = [
        r"\.\.\/",
        r"\.\.[/\\]",
        r"\/etc\/",
        r"\/proc\/",
        r"\/sys\/",
        r"C:\\Windows\\",
        r"C:\\System32\\"
    ]
    
    # Whitelisted table names for database operations
    ALLOWED_TABLE_NAMES = {
        'customers', 'accounts', 'transactions', 'products',
        'merchants', 'branches', 'employees', 'audit_logs'
    }
    
    # Whitelisted file extensions for exports
    ALLOWED_EXPORT_EXTENSIONS = {
        '.csv', '.json', '.xml', '.txt', '.xlsx', '.sql'
    }
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def validate_required(self, value: Any, field_name: str) -> Any:
        """
        Validate that a required field has a value.
        
        Args:
            value: Value to validate
            field_name: Name of the field for error messages
            
        Returns:
            The validated value
            
        Raises:
            SyFiValidationError: If value is None, empty, or whitespace-only
        """
        if value is None:
            raise SyFiValidationError(
                f"Field '{field_name}' is required but was None",
                field_name=field_name,
                field_value=value,
                validation_rule="required"
            )
        
        if isinstance(value, str) and not value.strip():
            raise SyFiValidationError(
                f"Field '{field_name}' is required but was empty or whitespace",
                field_name=field_name,
                field_value=value,
                validation_rule="required"
            )
        
        if isinstance(value, (list, dict)) and len(value) == 0:
            raise SyFiValidationError(
                f"Field '{field_name}' is required but was empty",
                field_name=field_name,
                field_value=value,
                validation_rule="required"
            )
        
        return value
    
    def validate_type(self, value: Any, expected_type: type, field_name: str) -> Any:
        """
        Validate that a value is of the expected type.
        
        Args:
            value: Value to validate
            expected_type: Expected Python type
            field_name: Name of the field for error messages
            
        Returns:
            The validated value
            
        Raises:
            SyFiValidationError: If value is not of expected type
        """
        if not isinstance(value, expected_type):
            raise SyFiValidationError(
                f"Field '{field_name}' must be of type {expected_type.__name__}, got {type(value).__name__}",
                field_name=field_name,
                field_value=value,
                validation_rule=f"type:{expected_type.__name__}"
            )
        
        return value
    
    def validate_range(self, value: Union[int, float], min_val: Optional[float] = None, 
                      max_val: Optional[float] = None, field_name: str = None) -> Union[int, float]:
        """
        Validate that a numeric value is within specified range.
        
        Args:
            value: Numeric value to validate
            min_val: Minimum allowed value (inclusive)
            max_val: Maximum allowed value (inclusive)
            field_name: Name of the field for error messages
            
        Returns:
            The validated value
            
        Raises:
            SyFiValidationError: If value is outside allowed range
        """
        if not isinstance(value, (int, float)):
            raise SyFiValidationError(
                f"Range validation requires numeric value, got {type(value).__name__}",
                field_name=field_name,
                field_value=value,
                validation_rule="numeric_range"
            )
        
        if min_val is not None and value < min_val:
            raise SyFiValidationError(
                f"Field '{field_name}' value {value} is below minimum {min_val}",
                field_name=field_name,
                field_value=value,
                validation_rule=f"min:{min_val}"
            )
        
        if max_val is not None and value > max_val:
            raise SyFiValidationError(
                f"Field '{field_name}' value {value} exceeds maximum {max_val}",
                field_name=field_name,
                field_value=value,
                validation_rule=f"max:{max_val}"
            )
        
        return value
    
    def validate_pattern(self, value: str, pattern: str, field_name: str, 
                        description: str = None) -> str:
        """
        Validate that a string matches a regular expression pattern.
        
        Args:
            value: String value to validate
            pattern: Regular expression pattern
            field_name: Name of the field for error messages
            description: Human-readable description of the pattern
            
        Returns:
            The validated value
            
        Raises:
            SyFiValidationError: If value doesn't match pattern
        """
        if not isinstance(value, str):
            raise SyFiValidationError(
                f"Pattern validation requires string value, got {type(value).__name__}",
                field_name=field_name,
                field_value=value,
                validation_rule="pattern_match"
            )
        
        if not re.match(pattern, value):
            desc = description or f"pattern {pattern}"
            raise SyFiValidationError(
                f"Field '{field_name}' value '{value}' does not match required {desc}",
                field_name=field_name,
                field_value=value,
                validation_rule=f"pattern:{pattern}"
            )
        
        return value
    
    def validate_whitelist(self, value: Any, allowed_values: List[Any], 
                          field_name: str) -> Any:
        """
        Validate that a value is in the allowed whitelist.
        
        Args:
            value: Value to validate
            allowed_values: List of allowed values
            field_name: Name of the field for error messages
            
        Returns:
            The validated value
            
        Raises:
            SyFiValidationError: If value is not in whitelist
        """
        if value not in allowed_values:
            raise SyFiValidationError(
                f"Field '{field_name}' value '{value}' is not in allowed values: {allowed_values}",
                field_name=field_name,
                field_value=value,
                validation_rule=f"whitelist:{allowed_values}"
            )
        
        return value
    
    def validate_table_name(self, table_name: str) -> str:
        """
        Validate and sanitize database table names for security.
        
        Args:
            table_name: Table name to validate
            
        Returns:
            The validated table name
            
        Raises:
            SyFiSecurityError: If table name is not allowed
        """
        if not isinstance(table_name, str):
            raise SyFiValidationError(
                "Table name must be a string",
                field_name="table_name",
                field_value=table_name,
                validation_rule="type:string"
            )
        
        # Remove any whitespace and convert to lowercase
        clean_name = table_name.strip().lower()
        
        # Check against whitelist
        if clean_name not in self.ALLOWED_TABLE_NAMES:
            raise SyFiSecurityError(
                f"Table name '{table_name}' is not in allowed list",
                security_context="table_validation",
                resource=table_name,
                action="database_access"
            )
        
        # Additional security checks
        self._check_sql_injection(clean_name, "table_name")
        
        return clean_name
    
    def validate_file_path(self, file_path: str, base_dir: str = None) -> str:
        """
        Validate and sanitize file paths to prevent directory traversal.
        
        Args:
            file_path: File path to validate
            base_dir: Base directory to restrict access to
            
        Returns:
            The validated and sanitized file path
            
        Raises:
            SyFiSecurityError: If path contains security risks
        """
        if not isinstance(file_path, str):
            raise SyFiValidationError(
                "File path must be a string",
                field_name="file_path",
                field_value=file_path,
                validation_rule="type:string"
            )
        
        # Check for path traversal attacks
        self._check_path_traversal(file_path, "file_path")
        
        # Resolve and normalize the path
        try:
            resolved_path = Path(file_path).resolve()
        except (OSError, ValueError) as e:
            raise SyFiSecurityError(
                f"Invalid file path: {file_path}",
                security_context="path_validation",
                resource=file_path,
                action="file_access"
            ) from e
        
        # Check base directory restriction
        if base_dir:
            base_path = Path(base_dir).resolve()
            try:
                resolved_path.relative_to(base_path)
            except ValueError:
                raise SyFiSecurityError(
                    f"File path '{file_path}' is outside allowed directory '{base_dir}'",
                    security_context="path_validation",
                    resource=str(resolved_path),
                    action="file_access"
                )
        
        # Check file extension if it's a file
        if resolved_path.suffix:
            if resolved_path.suffix.lower() not in self.ALLOWED_EXPORT_EXTENSIONS:
                raise SyFiSecurityError(
                    f"File extension '{resolved_path.suffix}' is not allowed",
                    security_context="file_extension_validation",
                    resource=str(resolved_path),
                    action="file_create"
                )
        
        return str(resolved_path)
    
    def _check_sql_injection(self, value: str, field_name: str) -> None:
        """Check for SQL injection patterns."""
        for pattern in self.SQL_INJECTION_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                raise SyFiSecurityError(
                    f"Potential SQL injection detected in field '{field_name}'",
                    security_context="sql_injection_prevention",
                    resource=value,
                    action="input_validation"
                )
    
    def _check_xss(self, value: str, field_name: str) -> None:
        """Check for XSS patterns."""
        for pattern in self.XSS_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                raise SyFiSecurityError(
                    f"Potential XSS attack detected in field '{field_name}'",
                    security_context="xss_prevention",
                    resource=value,
                    action="input_validation"
                )
    
    def _check_path_traversal(self, value: str, field_name: str) -> None:
        """Check for path traversal patterns."""
        for pattern in self.PATH_TRAVERSAL_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                raise SyFiSecurityError(
                    f"Potential path traversal attack detected in field '{field_name}'",
                    security_context="path_traversal_prevention",
                    resource=value,
                    action="input_validation"
                )


class BusinessRuleValidator:
    """
    Business logic validation specific to SyFi AI domain.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.input_validator = InputValidator()
    
    def validate_customer_data(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate customer data according to business rules.
        
        Args:
            customer_data: Dictionary containing customer information
            
        Returns:
            Validated customer data
            
        Raises:
            SyFiValidationError: If validation fails
        """
        # Required fields
        required_fields = ['customer_id', 'name', 'email']
        for field in required_fields:
            self.input_validator.validate_required(
                customer_data.get(field), field
            )
        
        # Type validation
        self.input_validator.validate_type(
            customer_data['customer_id'], (int, str), 'customer_id'
        )
        self.input_validator.validate_type(
            customer_data['name'], str, 'name'
        )
        self.input_validator.validate_type(
            customer_data['email'], str, 'email'
        )
        
        # Email pattern validation
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        self.input_validator.validate_pattern(
            customer_data['email'], 
            email_pattern,
            'email',
            'valid email format'
        )
        
        # Optional fields validation
        if 'phone' in customer_data:
            phone_pattern = r'^\+?[\d\s\-\(\)]{10,15}$'
            self.input_validator.validate_pattern(
                customer_data['phone'],
                phone_pattern,
                'phone',
                'valid phone number format'
            )
        
        if 'age' in customer_data:
            self.input_validator.validate_range(
                customer_data['age'], 
                min_val=18, 
                max_val=120,
                field_name='age'
            )
        
        return customer_data
    
    def validate_account_data(self, account_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate account data according to business rules.
        
        Args:
            account_data: Dictionary containing account information
            
        Returns:
            Validated account data
            
        Raises:
            SyFiValidationError: If validation fails
        """
        # Required fields
        required_fields = ['account_id', 'customer_id', 'account_type', 'balance']
        for field in required_fields:
            self.input_validator.validate_required(
                account_data.get(field), field
            )
        
        # Account type validation
        allowed_types = ['checking', 'savings', 'credit', 'investment', 'loan']
        self.input_validator.validate_whitelist(
            account_data['account_type'].lower(),
            allowed_types,
            'account_type'
        )
        
        # Balance validation
        self.input_validator.validate_type(
            account_data['balance'], (int, float), 'balance'
        )
        
        # Business rule: Credit accounts can have negative balance
        if account_data['account_type'].lower() != 'credit':
            self.input_validator.validate_range(
                account_data['balance'],
                min_val=0,
                field_name='balance'
            )
        
        return account_data
    
    def validate_export_configuration(self, export_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate export configuration data.
        
        Args:
            export_config: Export configuration dictionary
            
        Returns:
            Validated export configuration
            
        Raises:
            SyFiValidationError: If validation fails
        """
        # Required fields
        required_fields = ['format', 'output_path', 'tables']
        for field in required_fields:
            self.input_validator.validate_required(
                export_config.get(field), field
            )
        
        # Format validation
        allowed_formats = ['csv', 'json', 'xml', 'excel', 'sql']
        self.input_validator.validate_whitelist(
            export_config['format'].lower(),
            allowed_formats,
            'format'
        )
        
        # Path validation
        self.input_validator.validate_file_path(export_config['output_path'])
        
        # Tables validation
        if isinstance(export_config['tables'], list):
            for table in export_config['tables']:
                self.input_validator.validate_table_name(table)
        else:
            self.input_validator.validate_table_name(export_config['tables'])
        
        # Record count validation if present
        if 'record_count' in export_config:
            self.input_validator.validate_range(
                export_config['record_count'],
                min_val=1,
                max_val=1000000,  # 1M records max
                field_name='record_count'
            )
        
        return export_config


# Validation decorators for easy integration

def validate_input(**validation_rules):
    """
    Decorator to validate function input parameters.
    
    Usage:
        @validate_input(
            name={'type': str, 'required': True},
            age={'type': int, 'range': (18, 120)},
            email={'pattern': r'^[^@]+@[^@]+\.[^@]+$'}
        )
        def create_customer(name, age=None, email=None):
            pass
    """
    from functools import wraps
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get function signature
            import inspect
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            
            validator = InputValidator()
            
            # Validate each parameter
            for param_name, rules in validation_rules.items():
                if param_name in bound_args.arguments:
                    value = bound_args.arguments[param_name]
                    
                    # Required check
                    if rules.get('required', False):
                        validator.validate_required(value, param_name)
                    
                    # Skip further validation if value is None and not required
                    if value is None:
                        continue
                    
                    # Type check
                    if 'type' in rules:
                        validator.validate_type(value, rules['type'], param_name)
                    
                    # Range check
                    if 'range' in rules:
                        min_val, max_val = rules['range']
                        validator.validate_range(value, min_val, max_val, param_name)
                    
                    # Pattern check
                    if 'pattern' in rules:
                        validator.validate_pattern(
                            value, rules['pattern'], param_name,
                            rules.get('pattern_description')
                        )
                    
                    # Whitelist check
                    if 'whitelist' in rules:
                        validator.validate_whitelist(
                            value, rules['whitelist'], param_name
                        )
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def sanitize_output(func):
    """
    Decorator to sanitize function output for security.
    """
    from functools import wraps
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        
        # Sanitize sensitive information in output
        if isinstance(result, dict):
            result = _sanitize_dict(result)
        elif isinstance(result, list):
            result = [_sanitize_dict(item) if isinstance(item, dict) else item for item in result]
        
        return result
    
    return wrapper


def _sanitize_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """Remove or mask sensitive fields in dictionary output."""
    sensitive_fields = {
        'password', 'ssn', 'social_security_number', 'credit_card_number',
        'cvv', 'pin', 'secret', 'key', 'token', 'api_key'
    }
    
    sanitized = {}
    for key, value in data.items():
        if key.lower() in sensitive_fields:
            sanitized[key] = "***REDACTED***"
        else:
            sanitized[key] = value
    
    return sanitized