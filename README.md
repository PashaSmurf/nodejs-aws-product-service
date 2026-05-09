# AWS Product Service

This is the backend product service for the AWS Shop application. It's built with Python Lambda functions, AWS DynamoDB,
AWS API Gateway, and AWS CDK for infrastructure-as-code deployment.

## Project Structure

```
nodejs-aws-product-service/
├── src/
│   ├── handlers/
│   │   ├── get_products_list.py      # Lambda handler for GET /products
│   │   ├── get_products_by_id.py     # Lambda handler for GET /products/{productId}
│   │   └── create_product.py         # Lambda handler for POST /products
│   ├── utils/
│   │   └── db.py                     # DynamoDB operations
│   ├── data/
│   │   └── products.py               # Mock product data (legacy)
│   └── models/
│       └── product.py                # Product model/schema
├── cdk/
│   ├── product_stack.ts              # CDK Stack definition (TypeScript)
│   └── app.ts                        # CDK App entry point
├── scripts/
│   └── seed_db.py                    # Database seeding script
├── tests/
│   ├── test_get_products_list.py
│   └── test_get_products_by_id.py
├── requirements.txt                  # Python dependencies (includes boto3)
├── DEPLOYMENT.md                     # Detailed deployment guide
├── .gitignore
└── README.md
```

## Key Features (Task 4)

DynamoDB Integration: Products and Stocks tables with proper schema
Five Lambda Functions: GET /products, GET /products/{id}, POST /products, PUT /products/{id}, DELETE /products/{id}
Error Handling: 400 for validation, 404 for not found, 500 for server errors
Comprehensive Logging: All requests logged with arguments
Data Seeding: Automated script to populate test data
CORS Enabled: All endpoints support cross-origin requests
Validation: Product creation/update validates required fields and types
Comprehensive Tests: 43 unit tests covering all CRUD operations

## Prerequisites

- Python 3.11+
- AWS CDK v2
- AWS CLI with configured credentials
- Node.js 16+ (for AWS CDK)
- boto3 library (for DynamoDB operations)

## Quick Start

1. **Install dependencies:**

```bash
npm install
pip install -r requirements.txt
```

2. **Deploy infrastructure:**

```bash
npm run deploy
```

3. **Seed database:**

```bash
python scripts/seed_db.py
```

4. **Test endpoints** (see DEPLOYMENT.md for detailed examples)

## Endpoints

### GET /products

Returns list of all available products with stock counts.

**Response (200):**

```json
[
  {
    "id": "id1",
    "title": "Oranges",
    "description": "Oranges Product Description",
    "price": 24,
    "count": 1
  },
  ...
]
```

### GET /products/{productId}

Returns a specific product by ID with stock count.

**Response (200):**

```json
{
  "id": "id1",
  "title": "Oranges",
  "price": 24,
  "count": 1
}
```

**Error (404):**

```json
{
  "error": "Product not found"
}
```

### POST /products

Creates a new product with stock information.

**Request body:**

```json
{
  "title": "New Product",
  "description": "Product description",
  "price": 99,
  "count": 10
}
```

**Response (201):**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "New Product",
  "price": 99,
  "count": 10
}
```

**Error (400):**

```json
{
  "error": "Invalid product data",
  "details": [
    "price must be a non-negative number"
  ]
}
```

## Testing

Run unit tests:

```bash
npm run test
```

All 43 tests pass covering:
- GET /products and GET /products/{id} operations
- POST /products creation with validation
- PUT /products/{id} updates
- DELETE /products/{id} removal
- Error handling (400, 404, 500 responses)

## Deployment Guide

For detailed deployment instructions, database setup, and troubleshooting, see [DEPLOYMENT.md](./DEPLOYMENT.md).

## Environment Variables

Lambda functions use:

- `PRODUCTS_TABLE` - DynamoDB products table name
- `STOCKS_TABLE` - DynamoDB stocks table name
- `AWS_REGION` - AWS region (default: us-east-1)
