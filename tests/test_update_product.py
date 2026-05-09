"""Unit tests for update_product handler"""

import json
import pytest
from src.handlers.update_product import lambda_handler


def test_update_product_success():
    """Test successful product update"""
    event = {
        "pathParameters": {"productId": "id1"},
        "body": json.dumps({
            "price": 199,
            "count": 10
        })
    }
    response = lambda_handler(event, {})

    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["id"] == "id1"
    assert body["price"] == 199
    assert body["count"] == 10


def test_update_product_title_only():
    """Test updating only title"""
    event = {
        "pathParameters": {"productId": "id2"},
        "body": json.dumps({
            "title": "Updated Bananas"
        })
    }
    response = lambda_handler(event, {})

    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["title"] == "Updated Bananas"


def test_update_product_description_only():
    """Test updating only description"""
    event = {
        "pathParameters": {"productId": "id2"},
        "body": json.dumps({
            "description": "New description"
        })
    }
    response = lambda_handler(event, {})

    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["description"] == "New description"


def test_update_product_price_only():
    """Test updating only price"""
    event = {
        "pathParameters": {"productId": "id3"},
        "body": json.dumps({
            "price": 50
        })
    }
    response = lambda_handler(event, {})

    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["price"] == 50


def test_update_product_count_only():
    """Test updating only count"""
    event = {
        "pathParameters": {"productId": "id3"},
        "body": json.dumps({
            "count": 25
        })
    }
    response = lambda_handler(event, {})

    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["count"] == 25


def test_update_product_missing_id():
    """Test 400 when product ID is missing"""
    event = {
        "pathParameters": {},
        "body": json.dumps({
            "price": 99
        })
    }
    response = lambda_handler(event, {})

    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert "error" in body


def test_update_product_not_found():
    """Test 404 when product does not exist"""
    event = {
        "pathParameters": {"productId": "nonexistent"},
        "body": json.dumps({
            "price": 99
        })
    }
    response = lambda_handler(event, {})

    assert response["statusCode"] == 404
    body = json.loads(response["body"])
    assert "error" in body


def test_update_product_empty_body():
    """Test validation error when no fields provided"""
    event = {
        "pathParameters": {"productId": "id1"},
        "body": json.dumps({})
    }
    response = lambda_handler(event, {})

    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert "error" in body
    assert "details" in body


def test_update_product_negative_price():
    """Test validation error for negative price"""
    event = {
        "pathParameters": {"productId": "id1"},
        "body": json.dumps({
            "price": -50
        })
    }
    response = lambda_handler(event, {})

    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert "price must be a non-negative number" in body["details"]


def test_update_product_negative_count():
    """Test validation error for negative count"""
    event = {
        "pathParameters": {"productId": "id1"},
        "body": json.dumps({
            "count": -5
        })
    }
    response = lambda_handler(event, {})

    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert "count must be a non-negative integer" in body["details"]


def test_update_product_invalid_title_type():
    """Test validation error for invalid title type"""
    event = {
        "pathParameters": {"productId": "id1"},
        "body": json.dumps({
            "title": 123
        })
    }
    response = lambda_handler(event, {})

    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert "title must be a string" in body["details"]


def test_update_product_invalid_price_type():
    """Test validation error for invalid price type"""
    event = {
        "pathParameters": {"productId": "id1"},
        "body": json.dumps({
            "price": "expensive"
        })
    }
    response = lambda_handler(event, {})

    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert "price must be a non-negative number" in body["details"]


def test_update_product_invalid_count_type():
    """Test validation error for invalid count type"""
    event = {
        "pathParameters": {"productId": "id1"},
        "body": json.dumps({
            "count": "lots"
        })
    }
    response = lambda_handler(event, {})

    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert "count must be a non-negative integer" in body["details"]


def test_update_product_invalid_json():
    """Test error handling for invalid JSON"""
    event = {
        "pathParameters": {"productId": "id1"},
        "body": "not valid json"
    }
    response = lambda_handler(event, {})

    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert "error" in body


def test_update_product_headers():
    """Test response headers"""
    event = {
        "pathParameters": {"productId": "id1"},
        "body": json.dumps({
            "price": 99
        })
    }
    response = lambda_handler(event, {})

    assert response["headers"]["Content-Type"] == "application/json"
    assert response["headers"]["Access-Control-Allow-Origin"] == "*"


def test_update_product_multiple_fields():
    """Test updating multiple fields at once"""
    event = {
        "pathParameters": {"productId": "id1"},
        "body": json.dumps({
            "title": "Updated Title",
            "description": "Updated Description",
            "price": 150,
            "count": 20
        })
    }
    response = lambda_handler(event, {})

    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["title"] == "Updated Title"
    assert body["description"] == "Updated Description"
    assert body["price"] == 150
    assert body["count"] == 20

