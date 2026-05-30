# Authorization Service

A microservice that provides Basic Authentication authorization through a Lambda authorizer for the AWS Shop
application.

## Project Structure

```
authorization-service/
├── cdk/
│   ├── app.ts                    # CDK App entry point
│   └── authorization_stack.ts    # CDK Stack definition
├── src/
│   ├── handlers/
│   │   └── basic_authorizer.py   # Basic Auth Lambda authorizer
├── tests/
│   ├── conftest.py
│   └── test_basic_authorizer.py
├── package.json
├── requirements.txt
├── tsconfig.json
├── cdk.json
├── pytest.ini
└── .env                          # Environment variables (GH_USERNAME=TEST_PASSWORD)
```

## Features

- **Basic Authentication**: Validates HTTP Basic Authorization headers
- **Lambda Authorizer**: Returns IAM policy for valid credentials
- **Environment-based Credentials**: Loads credentials from `.env` file using `python-dotenv`
- **Proper HTTP Status Codes**:
    - `401`: When Authorization header is missing
    - `403`: When credentials are invalid
    - IAM Policy: When credentials are valid

## Prerequisites

- Python 3.11+
- AWS CDK v2
- AWS CLI with configured credentials
- Node.js 16+ (for AWS CDK)

## Setup

### 1. Install Dependencies

```bash
cd authorization-service
npm install
pip install -r requirements.txt
```

### 2. Configure Credentials

Edit the `.env` file with your GitHub username and password:

```
PashaSmurf=TEST_PASSWORD
```

**DO NOT commit this file to Git!** It's already in `.gitignore`.

### 3. Deploy Infrastructure

```bash
npm run deploy
```

This will:

- Create the `basicAuthorizer` Lambda function
- Export the function ARN as `BasicAuthorizerFunctionArn`

## Lambda Authorizer Format

The `basicAuthorizer` expects Authorization headers in the format:

```
Authorization: Basic {base64_encoded_credentials}
```

Where `{base64_encoded_credentials}` is the base64 encoding of `username:password`.

### Example

For credentials `PashaSmurf:TEST_PASSWORD`:

```bash
# Encode the credentials
echo -n "PashaSmurf:TEST_PASSWORD" | base64
# Output: UGFzaGFTbXVyZjpURVNUX1BBU1NXT1JE

# Use in Authorization header
Authorization: Basic UGFzaGFTbXVyZjpURVNUX1BBU1NXT1JE
```

## Testing

Run unit tests:

```bash
npm run test
```

Tests include:

- Valid credential authentication
- Missing Authorization header (401)
- Invalid credentials (403)
- Invalid token format
- Bearer token rejection
- Malformed credentials

## Integration with Import Service

The authorization-service exports the `basicAuthorizer` Lambda ARN with the export name `BasicAuthorizerFunctionArn`.
The Import Service Stack references this to create a Lambda authorizer for the `/import` endpoint.

### How It Works

1. Client sends request with `Authorization: Basic {base64(username:password)}`
2. API Gateway invokes the `basicAuthorizer` Lambda
3. Authorizer validates credentials against environment variables
4. If valid: Returns IAM policy allowing the invocation
5. If invalid: Returns 403 Forbidden
6. If missing Authorization header: Returns 401 Unauthorized

## Environment Variables

The `basicAuthorizer` Lambda receives credentials from the `.env` file as environment variables during deployment. The
CDK stack loads the `.env` file and passes the credentials to the Lambda function.

### Example .env

```
PashaSmurf=TEST_PASSWORD
```

The environment variable key is the username and the value is the password.

## Deployment Output

After successful deployment, you'll see outputs like:

```
BasicAuthorizerFunctionArn: arn:aws:lambda:us-east-1:123456789012:function:AuthorizationServiceStack-BasicAuthorizerFunction...
BasicAuthorizerFunctionName: AuthorizationServiceStack-BasicAuthorizerFunction...
```

These values are used by the Import Service to configure the Lambda authorizer.

