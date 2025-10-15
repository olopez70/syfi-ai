"""
Database Resilience Framework for SyFi AI

Provides robust database operations with retry logic, circuit breakers,
connection pooling, and comprehensive error handling.
"""
import sqlite3
import logging
import time
import threading
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable, Union
from contextlib import contextmanager
from pathlib import Path
from queue import Queue, Empty
from enum import Enum

from ..exceptions import SyFiDatabaseError, SyFiPerformanceError, with_database_retry


class CircuitBreakerState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class DatabaseMetrics:
    """Database operation metrics."""
    total_operations: int = 0
    successful_operations: int = 0
    failed_operations: int = 0
    avg_response_time_ms: float = 0.0
    peak_response_time_ms: float = 0.0
    connection_count: int = 0
    circuit_breaker_trips: int = 0
    last_operation_time: Optional[datetime] = None


class CircuitBreaker:
    """
    Circuit breaker pattern implementation for database operations.
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = Exception
    ):
        """
        Initialize circuit breaker.
        
        Args:
            failure_threshold: Number of failures to trigger open state
            recovery_timeout: Seconds before attempting recovery
            expected_exception: Exception type that triggers circuit breaker
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self._failure_count = 0
        self._last_failure_time = None
        self._state = CircuitBreakerState.CLOSED
        self._lock = threading.Lock()
        
        self.logger = logging.getLogger(__name__)
    
    @property
    def state(self) -> CircuitBreakerState:
        """Current circuit breaker state."""
        return self._state
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection.
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            SyFiDatabaseError: If circuit is open or function fails
        """
        with self._lock:
            if self._state == CircuitBreakerState.OPEN:
                if self._should_attempt_reset():
                    self._state = CircuitBreakerState.HALF_OPEN
                    self.logger.info("Circuit breaker moving to HALF_OPEN state")
                else:
                    raise SyFiDatabaseError(
                        "Circuit breaker is OPEN - rejecting database operation"
                    )
            
            try:
                start_time = time.time()
                result = func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                
                # Operation succeeded
                self._on_success()
                
                self.logger.debug(
                    "Database operation succeeded",
                    extra={
                        'operation': func.__name__,
                        'duration_ms': duration_ms,
                        'circuit_state': self._state.value
                    }
                )
                
                return result
                
            except self.expected_exception as e:
                self._on_failure()
                
                self.logger.warning(
                    "Database operation failed",
                    extra={
                        'operation': func.__name__,
                        'error': str(e),
                        'failure_count': self._failure_count,
                        'circuit_state': self._state.value
                    }
                )
                
                raise SyFiDatabaseError(
                    f"Database operation failed: {func.__name__}",
                    original_exception=e
                )
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        return (
            self._last_failure_time is not None and
            time.time() - self._last_failure_time >= self.recovery_timeout
        )
    
    def _on_success(self):
        """Handle successful operation."""
        self._failure_count = 0
        if self._state == CircuitBreakerState.HALF_OPEN:
            self._state = CircuitBreakerState.CLOSED
            self.logger.info("Circuit breaker reset to CLOSED state")
    
    def _on_failure(self):
        """Handle failed operation."""
        self._failure_count += 1
        self._last_failure_time = time.time()
        
        if self._failure_count >= self.failure_threshold:
            self._state = CircuitBreakerState.OPEN
            self.logger.warning(
                f"Circuit breaker OPENED after {self._failure_count} failures"
            )


class ConnectionPool:
    """
    Database connection pool with automatic cleanup and monitoring.
    """
    
    def __init__(
        self,
        database_path: str,
        pool_size: int = 10,
        max_age_seconds: int = 300,
        timeout_seconds: int = 30
    ):
        """
        Initialize connection pool.
        
        Args:
            database_path: Path to SQLite database
            pool_size: Maximum number of connections
            max_age_seconds: Maximum age before connection refresh
            timeout_seconds: Timeout for getting connections
        """
        self.database_path = database_path
        self.pool_size = pool_size
        self.max_age_seconds = max_age_seconds
        self.timeout_seconds = timeout_seconds
        
        self._pool = Queue(maxsize=pool_size)
        self._active_connections = {}
        self._lock = threading.Lock()
        self._metrics = DatabaseMetrics()
        
        self.logger = logging.getLogger(__name__)
        
        # Pre-populate pool
        self._initialize_pool()
    
    def _initialize_pool(self):
        """Create initial connections."""
        for _ in range(self.pool_size):
            try:
                conn = self._create_connection()
                self._pool.put(conn, block=False)
            except Exception as e:
                self.logger.warning(
                    f"Failed to create initial connection: {e}"
                )
    
    def _create_connection(self) -> sqlite3.Connection:
        """Create a new database connection with optimized settings."""
        try:
            conn = sqlite3.connect(
                self.database_path,
                timeout=self.timeout_seconds,
                check_same_thread=False
            )
            
            # Optimize SQLite settings
            conn.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging
            conn.execute("PRAGMA synchronous=NORMAL")  # Balance safety/performance
            conn.execute("PRAGMA cache_size=10000")  # 10MB cache
            conn.execute("PRAGMA temp_store=MEMORY")  # Use memory for temp tables
            conn.execute("PRAGMA mmap_size=268435456")  # 256MB memory map
            
            # Enable foreign keys
            conn.execute("PRAGMA foreign_keys=ON")
            
            # Set row factory for dict-like access
            conn.row_factory = sqlite3.Row
            
            # Tag connection with creation time
            conn._created_at = time.time()
            
            return conn
            
        except sqlite3.Error as e:
            raise SyFiDatabaseError(
                f"Failed to create database connection to {self.database_path}",
                database_path=self.database_path,
                original_exception=e
            )
    
    @contextmanager
    def get_connection(self):
        """
        Get a connection from the pool with automatic cleanup.
        
        Yields:
            sqlite3.Connection: Database connection
            
        Raises:
            SyFiDatabaseError: If unable to get connection
        """
        conn = None
        start_time = time.time()
        
        try:
            # Try to get existing connection
            try:
                conn = self._pool.get(timeout=self.timeout_seconds)
                
                # Check if connection is still valid and not too old
                if (time.time() - conn._created_at) > self.max_age_seconds:
                    conn.close()
                    conn = self._create_connection()
                
            except Empty:
                # Pool exhausted, create new connection
                conn = self._create_connection()
            
            # Track active connection
            connection_id = id(conn)
            with self._lock:
                self._active_connections[connection_id] = {
                    'connection': conn,
                    'acquired_at': time.time(),
                    'thread_id': threading.current_thread().ident
                }
                self._metrics.connection_count += 1
            
            duration_ms = (time.time() - start_time) * 1000
            self.logger.debug(
                "Connection acquired from pool",
                extra={
                    'connection_id': connection_id,
                    'acquisition_time_ms': duration_ms,
                    'active_connections': len(self._active_connections)
                }
            )
            
            yield conn
            
        except Exception as e:
            if conn:
                try:
                    conn.rollback()
                except:
                    pass
            raise
            
        finally:
            # Return connection to pool or close if pool full
            if conn:
                connection_id = id(conn)
                
                with self._lock:
                    if connection_id in self._active_connections:
                        del self._active_connections[connection_id]
                
                try:
                    self._pool.put_nowait(conn)
                except:
                    # Pool is full, close the connection
                    conn.close()
    
    def get_metrics(self) -> DatabaseMetrics:
        """Get current pool metrics."""
        with self._lock:
            self._metrics.connection_count = len(self._active_connections)
        return self._metrics
    
    def close_all(self):
        """Close all connections in the pool."""
        with self._lock:
            # Close active connections
            for conn_info in self._active_connections.values():
                try:
                    conn_info['connection'].close()
                except:
                    pass
            self._active_connections.clear()
            
            # Close pooled connections
            while not self._pool.empty():
                try:
                    conn = self._pool.get_nowait()
                    conn.close()
                except:
                    pass


class ResilientDatabase:
    """
    High-level database interface with comprehensive resilience patterns.
    """
    
    def __init__(
        self,
        database_path: str,
        pool_size: int = 10,
        circuit_breaker_threshold: int = 5,
        enable_metrics: bool = True
    ):
        """
        Initialize resilient database interface.
        
        Args:
            database_path: Path to SQLite database
            pool_size: Connection pool size
            circuit_breaker_threshold: Failures before circuit opens
            enable_metrics: Whether to collect detailed metrics
        """
        self.database_path = database_path
        self.enable_metrics = enable_metrics
        
        # Ensure database directory exists
        Path(database_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.pool = ConnectionPool(database_path, pool_size)
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=circuit_breaker_threshold,
            expected_exception=(sqlite3.Error, SyFiDatabaseError)
        )
        
        self.logger = logging.getLogger(__name__)
        self._metrics = DatabaseMetrics()
    
    @with_database_retry(max_retries=3)
    def execute_query(
        self,
        query: str,
        params: tuple = None,
        fetch_mode: str = 'all'
    ) -> Union[List[sqlite3.Row], sqlite3.Row, None]:
        """
        Execute SELECT query with full resilience patterns.
        
        Args:
            query: SQL SELECT statement
            params: Query parameters
            fetch_mode: 'all', 'one', or 'none'
            
        Returns:
            Query results based on fetch_mode
            
        Raises:
            SyFiDatabaseError: If query fails after retries
        """
        def _execute():
            start_time = time.time()
            
            with self.pool.get_connection() as conn:
                cursor = conn.cursor()
                
                self.logger.debug(
                    "Executing query",
                    extra={
                        'query': query[:100] + '...' if len(query) > 100 else query,
                        'params': str(params) if params else None,
                        'fetch_mode': fetch_mode
                    }
                )
                
                cursor.execute(query, params or ())
                
                # Fetch results based on mode
                if fetch_mode == 'all':
                    result = cursor.fetchall()
                elif fetch_mode == 'one':
                    result = cursor.fetchone()
                else:  # 'none'
                    result = None
                
                # Update metrics
                if self.enable_metrics:
                    duration_ms = (time.time() - start_time) * 1000
                    self._update_metrics(success=True, duration_ms=duration_ms)
                
                return result
        
        return self.circuit_breaker.call(_execute)
    
    @with_database_retry(max_retries=3)
    def execute_transaction(
        self,
        operations: List[Dict[str, Any]]
    ) -> bool:
        """
        Execute multiple operations as a single transaction.
        
        Args:
            operations: List of dicts with 'query' and optional 'params'
            
        Returns:
            True if transaction succeeded
            
        Raises:
            SyFiDatabaseError: If transaction fails after retries
        """
        def _execute():
            start_time = time.time()
            
            with self.pool.get_connection() as conn:
                try:
                    cursor = conn.cursor()
                    
                    # Begin transaction
                    cursor.execute("BEGIN")
                    
                    self.logger.debug(
                        f"Executing transaction with {len(operations)} operations"
                    )
                    
                    # Execute all operations
                    for op in operations:
                        query = op['query']
                        params = op.get('params')
                        
                        cursor.execute(query, params or ())
                    
                    # Commit transaction
                    conn.commit()
                    
                    # Update metrics
                    if self.enable_metrics:
                        duration_ms = (time.time() - start_time) * 1000
                        self._update_metrics(success=True, duration_ms=duration_ms)
                    
                    self.logger.info(
                        f"Transaction completed successfully with {len(operations)} operations"
                    )
                    
                    return True
                    
                except Exception as e:
                    conn.rollback()
                    self.logger.error(
                        f"Transaction failed, rolled back: {e}"
                    )
                    raise
        
        return self.circuit_breaker.call(_execute)
    
    def table_exists(self, table_name: str) -> bool:
        """
        Check if a table exists in the database.
        
        Args:
            table_name: Name of the table
            
        Returns:
            True if table exists
        """
        query = """
        SELECT COUNT(*) as count 
        FROM sqlite_master 
        WHERE type='table' AND name=?
        """
        
        result = self.execute_query(query, (table_name,), fetch_mode='one')
        return result['count'] > 0 if result else False
    
    def column_exists(self, table_name: str, column_name: str) -> bool:
        """
        Check if a column exists in a table.
        
        Args:
            table_name: Name of the table
            column_name: Name of the column
            
        Returns:
            True if column exists
        """
        if not self.table_exists(table_name):
            return False
        
        query = f"PRAGMA table_info({table_name})"
        columns = self.execute_query(query)
        
        if columns:
            column_names = [col['name'].lower() for col in columns]
            return column_name.lower() in column_names
        
        return False
    
    def get_table_info(self, table_name: str) -> List[Dict[str, Any]]:
        """
        Get detailed information about a table structure.
        
        Args:
            table_name: Name of the table
            
        Returns:
            List of column information dictionaries
        """
        if not self.table_exists(table_name):
            raise SyFiDatabaseError(f"Table '{table_name}' does not exist")
        
        query = f"PRAGMA table_info({table_name})"
        columns = self.execute_query(query)
        
        return [dict(col) for col in columns] if columns else []
    
    def _update_metrics(self, success: bool, duration_ms: float):
        """Update operation metrics."""
        self._metrics.total_operations += 1
        self._metrics.last_operation_time = datetime.now()
        
        if success:
            self._metrics.successful_operations += 1
        else:
            self._metrics.failed_operations += 1
        
        # Update response time metrics
        if self._metrics.total_operations == 1:
            self._metrics.avg_response_time_ms = duration_ms
        else:
            # Running average
            current_avg = self._metrics.avg_response_time_ms
            self._metrics.avg_response_time_ms = (
                (current_avg * (self._metrics.total_operations - 1) + duration_ms) /
                self._metrics.total_operations
            )
        
        if duration_ms > self._metrics.peak_response_time_ms:
            self._metrics.peak_response_time_ms = duration_ms
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get comprehensive database metrics.
        
        Returns:
            Dictionary containing all metrics
        """
        pool_metrics = self.pool.get_metrics()
        
        return {
            'database_path': self.database_path,
            'total_operations': self._metrics.total_operations,
            'successful_operations': self._metrics.successful_operations,
            'failed_operations': self._metrics.failed_operations,
            'success_rate': (
                self._metrics.successful_operations / self._metrics.total_operations
                if self._metrics.total_operations > 0 else 0
            ),
            'avg_response_time_ms': self._metrics.avg_response_time_ms,
            'peak_response_time_ms': self._metrics.peak_response_time_ms,
            'active_connections': pool_metrics.connection_count,
            'circuit_breaker_state': self.circuit_breaker.state.value,
            'circuit_breaker_trips': self._metrics.circuit_breaker_trips,
            'last_operation': (
                self._metrics.last_operation_time.isoformat()
                if self._metrics.last_operation_time else None
            )
        }
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform comprehensive health check.
        
        Returns:
            Health status dictionary
        """
        health_status = {
            'healthy': True,
            'checks': {},
            'timestamp': datetime.now().isoformat()
        }
        
        # Database connectivity check
        try:
            result = self.execute_query("SELECT 1 as test", fetch_mode='one')
            health_status['checks']['database_connectivity'] = {
                'status': 'healthy',
                'response': result['test'] if result else None
            }
        except Exception as e:
            health_status['healthy'] = False
            health_status['checks']['database_connectivity'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
        
        # Circuit breaker status
        cb_state = self.circuit_breaker.state
        health_status['checks']['circuit_breaker'] = {
            'status': 'healthy' if cb_state == CircuitBreakerState.CLOSED else 'degraded',
            'state': cb_state.value
        }
        
        if cb_state == CircuitBreakerState.OPEN:
            health_status['healthy'] = False
        
        # Connection pool status
        pool_metrics = self.pool.get_metrics()
        health_status['checks']['connection_pool'] = {
            'status': 'healthy',
            'active_connections': pool_metrics.connection_count,
            'pool_size': self.pool.pool_size
        }
        
        # Performance metrics
        if self._metrics.total_operations > 0:
            health_status['checks']['performance'] = {
                'status': (
                    'healthy' if self._metrics.avg_response_time_ms < 1000
                    else 'degraded'
                ),
                'avg_response_time_ms': self._metrics.avg_response_time_ms,
                'success_rate': (
                    self._metrics.successful_operations / self._metrics.total_operations
                )
            }
            
            if self._metrics.avg_response_time_ms > 5000:  # 5 second threshold
                health_status['healthy'] = False
        
        return health_status
    
    def close(self):
        """Close all database connections and cleanup resources."""
        self.logger.info("Closing resilient database interface")
        self.pool.close_all()