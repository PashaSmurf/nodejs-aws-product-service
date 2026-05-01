"""Unit tests for get_products_by_id handler"""

import json
import pytest
from src.handlers.get_products_by_id import lambda_handler

@pytest.mark.parametrize("product_id,expected_title,expected_price", [
    ("id1", "Oranges", 24),
    ("id2", "Bananas", 15),
    ("id3", None, None),
])
def test_get_products_by_id(product_id, expected_title, expected_price):
    """Test product retrieval by ID"""
    response = lambda_handler({"pathParameters": {"productId": product_id}}, {})
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    if expected_title:
        assert body["id"] == product_id
        assert body["title"] == expected_title
        assert body["price"] == expected_price

def test_get_products_by_id_not_found():
    """Test 404 for missing product"""
    response = lambda_handler({"pathParameters": {"productId": "invalid"}}, {})
    assert response["statusCode"] == 404
    assert "error" in json.loads(response["body"])

def test_get_products_by_id_missing_id():
    """Test 400 for missing productId"""
    response = lambda_handler({"pathParameters": {}}, {})
    assert response["statusCode"] == 400

def test_get_products_by_id_headers():
    """Test response headers"""
    response = lambda_handler({"pathParameters": {"productId": "id1"}}, {})
    assert response["headers"]["Content-Type"] == "application/json"
    assert response["headers"]["Access-Control-Allow-Origin"] == "*"
