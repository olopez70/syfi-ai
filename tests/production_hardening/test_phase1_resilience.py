"""
Tests for Production Hardening Framework - Phase 1: Error Handling & Resilience

Tests the custom exception hierarchy, input validation framework,
and database resilience patterns implemented for production environments.
"""
import pytest
import sqlite3
import tempfile
import threading
import time
import os
from unittest.mock import Mock, patch
from pathlib import Path
from typing import Dict, Any

from src.syfi.exceptions import (
    SyFiException, SyFiDatabaseError, SyFiValidationError, 
    SyFiConfigurationError, SyFiSecurityError, SyFiPerformanceError,
    SyFiExportError, SyFiSchemaError, SyFiUnexpectedError,
    ExceptionHandler, with_database_retry, with_error_context
)
from src.syfi.security.validation import (
    InputValidator, BusinessRuleValidator, validate_input, sanitize_output
)
from src.syfi.database.resilience import (
    ResilientDatabase, ConnectionPool, CircuitBreaker, CircuitBreakerState
)
from src.syfi.schema_management.schema_aware_db import SchemaAwareConnection


class TestCustomExceptions:
    """Test custom SyFi exception hierarchy."""
    
    def test_base_exception_creation(self):
        """Test SyFiException base functionality."""
        original_error = ValueError("Original error")
        context = {"operation": "test", "user_id": "123"}
        
        exc = SyFiException(
            "Test error message",
            error_code="TEST_ERROR",
            context=context,
            original_exception=original_error
        )
        
        assert exc.message == "Test error message"
        assert exc.error_code == "TEST_ERROR"
        assert exc.context["operation"] == "test"
        assert exc.context["user_id"] == "123"
        assert exc.original_exception == original_error
        assert exc.timestamp is not None
        
        # Test serialization
        error_dict = exc.to_dict()
        assert error_dict["error_code"] == "TEST_ERROR"
        assert error_dict["message"] == "Test error message"
        assert error_dict["context"]["operation"] == "test"
    
    def test_database_error_context(self):
        """Test SyFiDatabaseError with query context."""
        query = "SELECT * FROM customers WHERE id = ?"
        params = ("123",)
        
        exc = SyFiDatabaseError(
            "Database query failed",
            query=query,
            params=params,
            database_path="/test/db.sqlite",
            original_exception=sqlite3.Error("Connection failed")
        )
        
        assert exc.error_code == "DATABASE_ERROR"
        assert exc.context["query"] == query
        assert exc.context["params"] == str(params)
        assert exc.context["database_path"] == "/test/db.sqlite"
    
    def test_validation_error_field_context(self):
        """Test SyFiValidationError with field context."""
        exc = SyFiValidationError(
            "Invalid email format",
            field_name="email",
            field_value="invalid-email",
            validation_rule="email_format"
        )
        
        assert exc.error_code == "VALIDATION_ERROR"
        assert exc.context["field_name"] == "email"
        assert exc.context["field_value"] == "invalid-email"
        assert exc.context["validation_rule"] == "email_format"
    
    def test_security_error_context(self):
        """Test SyFiSecurityError with security context."""
        exc = SyFiSecurityError(
            "Potential SQL injection detected",
            security_context="input_validation",
            user_id="user123",
            resource="customer_query",
            action="database_access"
        )
        
        assert exc.error_code == "SECURITY_ERROR"
        assert exc.context["security_context"] == "input_validation"
        assert exc.context["user_id"] == "user123"
        assert exc.context["resource"] == "customer_query"
        assert exc.context["action"] == "database_access"
    
    def test_exception_handler_retry_logic(self):
        """Test ExceptionHandler retry mechanisms."""
        # Test successful retry
        retry_result = ExceptionHandler.handle_database_error(
            "test_operation",
            sqlite3.Error("Temporary failure"),
            retry_count=0,
            max_retries=3
        )
        assert retry_result is True
        
        # Test max retries exceeded
        with pytest.raises(SyFiDatabaseError):
            ExceptionHandler.handle_database_error(
                "test_operation",
                sqlite3.Error("Persistent failure"),
                retry_count=3,
                max_retries=3
            )
    
    def test_retry_decorator(self):
        """Test database retry decorator."""
        call_count = 0
        
        @with_database_retry(max_retries=2)
        def flaky_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise sqlite3.Error("Temporary failure")
            return "success"
        
        # Should succeed after retries
        result = flaky_function()
        assert result == "success"
        assert call_count == 3
    
    def test_error_context_decorator(self):
        """Test error context decorator."""
        @with_error_context("user_registration")
        def failing_function():
            raise ValueError("Generic error")
        
        with pytest.raises(SyFiUnexpectedError) as exc_info:
            failing_function()
        
        exc = exc_info.value
        assert exc.context["operation"] == "user_registration"
        assert isinstance(exc.original_exception, ValueError)


