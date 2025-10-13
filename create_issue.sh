#!/bin/bash
cd /home/orlando/Projects/syfi-ai
gh issue create \
  --title "Fix failing test: main.py execution test due to ProfileBuilder initialization error" \
  --body "## Issue Summary

The test_main_execution test in tests/test_main.py is currently failing due to errors in the main.py module execution.

## Error Details

**Test Output:**
FAILED tests/test_main.py::test_main_execution - assert 1 == 0

**Root Causes:**

1. Configuration parsing error: 'Configuration' object has no attribute 'get'
2. ProfileBuilder initialization error: ProfileBuilder.__init__() missing 1 required positional argument: 'db_manager'

## Current State

- 58/59 tests pass (98.3% success rate)
- All web interface tests pass
- All API endpoint tests pass  
- All integration tests pass
- Only main.py execution fails

## Expected Behavior

The main() function should execute successfully and return 0, demonstrating the SyFi AI capabilities without errors.

## Technical Analysis

### Issue 1: Configuration Object
The Configuration object is missing a get attribute that the parser expects.

### Issue 2: ProfileBuilder Constructor
Line 242 in main.py:
builder = ProfileBuilder(seed=1000 + i)

Should likely be:
builder = ProfileBuilder(db_manager, seed=1000 + i)

## Impact Assessment

- Low Priority: Does not affect web interface functionality
- User Impact: None for web users
- Developer Impact: Affects main.py demonstration script
- CI/CD Impact: One failing test in test suite

## Files Involved

- main.py - Main demonstration script
- tests/test_main.py - Failing test
- src/syfi/profile_builder.py - ProfileBuilder class
- src/syfi/core/parser.py - ConfigurationParser class

This issue was discovered during testing after the home page redesign (Issue #1). The web interface works perfectly, but the CLI demonstration needs fixes." \
  --label "bug"