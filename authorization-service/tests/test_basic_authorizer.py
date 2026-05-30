"""
Tests for the Basic Authorizer Lambda function.
"""

import pytest
import sys
from pathlib import Path
import base64
import os
from unittest.mock import patch

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from handlers.basic_authorizer import lambda_handler, generate_policy


class TestBasicAuthorizer:
    """Test suite for Basic Authorizer Lambda."""

    def test_valid_credentials(self, valid_event):
        """Test successful authentication with valid credentials."""
        # Set environment variable for test credentials
        with patch.dict(os.environ, {'testuser': 'testpass'}):
            response = lambda_handler(valid_event, None)

            assert 'policyDocument' in response
            assert response['principalId'] == 'user'
            assert response['policyDocument']['Statement'][0]['Effect'] == 'Allow'
            assert response['context']['username'] == 'testuser'

    def test_missing_authorization_header(self, empty_auth_event):
        """Test failure when Authorization header is missing."""
        response = lambda_handler(empty_auth_event, None)

        # Should return Deny policy instead of raising exception
        assert response['principalId'] == 'user'
        assert response['policyDocument']['Statement'][0]['Effect'] == 'Deny'
        assert response['context']['username'] == 'unknown'

    def test_invalid_credentials(self, valid_event):
        """Test failure when credentials don't match environment variables."""
        # Don't set the environment variable - credentials will be invalid
        response = lambda_handler(valid_event, None)

        assert response['principalId'] == 'user'
        assert response['policyDocument']['Statement'][0]['Effect'] == 'Deny'

    def test_invalid_auth_format(self, invalid_format_event):
        """Test failure when auth token format is incorrect."""
        response = lambda_handler(invalid_format_event, None)

        assert response['policyDocument']['Statement'][0]['Effect'] == 'Deny'

    def test_wrong_password(self):
        """Test failure when password doesn't match."""
        credentials = "testuser:wrongpass"
        encoded = base64.b64encode(credentials.encode()).decode()
        event = {
            'authorizationToken': f"Basic {encoded}",
            'methodArn': 'arn:aws:execute-api:us-east-1:123456789012:import-api-id/dev/GET/import'
        }

        with patch.dict(os.environ, {'testuser': 'testpass'}):
            response = lambda_handler(event, None)

            assert response['policyDocument']['Statement'][0]['Effect'] == 'Deny'

    def test_generate_policy(self):
        """Test IAM policy generation."""
        policy = generate_policy('user123', 'Allow', 'arn:aws:execute-api:us-east-1:123456789012:api-id/*', 'testuser')

        assert policy['principalId'] == 'user123'
        assert policy['policyDocument']['Statement'][0]['Effect'] == 'Allow'
        assert policy['context']['username'] == 'testuser'

    def test_bearer_token_format(self):
        """Test that Bearer format is rejected (only Basic is allowed)."""
        credentials = "testuser:testpass"
        encoded = base64.b64encode(credentials.encode()).decode()
        event = {
            'authorizationToken': f"Bearer {encoded}",
            'methodArn': 'arn:aws:execute-api:us-east-1:123456789012:import-api-id/dev/GET/import'
        }

        response = lambda_handler(event, None)

        assert response['policyDocument']['Statement'][0]['Effect'] == 'Deny'

    def test_missing_colon_in_credentials(self):
        """Test that credentials without colon separator are rejected."""
        # Base64 encode a string without colon
        credentials = "testusertestpass"
        encoded = base64.b64encode(credentials.encode()).decode()
        event = {
            'authorizationToken': f"Basic {encoded}",
            'methodArn': 'arn:aws:execute-api:us-east-1:123456789012:import-api-id/dev/GET/import'
        }

        response = lambda_handler(event, None)

        assert response['policyDocument']['Statement'][0]['Effect'] == 'Deny'



