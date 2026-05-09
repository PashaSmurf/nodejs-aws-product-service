"""Unit tests for create_product handler"""

import json
import pytest
from src.handlers.create_product import lambda_handler


def test_create_product_success():
    """Test successful product creation"""
    event = {
        "body": json.dumps({
            "title": "Test Product",
            "description": "Test Description",
            "price": 99,
            "count": 5
        })
    }
    response = lambda_handler(event, {})

    assert response["statusCode"] == 201
    body = json.loads(response["body"])
    assert body["id"] is not None
    assert body["title"] == "Test Product"
    assert body["description"] == "Test Description"
    assert body["price"] == 99
    assert body["count"] == 5


def test_create_product_minimal():
    """Test product creation with minimal required fields"""
    event = {
        "body": json.dumps({
            "title": "Minimal Product",
            "price": 50,
            "count": 10
        })
    }
    response = lambda_handler(event, {})

    assert response["statusCode"] == 201
    body = json.loads(response["body"])
    assert body["title"] == "Minimal Product"
    assert body["price"] == 50
    assert body["count"] == 10


def test_create_product_missing_title():
    """Test validation error when title is missing"""
    event = {
        "body": json.dumps({
            "price": 99,
            "count": 5
        })
    }
    response = lambda_handler(event, {})

    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert "error" in body
    assert "title is required" in body["details"]


def test_create_product_missing_price():
    """Test validation error when price is missing"""
    event = {
        "body": json.dumps({
            "title": "Test",
            "count": 5
        })
    }
    response = lambda_handler(event, {})

    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert "price is required" in body["details"]


def test_create_product_missing_count():
    """Test validation error when count is missing"""
    event = {
        "body": json.dumps({
            "title": "Test",
            "price": 99
        })
    }
    response = lambda_handler(event, {})

    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert "count is required" in body["details"]


def test_create_product_negative_price():
    """Test validation error for negative price"""
    event = {
        "body": json.dumps({
            "title": "Test",
            "price": -50,
            "count": 5
        })
    }
    response = lambda_handler(event, {})

    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert "price must be a non-negative number" in body["details"]


def test_create_product_negative_count():
    """Test validation error for negative count"""
    event = {
        "body": json.dumps({
            "title": "Test",
            "price": 99,
            "count": -5
        })
    }
    response = lambda_handler(event, {})

    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert "count must be a non-negative integer" in body["details"]


def test_create_product_invalid_price_type():
    """Test validation error for invalid price type"""
    event = {
        "body": json.dumps({
            "title": "Test",
            "price": "invalid",
            "count": 5
        })
    }
    response = lambda_handler(event, {})

    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert "price must be a non-negative number" in body["details"]


def test_create_product_invalid_count_type():
    """Test validation error for invalid count type"""
    event = {
        "body": json.dumps({
            "title": "Test",
            "price": 99,
            "count": "five"
        })
    }
    response = lambda_handler(event, {})

    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert "count must be a non-negative integer" in body["details"]


def test_create_product_invalid_json():
    """Test error handling for invalid JSON"""
    event = {
        "body": "invalid json"
    }
    response = lambda_handler(event, {})

    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert "error" in body


def test_create_product_headers():
    """Test response headers"""
    event = {
        "body": json.dumps({
            "title": "Test",
            "price": 99,
            "count": 5
        })
    }
    response = lambda_handler(event, {})

    assert response["headers"]["Content-Type"] == "application/json"
    assert response["headers"]["Access-Control-Allow-Origin"] == "*"


def test_create_product_unique_ids():
    """Test that each product gets a unique ID"""
    event1 = {
        "body": json.dumps({
            "title": "Product 1",
            "price": 10,
            "count": 1
        })
    }
    event2 = {
        "body": json.dumps({
            "title": "Product 2",
            "price": 20,
            "count": 2
        })
    }

    response1 = lambda_handler(event1, {})
    response2 = lambda_handler(event2, {})

    body1 = json.loads(response1["body"])
    body2 = json.loads(response2["body"])

    assert body1["id"] != body2["id"]

