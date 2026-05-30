import json
import base64
import logging
import os

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    """Lambda authorizer for Basic Authentication"""

    logger.info('Authorizer event: %s' % json.dumps(event))

    token = event.get('authorizationToken')
    method_arn = event.get('methodArn')

    logger.info('Token received: %s' % (token is not None))
    logger.info('Method ARN: %s' % method_arn)

    # Missing token = Deny (not exception - avoid 500 errors)
    if not token:
        logger.warning('No authorization token')
        return generate_policy('user', 'Deny', method_arn, None)

    # Parse Basic auth
    if not token.startswith('Basic '):
        logger.warning('Invalid auth type: %s' % token[:10])
        return generate_policy('user', 'Deny', method_arn, None)

    try:
        # Extract and decode credentials
        encoded = token[6:]  # Remove 'Basic ' prefix
        decoded = base64.b64decode(encoded).decode('utf-8')
        username, password = decoded.split(':', 1)

        logger.info('Auth attempt for user: %s' % username)

        # Check credentials
        expected_pass = os.environ.get(username)
        logger.info('Expected pass exists: %s' % (expected_pass is not None))

        if expected_pass and expected_pass == password:
            logger.info('Authentication SUCCESS for: %s' % username)
            return generate_policy('user', 'Allow', method_arn, username)
        else:
            logger.warning('Authentication FAILED for: %s' % username)
            return generate_policy('user', 'Deny', method_arn, None)

    except Exception as e:
        logger.error('Exception during auth: %s' % str(e))
        return generate_policy('user', 'Deny', method_arn, None)


def generate_policy(principal_id, effect, resource, username):
    """Build IAM policy for Lambda authorizer with optional context"""
    auth_response = {
        'principalId': principal_id
    }

    if effect and resource:
        policy_document = {
            'Version': '2012-10-17',
            'Statement': [
                {
                    'Action': 'execute-api:Invoke',
                    'Effect': effect,
                    'Resource': resource
                }
            ]
        }
        auth_response['policyDocument'] = policy_document

    # Add context for request context
    auth_response['context'] = {
        'username': username or 'unknown'
    }

    return auth_response

