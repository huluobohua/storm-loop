#!/bin/bash
# Install test dependencies
pip install -r tests/requirements-test.txt

# Run integration tests
python -m pytest tests/integration/test_enhanced_validators.py -v
