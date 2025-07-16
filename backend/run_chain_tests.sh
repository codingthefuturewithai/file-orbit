#!/bin/bash
# Script to run chain rules tests

echo "Running Chain Rules Tests"
echo "========================="
echo ""

# Activate virtual environment
source venv/bin/activate

# Ensure test database exists
echo "Setting up test database..."
psql -U timkitchens -d postgres -c "DROP DATABASE IF EXISTS file_orbit_test;" 2>/dev/null
psql -U timkitchens -d postgres -c "CREATE DATABASE file_orbit_test;" 2>/dev/null

echo ""
echo "Running current working chain rules tests..."
echo "-------------------------------------------"
python -m pytest tests/test_chain_rules.py -v -x

echo ""
echo "Running tests for known issues (expected to fail)..."
echo "---------------------------------------------------"
python -m pytest tests/test_chain_rules_known_issues.py -v -x

echo ""
echo "Test Summary:"
echo "- test_chain_rules.py: Tests for WORKING functionality"
echo "- test_chain_rules_known_issues.py: Tests for BROKEN functionality (CP-9)"