class TestInputValidation:
    """Test input validation and security framework."""
    
    @pytest.fixture
    def validator(self):
        """Create InputValidator instance."""
        return InputValidator()
    
    @pytest.fixture 
    def business_validator(self):
        """Create BusinessRuleValidator instance."""
        return BusinessRuleValidator()
    
    def test_required_validation(self, validator):
        """Test required field validation."""
        # Valid cases
        assert validator.validate_required("test", "field") == "test"
        assert validator.validate_required(123, "number") == 123
        assert validator.validate_required(["item"], "list") == ["item"]
        
        # Invalid cases
        with pytest.raises(SyFiValidationError):
            validator.validate_required(None, "field")
        
        with pytest.raises(SyFiValidationError):
            validator.validate_required("", "field")
        
        with pytest.raises(SyFiValidationError):
            validator.validate_required("   ", "field")
        
        with pytest.raises(SyFiValidationError):
            validator.validate_required([], "field")
    
    def test_type_validation(self, validator):
        """Test type validation."""
        # Valid cases
        assert validator.validate_type("test", str, "field") == "test"
        assert validator.validate_type(123, int, "field") == 123
        assert validator.validate_type(123.45, float, "field") == 123.45
        
        # Invalid cases
        with pytest.raises(SyFiValidationError):
            validator.validate_type("123", int, "field")
        
        with pytest.raises(SyFiValidationError):
            validator.validate_type(123, str, "field")
    
    def test_range_validation(self, validator):
        """Test numeric range validation."""
        # Valid cases
        assert validator.validate_range(5, 1, 10, "field") == 5
        assert validator.validate_range(1, min_val=1, field_name="field") == 1
        assert validator.validate_range(10, max_val=10, field_name="field") == 10
        
        # Invalid cases
        with pytest.raises(SyFiValidationError):
            validator.validate_range(0, 1, 10, "field")
        
        with pytest.raises(SyFiValidationError):
            validator.validate_range(11, 1, 10, "field")
        
        with pytest.raises(SyFiValidationError):
            validator.validate_range("5", 1, 10, "field")
    
    def test_pattern_validation(self, validator):
        """Test regex pattern validation."""
        # Email pattern
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        # Valid cases
        assert validator.validate_pattern(
            "test@example.com", email_pattern, "email"
        ) == "test@example.com"
        
        # Invalid cases
        with pytest.raises(SyFiValidationError):
            validator.validate_pattern(
                "invalid-email", email_pattern, "email"
            )
        
        with pytest.raises(SyFiValidationError):
            validator.validate_pattern(
                123, email_pattern, "email"
            )
    
    def test_whitelist_validation(self, validator):
        """Test whitelist validation."""
        allowed_values = ['admin', 'user', 'guest']
        
        # Valid cases
        assert validator.validate_whitelist('admin', allowed_values, 'role') == 'admin'
        assert validator.validate_whitelist('user', allowed_values, 'role') == 'user'
        
        # Invalid cases
        with pytest.raises(SyFiValidationError):
            validator.validate_whitelist('superuser', allowed_values, 'role')
    
    def test_table_name_validation(self, validator):
        """Test database table name validation."""
        # Valid cases
        assert validator.validate_table_name('customers') == 'customers'
        assert validator.validate_table_name('ACCOUNTS') == 'accounts'
        
        # Invalid cases - not in whitelist
        with pytest.raises(SyFiSecurityError):
            validator.validate_table_name('malicious_table')
        
        # Invalid cases - SQL injection attempts
        with pytest.raises(SyFiSecurityError):
            validator.validate_table_name('customers; DROP TABLE users--')
    
    def test_file_path_validation(self, validator):
        """Test file path validation and sanitization."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Valid cases
            safe_path = os.path.join(temp_dir, "export.csv")
            result = validator.validate_file_path(safe_path, temp_dir)
            assert result == str(Path(safe_path).resolve())
            
            # Invalid cases - directory traversal
            with pytest.raises(SyFiSecurityError):
                validator.validate_file_path("../../../etc/passwd", temp_dir)
            
            # Invalid cases - outside base directory
            with pytest.raises(SyFiSecurityError):
                validator.validate_file_path("/tmp/outside.csv", temp_dir)
            
            # Invalid cases - bad extension
            with pytest.raises(SyFiSecurityError):
                validator.validate_file_path(
                    os.path.join(temp_dir, "malware.exe"), temp_dir
                )
    
    def test_business_rule_validation(self, business_validator):
        """Test business-specific validation rules."""
        # Valid customer data
        valid_customer = {
            'customer_id': 'C123',
            'name': 'John Doe',
            'email': 'john@example.com',
            'phone': '+1-555-123-4567',
            'age': 25
        }
        
        result = business_validator.validate_customer_data(valid_customer)
        assert result == valid_customer
        
        # Invalid customer data - missing required field
        with pytest.raises(SyFiValidationError):
            business_validator.validate_customer_data({
                'name': 'John Doe',
                'email': 'john@example.com'
            })
        
        # Invalid customer data - bad email format
        with pytest.raises(SyFiValidationError):
            business_validator.validate_customer_data({
                'customer_id': 'C123',
                'name': 'John Doe',
                'email': 'invalid-email'
            })
    
    def test_validation_decorator(self):
        """Test input validation decorator."""
        @validate_input(
            name={'type': str, 'required': True},
            age={'type': int, 'range': (18, 120)},
            email={'pattern': r'^[^@]+@[^@]+\.[^@]+$'}
        )
        def create_user(name, age=None, email=None):
            return {'name': name, 'age': age, 'email': email}
        
        # Valid case
        result = create_user("John", 25, "john@example.com")
        assert result['name'] == "John"
        assert result['age'] == 25
        
        # Invalid case - missing required
        with pytest.raises(SyFiValidationError):
            create_user(age=25)
        
        # Invalid case - bad range
        with pytest.raises(SyFiValidationError):
            create_user("John", 15)
    
    def test_output_sanitization(self):
        """Test output sanitization decorator."""
        @sanitize_output
        def get_user_data():
            return {
                'name': 'John Doe',
                'email': 'john@example.com',
                'password': 'secret123',
                'ssn': '123-45-6789'
            }
        
        result = get_user_data()
        assert result['name'] == 'John Doe'
        assert result['email'] == 'john@example.com'
        assert result['password'] == "***REDACTED***"
        assert result['ssn'] == "***REDACTED***"


class TestDatabaseResilience:
    """Test database resilience framework."""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix='.sqlite', delete=False) as f:
            db_path = f.name
        
        # Create basic schema
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE test_table (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                value INTEGER
            )
        ''')
        cursor.execute('''
            INSERT INTO test_table (name, value) VALUES ('test1', 100), ('test2', 200)
        ''')
        conn.commit()
        conn.close()
        
        yield db_path
        
        # Cleanup
        os.unlink(db_path)
    
    def test_circuit_breaker_states(self):
        """Test circuit breaker state transitions."""
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=1)
        
        # Initial state should be CLOSED
        assert cb.state == CircuitBreakerState.CLOSED
        
        def failing_function():
            raise sqlite3.Error("Database error")
        
        # First failure - should remain CLOSED
        with pytest.raises(SyFiDatabaseError):
            cb.call(failing_function)
        assert cb.state == CircuitBreakerState.CLOSED
        
        # Second failure - should open circuit
        with pytest.raises(SyFiDatabaseError):
            cb.call(failing_function)
        assert cb.state == CircuitBreakerState.OPEN
        
        # Should reject calls when OPEN
        with pytest.raises(SyFiDatabaseError):
            cb.call(failing_function)
        assert cb.state == CircuitBreakerState.OPEN
        
        # Wait for recovery timeout
        time.sleep(1.1)
        
        # Should try HALF_OPEN state
        def success_function():
            return "success"
        
        result = cb.call(success_function)
        assert result == "success"
        assert cb.state == CircuitBreakerState.CLOSED
    
    def test_connection_pool_basic_operations(self, temp_db):
        """Test basic connection pool operations."""
        pool = ConnectionPool(temp_db, pool_size=3)
        
        # Test getting connection
        with pool.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM test_table")
            result = cursor.fetchone()
            assert result[0] == 2
        
        # Test metrics
        metrics = pool.get_metrics()
        assert metrics.connection_count >= 0
        
        # Cleanup
        pool.close_all()
    
    def test_connection_pool_concurrent_access(self, temp_db):
        """Test connection pool under concurrent access."""
        pool = ConnectionPool(temp_db, pool_size=2)
        results = []
        exceptions = []
        
        def worker():
            try:
                with pool.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM test_table")
                    result = cursor.fetchone()[0]
                    results.append(result)
                    time.sleep(0.1)  # Simulate work
            except Exception as e:
                exceptions.append(e)
        
        # Start multiple threads
        threads = []
        for _ in range(5):
            t = threading.Thread(target=worker)
            threads.append(t)
            t.start()
        
        # Wait for completion
        for t in threads:
            t.join()
        
        # All threads should succeed
        assert len(exceptions) == 0
        assert len(results) == 5
        assert all(r == 2 for r in results)
        
        pool.close_all()
    
    def test_resilient_database_queries(self, temp_db):
        """Test ResilientDatabase query execution."""
        db = ResilientDatabase(temp_db)
        
        # Test SELECT query
        results = db.execute_query(
            "SELECT name, value FROM test_table ORDER BY id",
            fetch_mode='all'
        )
        assert len(results) == 2
        assert results[0]['name'] == 'test1'
        assert results[0]['value'] == 100
        
        # Test single row query
        result = db.execute_query(
            "SELECT name FROM test_table WHERE id = ?",
            params=(1,),
            fetch_mode='one'
        )
        assert result['name'] == 'test1'
        
        # Test transaction
        operations = [
            {'query': "INSERT INTO test_table (name, value) VALUES (?, ?)", 'params': ('test3', 300)},
            {'query': "UPDATE test_table SET value = ? WHERE name = ?", 'params': (150, 'test1')}
        ]
        
        success = db.execute_transaction(operations)
        assert success is True
        
        # Verify transaction results
        count = db.execute_query("SELECT COUNT(*) as count FROM test_table", fetch_mode='one')
        assert count['count'] == 3
        
        updated = db.execute_query("SELECT value FROM test_table WHERE name = 'test1'", fetch_mode='one')
        assert updated['value'] == 150
        
        db.close()
    
    def test_resilient_database_schema_methods(self, temp_db):
        """Test ResilientDatabase schema inspection methods."""
        db = ResilientDatabase(temp_db)
        
        # Test table existence
        assert db.table_exists('test_table') is True
        assert db.table_exists('nonexistent_table') is False
        
        # Test column existence
        assert db.column_exists('test_table', 'id') is True
        assert db.column_exists('test_table', 'name') is True
        assert db.column_exists('test_table', 'nonexistent_column') is False
        
        # Test table info
        table_info = db.get_table_info('test_table')
        assert len(table_info) == 3  # id, name, value columns
        column_names = [col['name'] for col in table_info]
        assert 'id' in column_names
        assert 'name' in column_names
        assert 'value' in column_names
        
        db.close()
    
    def test_resilient_database_metrics(self, temp_db):
        """Test ResilientDatabase metrics collection."""
        db = ResilientDatabase(temp_db, enable_metrics=True)
        
        # Execute some operations
        db.execute_query("SELECT COUNT(*) FROM test_table", fetch_mode='one')
        db.execute_query("SELECT * FROM test_table", fetch_mode='all')
        
        # Check metrics
        metrics = db.get_metrics()
        assert metrics['total_operations'] >= 2
        assert metrics['successful_operations'] >= 2
        assert metrics['failed_operations'] == 0
        assert metrics['success_rate'] > 0
        assert metrics['avg_response_time_ms'] > 0
        
        db.close()
    
    def test_resilient_database_health_check(self, temp_db):
        """Test ResilientDatabase health monitoring."""
        db = ResilientDatabase(temp_db)
        
        health_status = db.health_check()
        assert health_status['healthy'] is True
        assert 'checks' in health_status
        assert 'database_connectivity' in health_status['checks']
        assert 'circuit_breaker' in health_status['checks']
        assert 'connection_pool' in health_status['checks']
        
        # Database connectivity should be healthy
        assert health_status['checks']['database_connectivity']['status'] == 'healthy'
        
        # Circuit breaker should be closed
        assert health_status['checks']['circuit_breaker']['state'] == 'closed'
        
        db.close()


class TestSchemaAwareResilience:
    """Test integration of schema awareness with resilience framework."""
    
    @pytest.fixture
    def temp_db_with_schema(self):
        """Create temporary database with schema for testing."""
        with tempfile.NamedTemporaryFile(suffix='.sqlite', delete=False) as f:
            db_path = f.name
        
        # Create schema-aware test database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE customers (
                customer_id TEXT PRIMARY KEY,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                email TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE accounts (
                account_id TEXT PRIMARY KEY,
                customer_id TEXT NOT NULL,
                account_type TEXT,
                balance DECIMAL(12,2),
                status TEXT DEFAULT 'active'
            )
        ''')
        
        cursor.execute('''
            INSERT INTO customers VALUES ('C1', 'John', 'Doe', 'john@example.com')
        ''')
        cursor.execute('''
            INSERT INTO accounts VALUES ('A1', 'C1', 'checking', 1000.00, 'active')
        ''')
        
        conn.commit()
        conn.close()
        
        yield db_path
        
        os.unlink(db_path)
    
    def test_schema_aware_with_resilience(self, temp_db_with_schema):
        """Test SchemaAwareConnection with resilience enabled."""
        db = SchemaAwareConnection(temp_db_with_schema, enable_resilience=True)
        
        # Test that resilient database is initialized
        assert db._resilient_db is not None
        
        # Test schema-aware operations work with resilience
        assert db.table_exists('customers') is True
        assert db.table_exists('nonexistent_table') is False
        
        assert db.column_exists('accounts', 'status') is True
        assert db.column_exists('accounts', 'nonexistent_column') is False
        
        # Test safe_execute with resilience
        results = db.safe_execute("SELECT * FROM customers")
        assert len(results) == 1
        assert results[0]['first_name'] == 'John'
        
        # Test safe_count
        count = db.safe_count('customers')
        assert count == 1
        
        count = db.safe_count('nonexistent_table')
        assert count == 0
    
    def test_schema_aware_fallback_mode(self, temp_db_with_schema):
        """Test SchemaAwareConnection fallback when resilience unavailable."""
        # Mock the import to fail
        with patch('src.syfi.schema_management.schema_aware_db.ResilientDatabase', side_effect=ImportError):
            db = SchemaAwareConnection(temp_db_with_schema, enable_resilience=True)
            
            # Should fallback to basic connection
            assert db._resilient_db is None
            
            # Operations should still work
            assert db.table_exists('customers') is True
            results = db.safe_execute("SELECT * FROM customers")
            assert len(results) == 1
    
    def test_resilience_disabled(self, temp_db_with_schema):
        """Test SchemaAwareConnection with resilience explicitly disabled."""
        db = SchemaAwareConnection(temp_db_with_schema, enable_resilience=False)
        
        # Resilient database should not be initialized
        assert db._resilient_db is None
        
        # Operations should still work using basic connections
        assert db.table_exists('customers') is True
        results = db.safe_execute("SELECT * FROM customers")
        assert len(results) == 1


if __name__ == "__main__":
    # Run basic validation tests
    print("=== Production Hardening Phase 1 Tests ===")
    
    # Test exception hierarchy
    try:
        raise SyFiDatabaseError(
            "Test database error",
            query="SELECT * FROM test",
            database_path="/tmp/test.db"
        )
    except SyFiDatabaseError as e:
        print(f"✅ Exception hierarchy: {e.error_code}")
        print(f"✅ Context preservation: {e.context}")
    
    # Test input validation
    validator = InputValidator()
    try:
        validator.validate_table_name("customers")
        print("✅ Input validation: Table name validated")
    except Exception as e:
        print(f"❌ Input validation failed: {e}")
    
    # Test circuit breaker
    cb = CircuitBreaker(failure_threshold=1)
    try:
        def test_func():
            return "success"
        result = cb.call(test_func)
        print(f"✅ Circuit breaker: {result}")
    except Exception as e:
        print(f"❌ Circuit breaker failed: {e}")
    
    print("=== Phase 1 Production Hardening Tests Complete ===")