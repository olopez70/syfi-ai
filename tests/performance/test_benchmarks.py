"""
Performance benchmarks for SyFi AI operations.

Tests performance characteristics of bulk operations and data generation.
"""

import pytest
import time
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from src.syfi.generators import CustomerGenerator
from src.syfi.database import DatabaseManager


@pytest.mark.performance
@pytest.mark.slow
class TestGenerationPerformance:
    """Benchmark data generation performance."""
    
    def test_single_customer_generation_speed(self):
        """Benchmark single customer generation time."""
        generator = CustomerGenerator(seed=12345)
        
        start_time = time.perf_counter()
        customers, accounts = generator.generate_customers(1, accounts_per_customer=1)
        end_time = time.perf_counter()
        
        duration_ms = (end_time - start_time) * 1000
        
        # Should generate single customer in under 100ms
        assert duration_ms < 100, f"Single customer generation took {duration_ms:.2f}ms"
        assert len(customers) == 1
        assert len(accounts) >= 1
    
    def test_bulk_customer_generation_speed(self):
        """Benchmark bulk customer generation performance."""
        generator = CustomerGenerator(seed=12345)
        
        # Test various batch sizes
        batch_sizes = [10, 100, 500]
        
        for batch_size in batch_sizes:
            start_time = time.perf_counter()
            customers, accounts = generator.generate_customers(batch_size, accounts_per_customer=2)
            end_time = time.perf_counter()
            
            duration = end_time - start_time
            customers_per_second = batch_size / duration
            
            print(f"Generated {batch_size} customers in {duration:.2f}s ({customers_per_second:.1f} customers/sec)")
            
            # Should generate at least 10 customers per second
            assert customers_per_second > 10, f"Generation rate too slow: {customers_per_second:.1f} customers/sec"
            assert len(customers) == batch_size
            assert len(accounts) >= batch_size  # At least one account per customer
    
    @pytest.mark.benchmark
    def test_customer_generation_benchmark(self, benchmark):
        """Benchmark customer generation using pytest-benchmark.""" 
        generator = CustomerGenerator(seed=12345)
        
        # Benchmark function
        def generate_customers():
            return generator.generate_customers(50, accounts_per_customer=2)
        
        result = benchmark(generate_customers)
        customers, accounts = result
        
        assert len(customers) == 50
        assert len(accounts) >= 50  # At least one account per customer


@pytest.mark.performance
@pytest.mark.slow  
class TestDatabasePerformance:
    """Benchmark database operation performance."""
    
    def test_database_insertion_speed(self, temp_db):
        """Benchmark database insertion performance."""
        db_manager = DatabaseManager(temp_db)
        db_manager.initialize_schema()
        
        generator = CustomerGenerator(seed=12345)
        customers, accounts = generator.generate_customers(100, accounts_per_customer=2)
        
        # Benchmark customer insertion
        start_time = time.perf_counter()
        db_manager.insert_customers(customers)
        end_time = time.perf_counter()
        
        customer_insert_duration = end_time - start_time
        customers_per_second = len(customers) / customer_insert_duration
        
        print(f"Inserted {len(customers)} customers in {customer_insert_duration:.2f}s ({customers_per_second:.1f} customers/sec)")
        
        # Should insert at least 50 customers per second
        assert customers_per_second > 50, f"Customer insertion too slow: {customers_per_second:.1f} customers/sec"
        
        # Benchmark account insertion
        start_time = time.perf_counter()
        db_manager.insert_accounts(accounts)
        end_time = time.perf_counter()
        
        account_insert_duration = end_time - start_time
        accounts_per_second = len(accounts) / account_insert_duration
        
        print(f"Inserted {len(accounts)} accounts in {account_insert_duration:.2f}s ({accounts_per_second:.1f} accounts/sec)")
        
        # Should insert at least 100 accounts per second
        assert accounts_per_second > 100, f"Account insertion too slow: {accounts_per_second:.1f} accounts/sec"
    
    def test_database_query_performance(self, populated_database):
        """Benchmark database query performance."""
        db = populated_database
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Benchmark simple query
        start_time = time.perf_counter()
        for _ in range(100):  # Run query 100 times
            cursor.execute("SELECT * FROM customers LIMIT 10")
            cursor.fetchall()
        end_time = time.perf_counter()
        
        query_duration = end_time - start_time
        queries_per_second = 100 / query_duration
        
        print(f"Executed 100 simple queries in {query_duration:.2f}s ({queries_per_second:.1f} queries/sec)")
        
        # Should execute at least 500 simple queries per second
        assert queries_per_second > 500, f"Query performance too slow: {queries_per_second:.1f} queries/sec"
        
        # Benchmark complex join query
        complex_query = """
            SELECT c.customer_id, c.first_name, c.last_name, 
                   COUNT(a.account_id) as account_count,
                   AVG(a.balance) as avg_balance
            FROM customers c
            LEFT JOIN accounts a ON c.customer_id = a.customer_id  
            GROUP BY c.customer_id
        """
        
        start_time = time.perf_counter()
        for _ in range(10):  # Run complex query 10 times
            cursor.execute(complex_query)
            cursor.fetchall()
        end_time = time.perf_counter()
        
        complex_query_duration = end_time - start_time
        complex_queries_per_second = 10 / complex_query_duration
        
        print(f"Executed 10 complex queries in {complex_query_duration:.2f}s ({complex_queries_per_second:.1f} queries/sec)")
        
        # Should execute at least 20 complex queries per second
        assert complex_queries_per_second > 20, f"Complex query performance too slow: {complex_queries_per_second:.1f} queries/sec"


@pytest.mark.performance
class TestMemoryUsage:
    """Monitor memory usage during operations."""
    
    def test_large_dataset_memory_usage(self, temp_db):
        """Monitor memory usage during large dataset generation."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        
        # Measure initial memory
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Generate large dataset
        generator = CustomerGenerator(seed=12345)
        customers, accounts = generator.generate_customers(1000, accounts_per_customer=3)
        
        # Measure memory after generation
        post_generation_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = post_generation_memory - initial_memory
        
        print(f"Memory usage: {initial_memory:.1f}MB → {post_generation_memory:.1f}MB (+{memory_increase:.1f}MB)")
        
        # Memory increase should be reasonable (adjust threshold as needed)
        assert memory_increase < 100, f"Memory usage increase too high: {memory_increase:.1f}MB"
        
        # Insert into database
        db_manager = DatabaseManager(temp_db)
        db_manager.initialize_schema()
        
        db_manager.insert_customers(customers)
        db_manager.insert_accounts(accounts)
        
        # Measure final memory
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        total_increase = final_memory - initial_memory
        
        print(f"Final memory usage: {final_memory:.1f}MB (+{total_increase:.1f}MB total)")
        
        # Total memory increase should still be reasonable
        assert total_increase < 150, f"Total memory usage increase too high: {total_increase:.1f}MB"