"""Unit tests for delete_product handler"""

import json
import pytest
from src.handlers.delete_product import lambda_handler


def test_delete_product_success():
    """Test successful product deletion"""
    event = {
        "pathParameters": {"productId": "id6"}
    }
    response = lambda_handler(event, {})

    assert response["statusCode"] == 204
    assert response["body"] == ""


def test_delete_product_not_found():
    """Test 404 when product does not exist"""
    event = {
        "pathParameters": {"productId": "nonexistent"}
    }
    response = lambda_handler(event, {})

    assert response["statusCode"] == 404
    body = json.loads(response["body"])
    assert "error" in body


def test_delete_product_missing_id():
    """Test 400 when product ID is missing"""
    event = {
        "pathParameters": {}
    }
    response = lambda_handler(event, {})

    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert "error" in body


def test_delete_product_headers_success():
    """Test response headers for successful deletion"""
    event = {
        "pathParameters": {"productId": "id5"}
    }
    response = lambda_handler(event, {})

    assert response["headers"]["Access-Control-Allow-Origin"] == "*"


def test_delete_product_headers_not_found():
    """Test response headers for 404 error"""
    event = {
        "pathParameters": {"productId": "invalid"}
    }
    response = lambda_handler(event, {})

    assert response["statusCode"] == 404
    assert response["headers"]["Content-Type"] == "application/json"
    assert response["headers"]["Access-Control-Allow-Origin"] == "*"


def test_delete_product_headers_missing_id():
    """Test response headers for 400 error"""
    event = {
        "pathParameters": {}
    }
    response = lambda_handler(event, {})

    assert response["statusCode"] == 400
    assert response["headers"]["Content-Type"] == "application/json"
    assert response["headers"]["Access-Control-Allow-Origin"] == "*"

