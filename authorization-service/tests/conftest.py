"""
Pytest configuration and fixtures for authorization service tests.
Mocks all external AWS services for unit testing.
"""

import pytest
from unittest.mock import MagicMock, patch
import sys
from pathlib import Path
import base64

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))


@pytest.fixture
def basic_auth_token():
    """Generate a valid basic auth token for testing."""
    credentials = "testuser:testpass"
    encoded = base64.b64encode(credentials.encode()).decode()
    return f"Basic {encoded}"


@pytest.fixture
def invalid_auth_token():
    """Generate an invalid basic auth token."""
    return "Bearer invalid_token"


@pytest.fixture
def valid_event(basic_auth_token):
    """Create a valid API Gateway Lambda authorizer event."""
    return {
        'authorizationToken': basic_auth_token,
        'methodArn': 'arn:aws:execute-api:us-east-1:123456789012:import-api-id/dev/GET/import'
    }


@pytest.fixture
def empty_auth_event():
    """Create an event with no authorization token."""
    return {
        'authorizationToken': None,
        'methodArn': 'arn:aws:execute-api:us-east-1:123456789012:import-api-id/dev/GET/import'
    }


@pytest.fixture
def invalid_format_event():
    """Create an event with invalid authorization format."""
    return {
        'authorizationToken': 'Invalid_Format',
        'methodArn': 'arn:aws:execute-api:us-east-1:123456789012:import-api-id/dev/GET/import'
    }

