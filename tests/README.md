# Test Directory Structure

This directory contains the comprehensive test suite for SyFi AI synthetic banking data library.

## Directory Organization

```
tests/
├── conftest.py                    # Shared fixtures and configuration
├── data/                         # Test data and databases
│   ├── fixtures/                 # Static test data files
│   └── databases/               # Test database files
├── unit/                        # Unit tests
│   ├── test_parsers.py          # Configuration parser tests
│   ├── test_generators.py       # Data generation tests
│   ├── test_database.py         # Database operations tests
│   └── test_exporters.py        # Export functionality tests
├── integration/                 # Integration tests
│   ├── test_generation_pipeline.py  # End-to-end pipeline tests
│   └── test_database_operations.py  # Multi-component tests
├── web/                        # Web interface tests
│   ├── test_api_endpoints.py    # Flask API endpoint tests
│   └── test_ui_functionality.py # User interface tests
├── performance/                # Performance tests
│   └── test_benchmarks.py      # Performance benchmarks
└── domain/                     # Banking domain tests
    └── test_banking_rules.py   # Financial business rules tests
```

## Running Tests

### Install Test Dependencies
```bash
pip install -r requirements-test.txt
```

### Run All Tests
```bash
pytest tests/ -v
```

### Run Specific Test Categories
```bash
# Unit tests only
pytest tests/unit/ -v -m unit

# Integration tests
pytest tests/integration/ -v -m integration

# Web interface tests  
pytest tests/web/ -v -m web

# Performance tests (slow)
pytest tests/performance/ -v -m performance

# Banking domain tests
pytest tests/domain/ -v -m banking
```

### Coverage Report
```bash
# Generate HTML coverage report
pytest tests/ --cov=src --cov-report=html

# View coverage in terminal
pytest tests/ --cov=src --cov-report=term-missing
```

### Performance Benchmarking
```bash
# Run performance tests with benchmarks
pytest tests/performance/ --benchmark-only

# Generate benchmark report
pytest tests/performance/ --benchmark-json=benchmark.json
```

## Test Categories and Markers

- `@pytest.mark.unit` - Unit tests for individual functions
- `@pytest.mark.integration` - Integration tests for component interactions  
- `@pytest.mark.web` - Web interface and API tests
- `@pytest.mark.performance` - Performance and benchmark tests
- `@pytest.mark.domain` - Banking domain business rule tests
- `@pytest.mark.slow` - Slow-running tests (may be skipped)

## Test Data Management

### Fixtures
Common test fixtures are defined in `conftest.py`:
- `sample_customer` - Standard test customer
- `sample_account` - Standard test account  
- `sample_transaction` - Standard test transaction
- `temp_db` - Temporary database for isolated tests
- `populated_database` - Database with test data

### Isolated Testing
Each test uses isolated data through:
- Temporary databases created per test
- Fixed random seeds for reproducible results
- Automatic cleanup of test artifacts

## Writing New Tests

### Test Naming Convention
- Test files: `test_<module_name>.py`
- Test classes: `Test<ClassName>`
- Test methods: `test_<functionality>_<scenario>()`

### Example Test Structure
```python
import pytest

@pytest.mark.unit
class TestMyFeature:
    """Test my feature functionality."""
    
    def test_feature_success_case(self, fixture_name):
        """Test successful operation."""
        # Arrange
        # Act  
        # Assert
        
    def test_feature_error_case(self):
        """Test error handling."""
        # Test error conditions
```

### Test Documentation
- Include docstrings for all test classes and methods
- Document test purpose and expected behavior
- Add comments for complex test logic
- Use descriptive assertion messages

## Continuous Integration

Tests run automatically on:
- Pull requests
- Pushes to main branch  
- Scheduled nightly runs

CI configuration includes:
- Multiple Python versions (3.9, 3.10, 3.11, 3.12)
- Coverage reporting
- Performance regression detection
- Test result notifications

## Quality Gates

All tests must pass before:
- Code merge approvals
- Production deployments  
- Release tagging

Coverage requirements:
- Overall coverage >85%
- New code coverage >90%
- No decrease in coverage percentage