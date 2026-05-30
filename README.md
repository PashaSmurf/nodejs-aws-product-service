# AWS Product & Import Services with Authorization

A microservices backend for the AWS Shop application consisting of three independent services:

- **Product Service**: CRUD operations on products with DynamoDB
- **Import Service**: CSV file import with S3 integration and automated parsing
- **Authorization Service**: Lambda authorizer providing Basic Authentication

## Project Structure

```
nodejs-aws-product-service/
│
├── product-service/                  # Product management microservice
│   ├── cdk/
│   │   ├── app.ts                    # CDK App entry point
│   │   └── product_stack.ts          # CDK Stack definition
│   ├── src/
│   │   ├── handlers/                 # Lambda handlers
│   │   │   ├── get_products_list.py
│   │   │   ├── get_products_by_id.py
│   │   │   ├── create_product.py
│   │   │   ├── update_product.py
│   │   │   └── delete_product.py
│   │   ├── data/
│   │   ├── models/
│   │   └── utils/
│   ├── tests/
│   ├── scripts/
│   ├── package.json
│   ├── tsconfig.json
│   ├── cdk.json
│   ├── pytest.ini
│   ├── requirements.txt
│   └── openapi.yaml
│
├── import-service/                   # File import microservice
│   ├── cdk/
│   │   ├── app.ts                    # CDK App entry point
│   │   └── import_stack.ts           # CDK Stack definition
│   ├── src/
│   │   ├── handlers/
│   │   │   ├── import_products_file.py  # Get signed URL for upload
│   │   │   └── import_file_parser.py    # Parse CSV from S3
│   │   ├── models/
│   │   └── utils/
│   ├── tests/
│   ├── package.json
│   ├── tsconfig.json
│   ├── cdk.json
│   ├── pytest.ini
│   └── requirements.txt
│
├── authorization-service/            # Authorization microservice (Task 7)
│   ├── cdk/
│   │   ├── app.ts                    # CDK App entry point
│   │   └── authorization_stack.ts    # CDK Stack definition
│   ├── src/
│   │   ├── handlers/
│   │   │   └── basic_authorizer.py   # Basic Auth Lambda authorizer
│   ├── tests/
│   │   ├── conftest.py
│   │   └── test_basic_authorizer.py
│   ├── package.json
│   ├── tsconfig.json
│   ├── cdk.json
│   ├── pytest.ini
│   ├── requirements.txt
│   ├── .env                          # Credentials (NOT in Git)
│   └── README.md
│
├── openapi.yaml                      # Shared API documentation
├── AUTHORIZATION_DEPLOYMENT_GUIDE.md # Authorization setup instructions
├── README.md
└── .gitignore
```

## Key Features

### Product Service (Task 4)

- **DynamoDB Integration**: Products and Stocks tables with proper schema
- **CRUD Operations**: GET /products, GET /products/{id}, POST /products, PUT /products/{id}, DELETE /products/{id}
- **Error Handling**: Proper HTTP status codes (400, 404, 500)
- **Comprehensive Logging**: All requests logged with arguments
- **Data Seeding**: Automated script to populate test data
- **CORS Enabled**: All endpoints support cross-origin requests
- **Validation**: Product creation/update validates required fields and types
- **Comprehensive Tests**: 43+ unit tests covering all CRUD operations

### Import Service (Task 5)

- **S3 Integration**: Secure file upload with signed URLs
- **CSV Parsing**: Automated parsing of uploaded CSV files
- **Event-Driven**: Triggered by S3 ObjectCreated events
- **File Organization**: Automatic movement from 'uploaded' to 'parsed' folders
- **Logging**: All records logged to CloudWatch
- **Security**: IAM policies restrict access to specific S3 locations

### Authorization Service (Task 7)

- **Lambda Authorizer**: Token-based authorization for API Gateway
- **Basic Authentication**: Validates HTTP Basic Auth header (base64-encoded credentials)
- **Environment-based Credentials**: Loads credentials from `.env` file using dotenv
- **IAM Policy Generation**: Returns Allow/Deny policies for API Gateway
- **Proper HTTP Status Codes**: 401 for missing header, 403 for invalid credentials
- **Integration**: Secures the `/import` endpoint in Import Service
- **Comprehensive Tests**: Tests for validation, invalid formats, and edge cases

## Prerequisites

- Python 3.11+
- AWS CDK v2
- AWS CLI with configured credentials
- Node.js 16+ (for AWS CDK)
- boto3 library (for AWS services)

## Quick Start

### Authorization Service

Deploy this first before the Import Service, as the Import Service depends on it.

1. **Install dependencies:**

```bash
cd authorization-service
npm install
pip install -r requirements.txt
```

2. **Configure credentials:**

Edit `.env` file with your GitHub username:

```
PashaSmurf=TEST_PASSWORD
```

3. **Deploy infrastructure:**

```bash
npm run deploy
```

