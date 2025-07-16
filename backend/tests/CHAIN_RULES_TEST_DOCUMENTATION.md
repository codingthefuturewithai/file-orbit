# Chain Rules Test Documentation

## Overview

This document describes the comprehensive test suite for chain rules functionality in FileOrbit. The tests are split into two files to clearly document what currently works and what is broken.

## Test Files

### 1. `test_chain_rules.py` - Working Functionality

Tests the CURRENT WORKING behavior of chain rules:
- **Single file transfers**: Chain rules work correctly when transferring individual files
- **Event-triggered transfers**: Chain rules work for file events with specific file paths
- **Path template substitution**: All template variables are correctly replaced
- **Chain job lifecycle**: Jobs remain PENDING until parent completes, then get QUEUED
- **API integration**: Template execution creates proper chain jobs
- **Error recovery**: Chain job creation continues even if individual jobs fail

### 2. `test_chain_rules_known_issues.py` - Broken Functionality (CP-9)

Tests marked with `@pytest.mark.xfail` that document broken behavior:
- **Batch transfers with wildcards**: Chain jobs created with unresolved `{original_filename}`
- **Manual template execution with patterns**: Same issue as batch transfers
- **Proposed fixes**: Documents the desired behavior for file-level chain job creation

## Test Categories

### 1. Core Functionality Tests

#### TestChainJobService
- `test_create_chain_jobs`: Verifies chain jobs are created with correct attributes
- `test_path_template_substitution`: Tests all supported template variables
- `test_get_chain_jobs`: Verifies retrieval of chain jobs by parent ID

#### TestSingleFileChainRules
- `test_single_file_transfer_with_chains`: Working scenario with resolved paths
- `test_event_triggered_single_file_chain`: Event-driven transfers with chains

### 2. Integration Tests

#### TestChainRulesAPI
- `test_execute_template_with_chains`: Full API flow from template to chain jobs
- `test_create_template_validates_chain_endpoints`: Endpoint validation
- `test_execute_inactive_template_fails`: Inactive template handling

### 3. Worker Integration

#### TestChainJobStatusTransitions
- `test_chain_jobs_remain_pending_until_parent_completes`: Status lifecycle
- `test_worker_queues_chain_jobs_on_parent_success`: Worker chain job processing

### 4. Path Template Tests

#### TestChainRulePathTemplates
- Tests for all supported variables: `{year}`, `{month}`, `{day}`, `{filename}`, `{basename}`, `{extension}`
- Preservation of literal text in templates
- Handling of nested source paths

### 5. Validation and Error Handling

#### TestChainRuleValidation
- Invalid endpoint ID detection
- Empty chain rules handling

#### TestChainJobRecovery
- Partial failure recovery
- Error logging

## Running the Tests

### Run all chain rule tests:
```bash
cd backend
./run_chain_tests.sh
```

### Run only working tests:
```bash
cd backend
source venv/bin/activate
python -m pytest tests/test_chain_rules.py -v
```

### Run only broken functionality tests:
```bash
cd backend
source venv/bin/activate
python -m pytest tests/test_chain_rules_known_issues.py -v
```

### Run specific test class:
```bash
python -m pytest tests/test_chain_rules.py::TestSingleFileChainRules -v
```

## Test Fixtures

The tests use several fixtures defined in `conftest.py` and within the test files:

- `test_endpoints`: Creates source, primary, backup, and archive endpoints
- `test_template_with_chains`: Creates a template with two chain rules
- `db` / `db_session`: Database session for tests
- `client`: HTTP client for API tests

## Key Test Patterns

1. **Database Setup**: Each test gets a clean database transaction that's rolled back
2. **Endpoint Creation**: Test endpoints are created as fixtures for reuse
3. **Job Verification**: Tests verify job attributes, status transitions, and relationships
4. **Path Resolution**: Tests ensure template variables are properly replaced
5. **Error Simulation**: Some tests intentionally cause errors to verify recovery

## Known Issues Being Tested

The `test_chain_rules_known_issues.py` file documents:
1. Chain jobs created for batch transfers have unresolved template variables
2. The `{original_filename}` variable remains in paths instead of being replaced
3. Chain jobs fail when worker attempts to process them with rclone

## Future Improvements

When CP-9 is fixed, the tests in `test_chain_rules_known_issues.py` should:
1. Be moved to the main test file
2. Have the `@pytest.mark.xfail` decorators removed
3. Test the new file-level chain job creation logic