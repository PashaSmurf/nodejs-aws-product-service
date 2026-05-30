"""CORS helper utilities for Lambda responses"""

import json


def get_cors_headers():
    """Get standard CORS headers for all API responses"""
    return {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
        "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
        "Access-Control-Max-Age": "3600",
    }


def success_response(body, status_code=200):
    """Create a successful API response with CORS headers"""
    return {
        "statusCode": status_code,
        "body": json.dumps(body) if not isinstance(body, str) else body,
        "headers": get_cors_headers(),
    }


def error_response(error, status_code=500):
    """Create an error API response with CORS headers"""
    return {
        "statusCode": status_code,
        "body": json.dumps({"error": error}),
        "headers": get_cors_headers(),
    }


def options_response():
    """Create response for OPTIONS preflight request"""
    return {
        "statusCode": 200,
        "body": json.dumps({}),
        "headers": get_cors_headers(),
    }

