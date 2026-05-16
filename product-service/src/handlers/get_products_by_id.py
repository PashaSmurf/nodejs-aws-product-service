"""Lambda handler for GET /products/{productId} endpoint"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.db import get_product_by_id


def lambda_handler(event, context):
    """
    Get a specific product by ID from DynamoDB.

    Args:
        event: Lambda event with pathParameters containing productId
        context: Lambda context
    
    Returns:
        API Gateway response with product details or error
    """
    print(f"Received request: {json.dumps(event)}")

    try:
        # Get productId from path parameters
        product_id = event.get("pathParameters", {}).get("productId")
        print(f"Fetching product with ID: {product_id}")

        if not product_id:
            print("Product ID is required")
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Product ID is required"}),
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*",
                },
            }

        # Find product by ID
        product = get_product_by_id(product_id)

        if not product:
            print(f"Product not found: {product_id}")
            return {
                "statusCode": 404,
                "body": json.dumps({"error": "Product not found"}),
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*",
                },
            }

        print(f"Product found: {json.dumps(product)}")
        return {
            "statusCode": 200,
            "body": json.dumps(product),
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
        }
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Internal server error"}),
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
        }
