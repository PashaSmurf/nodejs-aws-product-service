"""Unit tests for get_products_list handler"""

import json
import pytest
from src.handlers.get_products_list import lambda_handler


def test_get_products_list_success():
    """Test successful retrieval of products list"""
    event = {}
    context = {}
    
    response = lambda_handler(event, context)
    
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert isinstance(body, list)
    assert len(body) > 0
    assert "id" in body[0]
    assert "title" in body[0]
    assert "description" in body[0]
    assert "price" in body[0]
    assert "count" in body[0]


def test_get_products_list_response_headers():
    """Test response headers are correct"""
    event = {}
    context = {}
    
    response = lambda_handler(event, context)
    
    assert response["headers"]["Content-Type"] == "application/json"
    assert response["headers"]["Access-Control-Allow-Origin"] == "*"


def test_get_products_list_contains_expected_products():
    """Test that response contains expected products"""
    event = {}
    context = {}
    
    response = lambda_handler(event, context)
    body = json.loads(response["body"])
    
    product_ids = [p["id"] for p in body]
    assert "id1" in product_ids
    assert "id2" in product_ids
    assert "id3" in product_ids