### Product Service

1. **Install dependencies:**

```bash
cd product-service
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

### Import Service

1. **Install dependencies:**

```bash
cd import-service
npm install
pip install -r requirements.txt
```

2. **Deploy infrastructure:**

```bash
npm run deploy
```

3. **Create S3 bucket folders** (if not created automatically):
    - The service will create an S3 bucket with `uploaded/` and `parsed/` prefixes for file organization

### Running Tests

**Authorization Service:**

```bash
cd authorization-service
npm run test
```

Covers:

- Valid credential authentication
- Missing Authorization header (401)
- Invalid credentials (403)
- Invalid token format
- Bearer token rejection
- Malformed credentials

**Product Service:**

```bash
cd product-service
npm run test
```

**Import Service:**

```bash
cd import-service
npm run test
```

## Endpoints

### Product Service

#### GET /products

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

#### GET /products/{productId}

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

#### POST /products

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

### Import Service

#### GET /import

Generates a signed URL for uploading a CSV file to S3.

**Authorization:** Required - Basic Authentication header

**Query Parameters:**

- `name` (required): The name of the CSV file to upload (e.g., `products.csv`)

**Request:**

```
GET /import?name=products.csv
Authorization: Basic {base64_encoded_username_password}
```

Where `{base64_encoded_username_password}` is base64(`username:password`)

**Response (200):**
Returns a clean signed URL as plain text that can be used to upload a file via PUT request.

**Example usage:**

```bash
# Generate authorization token
AUTH_TOKEN=$(echo -n "PashaSmurf:TEST_PASSWORD" | base64)

# Get signed URL
SIGNED_URL=$(curl -H "Authorization: Basic $AUTH_TOKEN" https://{import-service-endpoint}/import?name=products.csv)

# Upload file using the signed URL
curl -X PUT --data-binary @products.csv "$SIGNED_URL"
```

**Error (401):**

```json
{
  "message": "Unauthorized"
}
```

Authorization header is missing or empty.

**Error (403):**

```json
{
  "message": "Forbidden"
}
```

Authorization token is invalid or credentials don't match.

**Error (400):**

```json
{
  "error": "File name parameter \"name\" is required"
}
```

#### S3 Event - File Parser

Automatically triggered when a file is uploaded to the `uploaded/` folder in S3.

**Behavior:**

1. Downloads the CSV file from S3
2. Parses it using Python's csv module
3. Logs each product record to CloudWatch
4. Moves the file from `uploaded/` to `parsed/` folder

**CSV Format Expected:**

```csv
id,title,description,price,count
1,Product Name,Description,99.99,10
```

### Accessing Deployed Services

After deployment, both services will output their API endpoints:

```
Product Service:
  API Endpoint: https://{product-api-id}.execute-api.{region}.amazonaws.com/dev/
  Products: https://{product-api-id}.execute-api.{region}.amazonaws.com/dev/products

Import Service:
  API Endpoint: https://{import-api-id}.execute-api.{region}.amazonaws.com/dev/
  Import Endpoint: https://{import-api-id}.execute-api.{region}.amazonaws.com/dev/import?name={filename}
  S3 Bucket: import-service-bucket-{account-suffix}
```

## Testing

### Product Service Tests

Run unit tests:

```bash
cd product-service
npm run test
```

Covers:

- GET /products and GET /products/{id} operations
- POST /products creation with validation
- PUT /products/{id} updates
- DELETE /products/{id} removal
- Error handling (400, 404, 500 responses)
- 43+ test cases

### Import Service Tests

Run unit tests:

```bash
cd import-service
npm run test
```

Tests include (to be implemented):

- Signed URL generation
- CSV parsing logic
- S3 event handling
- File movement functionality

## Environment Variables

### Product Service

Lambda functions use:

- `PRODUCTS_TABLE` - DynamoDB products table name
- `STOCKS_TABLE` - DynamoDB stocks table name
- `AWS_REGION` - AWS region (default: us-east-1)

### Import Service

Lambda functions use:

- `IMPORT_BUCKET_NAME` - S3 bucket name for imports
- `AWS_REGION` - AWS region (default: us-east-1)

### Authorization Service

The `basicAuthorizer` Lambda function receives credentials from the `.env` file during deployment:

- Format: `USERNAME=PASSWORD`
- Example: `PashaSmurf=TEST_PASSWORD`

**Important:** The `.env` file is not committed to Git and must be configured locally before deployment.

## Authorization Setup

The Import Service now requires Basic Authentication for the `/import` endpoint.
See [AUTHORIZATION_DEPLOYMENT_GUIDE.md](./AUTHORIZATION_DEPLOYMENT_GUIDE.md) for detailed setup instructions.

**Quick Summary:**

1. Deploy authorization-service first (requires `.env` file with credentials)
2. Deploy import-service (references authorization service Lambda)
3. Update client to send `Authorization: Basic {base64(username:password)}` header

