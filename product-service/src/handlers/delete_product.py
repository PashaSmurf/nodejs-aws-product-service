"""Lambda handler for DELETE /products/{productId} endpoint"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.db import delete_product


def lambda_handler(event, context):
    """
    Delete a product from DynamoDB.

    Args:
        event: Lambda event with pathParameters containing productId
        context: Lambda context

    Returns:
        API Gateway response with 204 No Content on success or error
    """
    print(f"Received request: {json.dumps(event)}")

    try:
        # Get productId from path parameters
        product_id = event.get("pathParameters", {}).get("productId")
        print(f"Deleting product with ID: {product_id}")

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

        # Delete product
        success = delete_product(product_id)

        if not success:
            print(f"Product not found: {product_id}")
            return {
                "statusCode": 404,
                "body": json.dumps({"error": "Product not found"}),
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*",
                },
            }

        print(f"Product deleted: {product_id}")
        return {
            "statusCode": 204,
            "body": "",
            "headers": {
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
