# AWS Product Service

This is the backend product service for the AWS Shop application. It's built with Python Lambda functions, AWS API Gateway, and AWS CDK for infrastructure-as-code deployment.

## Project Structure

```
nodejs-aws-product-service/
├── src/
│   ├── handlers/
│   │   ├── get_products_list.py      # Lambda handler for GET /products
│   │   └── get_products_by_id.py     # Lambda handler for GET /products/{productId}
│   ├── data/
│   │   └── products.py               # Mock product data
│   └── models/
│       └── product.py                # Product model/schema
├── cdk/
│   ├── product_stack.py              # CDK Stack definition
│   └── app.py                        # CDK App entry point
├── tests/
│   ├── test_get_products_list.py
│   └── test_get_products_by_id.py
├── requirements.txt                  # Python dependencies
├── .gitignore
└── README.md
```

## Prerequisites

- Python 3.9+
- AWS CDK v2
- AWS CLI with configured credentials
- Node.js (for AWS CDK)

## Setup

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Deploy to AWS:
```bash
cdk deploy
```

## Endpoints

- `GET /products` - Returns list of all available products
- `GET /products/{productId}` - Returns a specific product by ID

## Testing

Run unit tests:
```bash
pytest tests/
```

## Environment

Set the region in your environment or use the default:
```bash
export AWS_REGION=us-east-1
```

