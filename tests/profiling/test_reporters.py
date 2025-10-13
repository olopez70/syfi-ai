"""
Tests for Profile Reporter.

This module tests the multi-format report generation capabilities
that handle HTML, JSON, and Markdown output for banking data profiles.
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
from datetime import datetime, date

from src.syfi.profiling.reporters import ProfileReporter
from src.syfi.profiling.analyzer import ProfileSummary, TableProfile


@pytest.mark.unit
class TestProfileReporter:
    """Test ProfileReporter class."""
    
    @pytest.fixture
    def sample_profile_data(self):
        """Create sample profile data for testing."""
        summary = ProfileSummary(
            database_path="/test/banking.sqlite",
            analysis_date=datetime(2023, 1, 15, 10, 30, 0),
            total_customers=100,
            total_accounts=250,
            total_transactions=1500,
            database_size_kb=512.75,
            unique_profiles=5,
            date_range=(date(2023, 1, 1), date(2023, 12, 31))
        )
        
        table_profiles = {
            "customers": TableProfile(
                table_name="customers",
                row_count=100,
                column_count=8,
                columns=[
                    {"name": "customer_id", "type": "TEXT"},
                    {"name": "first_name", "type": "TEXT"},
                    {"name": "last_name", "type": "TEXT"},
                    {"name": "age", "type": "INTEGER"}
                ],
                data_types={"customer_id": "TEXT", "first_name": "TEXT", "last_name": "TEXT", "age": "INTEGER"},
                null_counts={"customer_id": 0, "first_name": 0, "last_name": 1, "age": 3},
                unique_counts={"customer_id": 100, "first_name": 75, "last_name": 80, "age": 45},
                sample_values={
                    "customer_id": ["cust_001", "cust_002", "cust_003"],
                    "first_name": ["John", "Jane", "Alice"],
                    "last_name": ["Doe", "Smith", "Johnson"],
                    "age": [25, 30, 35]
                }
            ),
            "accounts": TableProfile(
                table_name="accounts",
                row_count=250,
                column_count=6,
                columns=[
                    {"name": "account_id", "type": "TEXT"},
                    {"name": "customer_id", "type": "TEXT"},
                    {"name": "account_type", "type": "TEXT"},
                    {"name": "balance", "type": "DECIMAL"}
                ],
                data_types={"account_id": "TEXT", "customer_id": "TEXT", "account_type": "TEXT", "balance": "DECIMAL"},
                null_counts={"account_id": 0, "customer_id": 0, "account_type": 0, "balance": 0},
                unique_counts={"account_id": 250, "customer_id": 100, "account_type": 3, "balance": 200},
                sample_values={
                    "account_id": ["acc_001", "acc_002", "acc_003"],
                    "customer_id": ["cust_001", "cust_001", "cust_002"],
                    "account_type": ["checking", "savings", "checking"],
                    "balance": [2500.00, 15000.00, 3200.00]
                }
            )
        }
        
        banking_metrics = {
            "account_stats": {
                "checking": {"count": 150, "total_balance": 375000.00, "avg_balance": 2500.00},
                "savings": {"count": 80, "total_balance": 1200000.00, "avg_balance": 15000.00},
                "credit": {"count": 20, "total_balance": -50000.00, "avg_balance": -2500.00}
            },
            "transaction_stats": {
                "debit": {"count": 800, "total_amount": -400000.00, "avg_amount": -500.00},
                "credit": {"count": 700, "total_amount": 350000.00, "avg_amount": 500.00}
            },
            "customer_segments": {
                "high_value": {"count": 20, "total_balance": 600000.00, "avg_balance": 30000.00},
                "medium_value": {"count": 50, "total_balance": 750000.00, "avg_balance": 15000.00},
                "low_value": {"count": 30, "total_balance": 225000.00, "avg_balance": 7500.00}
            },
            "balance_distribution": {
                "negative": 20,
                "0_1000": 40,
                "1000_5000": 60,
                "5000_10000": 80,
                "10000_plus": 50
            }
        }
        
        return {
            "summary": summary,
            "tables": table_profiles,
            "banking_metrics": banking_metrics
        }
    
    @pytest.fixture
    def reporter(self):
        """Create a ProfileReporter instance."""
        import tempfile
        temp_dir = tempfile.mkdtemp()
        return ProfileReporter(Path(temp_dir))
    
    def test_reporter_initialization(self, reporter):
        """Test ProfileReporter initialization."""
        assert hasattr(reporter, 'generate_report')
        assert hasattr(reporter, '_generate_html_report')
        assert hasattr(reporter, '_generate_json_report')
        assert hasattr(reporter, '_generate_markdown_report')
    
    def test_generate_report_html_format(self, reporter, sample_profile_data):
        """Test report generation in HTML format."""
        output_path = reporter.generate_report(sample_profile_data, format="html", filename="test_report")
        
        assert output_path.exists()
        assert output_path.suffix == ".html"
        
        # Read and verify HTML content
        content = output_path.read_text()
        assert "<!DOCTYPE html>" in content
        assert "<html" in content
        assert "banking.sqlite" in content
        assert "100" in content  # total customers
        assert "250" in content  # total accounts
    
    def test_generate_report_json_format(self, reporter, sample_profile_data):
        """Test report generation in JSON format."""
        output_path = reporter.generate_report(sample_profile_data, format="json", filename="test_report")
        
        assert output_path.exists()
        assert output_path.suffix == ".json"
        
        # Read and verify JSON content
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        assert "summary" in data
        assert "tables" in data
        assert "banking_metrics" in data
        
        # Verify summary data
        summary = data["summary"]
        assert summary["total_customers"] == 100
        assert summary["total_accounts"] == 250
        assert summary["database_path"] == "/test/banking.sqlite"
        
        # Verify tables data
        assert "customers" in data["tables"]
        assert "accounts" in data["tables"]
        assert data["tables"]["customers"]["row_count"] == 100
        assert data["tables"]["accounts"]["row_count"] == 250
    
    def test_generate_report_markdown_format(self, reporter, sample_profile_data):
        """Test report generation in Markdown format."""
        output_path = reporter.generate_report(sample_profile_data, format="markdown", filename="test_report")
        
        assert output_path.exists()
        assert output_path.suffix == ".md"
        
        # Read and verify Markdown content
        content = output_path.read_text()
        assert "banking.sqlite" in content
        assert "100" in content  # total customers
        assert "250" in content  # total accounts
    
    def test_generate_report_invalid_format(self, reporter, sample_profile_data):
        """Test report generation with invalid format."""
        with pytest.raises(ValueError, match="Unsupported format"):
            reporter.generate_report(sample_profile_data, format="xml", filename="test_report")
    
    def test_html_report_structure(self, reporter, sample_profile_data):
        """Test HTML report structure and content."""
        output_path = reporter.generate_report(sample_profile_data, format="html", filename="structure_test")
        
        assert output_path.exists()
        
        # Read the written content
        written_content = output_path.read_text()
        
        # Verify HTML structure basics
        assert "<!DOCTYPE html>" in written_content
        assert "<html" in written_content
        assert "<head>" in written_content
        assert "<body>" in written_content
        
        # Verify specific data
        assert "banking.sqlite" in written_content
        assert "100" in written_content  # customers
        assert "250" in written_content  # accounts
    
    def test_json_report_structure(self, reporter, sample_profile_data):
        """Test JSON report structure and serialization."""
        output_path = reporter.generate_report(sample_profile_data, format="json", filename="structure_test")
        
        assert output_path.exists()
        
        # Read and parse JSON content
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        # Verify JSON structure
        assert "summary" in data
        assert "tables" in data
        assert "banking_metrics" in data
        
        # Verify data integrity
        assert data["summary"]["total_customers"] == 100
        assert data["summary"]["total_accounts"] == 250
        assert len(data["tables"]) == 2
        assert "customers" in data["tables"]
        assert "accounts" in data["tables"]
    
    def test_markdown_report_structure(self, reporter, sample_profile_data):
        """Test Markdown report structure and formatting."""
        output_path = reporter.generate_report(sample_profile_data, format="markdown", filename="structure_test")
        
        assert output_path.exists()
        
        # Read the written content
        written_content = output_path.read_text()
        
        # Verify content exists and contains expected data
        assert "banking.sqlite" in written_content
        assert "100" in written_content  # customers
        assert "250" in written_content  # accounts
    
    def test_html_escape_security(self, reporter, sample_profile_data):
        """Test HTML escaping for security."""
        # Modify sample data to include potentially dangerous content
        sample_profile_data["summary"].database_path = "/test/<script>alert('xss')</script>.sqlite"
        
        output_path = reporter.generate_report(sample_profile_data, format="html", filename="security_test")
        
        content = output_path.read_text()
        
        # Verify dangerous content is escaped
        assert "<script>" not in content
        assert "&lt;script&gt;" in content or "alert('xss')" not in content
    
    def test_report_with_minimal_data(self, reporter):
        """Test report generation with minimal data."""
        minimal_data = {
            "summary": ProfileSummary(
                database_path="/test/minimal.sqlite",
                analysis_date=datetime.now(),
                total_customers=0,
                total_accounts=0,
                total_transactions=0,
                database_size_kb=0.0,
                unique_profiles=0,
                date_range=None
            ),
            "tables": {},
            "banking_metrics": {
                "account_stats": {},
                "transaction_stats": {},
                "customer_segments": {},
                "balance_distribution": {}
            }
        }
        
        # Test all formats with minimal data
        for format_type in ["html", "json", "markdown"]:
            # Should not raise an exception
            output_path = reporter.generate_report(minimal_data, format=format_type, filename=f"minimal_report_{format_type}")
            assert output_path.exists()
            
            # Verify content is not empty
            content = output_path.read_text()
            assert len(content) > 0
            assert "minimal.sqlite" in content
    
    def test_report_with_special_characters(self, reporter, sample_profile_data):
        """Test report generation with special characters in data."""
        # Add special characters to test data
        sample_profile_data["tables"]["customers"].sample_values["first_name"] = [
            "José", "François", "北京", "测试用户"
        ]
        
        for format_type in ["html", "json", "markdown"]:
            # Should handle special characters properly
            output_path = reporter.generate_report(sample_profile_data, format=format_type, filename=f"special_chars_{format_type}")
            assert output_path.exists()
            
            # Read content and verify special characters are preserved
            if format_type == "json":
                with open(output_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                # Special characters should be preserved in JSON
                first_names = data["tables"]["customers"]["sample_values"]["first_name"]
                assert "José" in first_names
            else:
                content = output_path.read_text(encoding='utf-8')
                assert "José" in content or "François" in content
    
    def test_timestamp_generation(self, reporter, sample_profile_data):
        """Test that reports are generated without errors."""
        before_time = datetime.now()
        output_path = reporter.generate_report(sample_profile_data, format="json", filename="timestamped_report")
        after_time = datetime.now()
        
        assert output_path.exists()
        
        # Check that file was created within expected time range
        file_mtime = datetime.fromtimestamp(output_path.stat().st_mtime)
        assert before_time <= file_mtime <= after_time


@pytest.mark.integration
class TestProfileReporterIntegration:
    """Integration tests for ProfileReporter with complex data."""
    
    def test_large_dataset_reporting(self):
        """Test reporting with larger datasets."""
        # Create large dataset
        large_table_profile = TableProfile(
            table_name="large_transactions",
            row_count=100000,
            column_count=15,
            columns=[{"name": f"col_{i}", "type": "TEXT"} for i in range(15)],
            data_types={f"col_{i}": "TEXT" for i in range(15)},
            null_counts={f"col_{i}": i * 100 for i in range(15)},
            unique_counts={f"col_{i}": 100000 - (i * 1000) for i in range(15)},
            sample_values={f"col_{i}": [f"value_{i}_{j}" for j in range(5)] for i in range(15)}
        )
        
        large_data = {
            "summary": ProfileSummary(
                database_path="/test/large_banking.sqlite",
                analysis_date=datetime.now(),
                total_customers=10000,
                total_accounts=25000,
                total_transactions=100000,
                database_size_kb=10240.0,
                unique_profiles=10,
                date_range=(date(2020, 1, 1), date(2023, 12, 31))
            ),
            "tables": {"large_transactions": large_table_profile},
            "banking_metrics": {
                "account_stats": {f"type_{i}": {"count": 1000, "total_balance": i * 100000} for i in range(10)},
                "transaction_stats": {},
                "customer_segments": {},
                "balance_distribution": {}
            }
        }
        
        import tempfile
        temp_dir = tempfile.mkdtemp()
        reporter = ProfileReporter(Path(temp_dir))
        
        # Test that large datasets don't cause memory issues
        for format_type in ["html", "json", "markdown"]:
            # Should complete without memory errors
            output_path = reporter.generate_report(large_data, format=format_type, filename=f"large_report_{format_type}")
            assert output_path.exists()
            
            # File should not be empty
            assert output_path.stat().st_size > 0
    
    def test_concurrent_report_generation(self):
        """Test concurrent report generation."""
        import threading
        import queue
        
        import tempfile
        temp_dir = tempfile.mkdtemp()
        reporter = ProfileReporter(Path(temp_dir))
        
        # Create test data
        test_data = {
            "summary": ProfileSummary(
                database_path="/test/concurrent.sqlite",
                analysis_date=datetime.now(),
                total_customers=100,
                total_accounts=200,
                total_transactions=500,
                database_size_kb=100.0,
                unique_profiles=3,
                date_range=None
            ),
            "tables": {},
            "banking_metrics": {
                "account_stats": {},
                "transaction_stats": {},
                "customer_segments": {},
                "balance_distribution": {}
            }
        }
        
        results_queue = queue.Queue()
        
        def generate_report(thread_id):
            """Generate report in thread."""
            try:
                output_path = reporter.generate_report(test_data, format="html", filename=f"concurrent_report_{thread_id}")
                results_queue.put(("success", thread_id))
            except Exception as e:
                results_queue.put(("error", thread_id, str(e)))
        
        # Start multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=generate_report, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check results
        success_count = 0
        while not results_queue.empty():
            result = results_queue.get()
            if result[0] == "success":
                success_count += 1
            else:
                pytest.fail(f"Thread {result[1]} failed: {result[2]}")
        
        assert success_count == 5  # All threads should succeed


@pytest.mark.performance
class TestProfileReporterPerformance:
    """Performance tests for ProfileReporter."""
    
    def test_html_generation_performance(self):
        """Test HTML report generation performance."""
        # Create moderately complex data
        table_profiles = {}
        for i in range(10):  # 10 tables
            table_profiles[f"table_{i}"] = TableProfile(
                table_name=f"table_{i}",
                row_count=10000,
                column_count=20,
                columns=[{"name": f"col_{j}", "type": "TEXT"} for j in range(20)],
                data_types={f"col_{j}": "TEXT" for j in range(20)},
                null_counts={f"col_{j}": j * 10 for j in range(20)},
                unique_counts={f"col_{j}": 10000 - (j * 100) for j in range(20)},
                sample_values={f"col_{j}": [f"sample_{j}_{k}" for k in range(5)] for j in range(20)}
            )
        
        test_data = {
            "summary": ProfileSummary(
                database_path="/test/performance.sqlite",
                analysis_date=datetime.now(),
                total_customers=10000,
                total_accounts=25000,
                total_transactions=100000,
                database_size_kb=5120.0,
                unique_profiles=5,
                date_range=None
            ),
            "tables": table_profiles,
            "banking_metrics": {
                "account_stats": {f"type_{i}": {"count": 1000} for i in range(5)},
                "transaction_stats": {},
                "customer_segments": {},
                "balance_distribution": {}
            }
        }
        
        import tempfile
        temp_dir = tempfile.mkdtemp()
        reporter = ProfileReporter(Path(temp_dir))
        
        import time
        start_time = time.time()
        output_path = reporter.generate_report(test_data, format="html", filename="performance_test")
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        # Should complete within reasonable time (< 10 seconds for moderate complexity)
        assert execution_time < 10.0
        assert output_path.exists()
        assert output_path.stat().st_size > 1000  # Should generate substantial content