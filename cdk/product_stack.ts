import * as cdk from 'aws-cdk-lib';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as apigateway from 'aws-cdk-lib/aws-apigateway';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import { Construct } from 'constructs';
import * as path from 'path';

export class ProductServiceStack extends cdk.Stack {
  public readonly apiEndpoint: string;

  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // Create DynamoDB Tables
    const productsTable = new dynamodb.Table(this, 'ProductsTable', {
      tableName: 'products',
      partitionKey: { name: 'id', type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    const stocksTable = new dynamodb.Table(this, 'StocksTable', {
      tableName: 'stocks',
      partitionKey: { name: 'product_id', type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    // Create API Gateway REST API
    const api = new apigateway.RestApi(this, 'ProductServiceApi', {
      restApiName: 'ProductServiceApi',
      description: 'Product Service API',
      deploy: true,
      deployOptions: {
        stageName: 'dev',
      },
      defaultCorsPreflightOptions: {
        allowOrigins: apigateway.Cors.ALL_ORIGINS,
        allowMethods: apigateway.Cors.ALL_METHODS,
        allowHeaders: ['Content-Type', 'X-Amz-Date', 'Authorization', 'X-Api-Key'],
      },
    });

    // Lambda function for GET /products
    const getProductsListFunction = new lambda.Function(
      this,
      'GetProductsListFunction',
      {
        runtime: lambda.Runtime.PYTHON_3_11,
        code: lambda.Code.fromAsset(path.join(__dirname, '../src'), {
          exclude: ['*.pyc', '__pycache__', '*.egg-info', '.pytest_cache'],
        }),
        handler: 'handlers.get_products_list.lambda_handler',
        description: 'Get list of all products',
        environment: {
          PRODUCTS_TABLE: productsTable.tableName,
          STOCKS_TABLE: stocksTable.tableName,
        },
      }
    );

    // Lambda function for GET /products/{productId}
    const getProductsByIdFunction = new lambda.Function(
      this,
      'GetProductsByIdFunction',
      {
        runtime: lambda.Runtime.PYTHON_3_11,
        code: lambda.Code.fromAsset(path.join(__dirname, '../src'), {
          exclude: ['*.pyc', '__pycache__', '*.egg-info', '.pytest_cache'],
        }),
        handler: 'handlers.get_products_by_id.lambda_handler',
        description: 'Get product by ID',
        environment: {
          PRODUCTS_TABLE: productsTable.tableName,
          STOCKS_TABLE: stocksTable.tableName,
        },
      }
    );

    // Lambda function for POST /products
    const createProductFunction = new lambda.Function(
      this,
      'CreateProductFunction',
      {
        runtime: lambda.Runtime.PYTHON_3_11,
        code: lambda.Code.fromAsset(path.join(__dirname, '../src'), {
          exclude: ['*.pyc', '__pycache__', '*.egg-info', '.pytest_cache'],
        }),
        handler: 'handlers.create_product.lambda_handler',
        description: 'Create a new product',
        environment: {
          PRODUCTS_TABLE: productsTable.tableName,
          STOCKS_TABLE: stocksTable.tableName,
        },
      }
    );

    // Lambda function for PUT /products/{productId}
    const updateProductFunction = new lambda.Function(
      this,
      'UpdateProductFunction',
      {
        runtime: lambda.Runtime.PYTHON_3_11,
        code: lambda.Code.fromAsset(path.join(__dirname, '../src'), {
          exclude: ['*.pyc', '__pycache__', '*.egg-info', '.pytest_cache'],
        }),
        handler: 'handlers.update_product.lambda_handler',
        description: 'Update an existing product',
        environment: {
          PRODUCTS_TABLE: productsTable.tableName,
          STOCKS_TABLE: stocksTable.tableName,
        },
      }
    );

    // Lambda function for DELETE /products/{productId}
    const deleteProductFunction = new lambda.Function(
      this,
      'DeleteProductFunction',
      {
        runtime: lambda.Runtime.PYTHON_3_11,
        code: lambda.Code.fromAsset(path.join(__dirname, '../src'), {
          exclude: ['*.pyc', '__pycache__', '*.egg-info', '.pytest_cache'],
        }),
        handler: 'handlers.delete_product.lambda_handler',
        description: 'Delete a product',
        environment: {
          PRODUCTS_TABLE: productsTable.tableName,
          STOCKS_TABLE: stocksTable.tableName,
        },
      }
    );

    // Grant read/write permissions to Lambda functions
    productsTable.grantReadWriteData(getProductsListFunction);
    productsTable.grantReadWriteData(getProductsByIdFunction);
    productsTable.grantReadWriteData(createProductFunction);
    productsTable.grantReadWriteData(updateProductFunction);
    productsTable.grantReadWriteData(deleteProductFunction);

    stocksTable.grantReadWriteData(getProductsListFunction);
    stocksTable.grantReadWriteData(getProductsByIdFunction);
    stocksTable.grantReadWriteData(createProductFunction);
    stocksTable.grantReadWriteData(updateProductFunction);
    stocksTable.grantReadWriteData(deleteProductFunction);

      // Create /products resource and GET/POST methods
    const productsResource = api.root.addResource('products');
    productsResource.addMethod('GET', new apigateway.LambdaIntegration(getProductsListFunction));
    productsResource.addMethod('POST', new apigateway.LambdaIntegration(createProductFunction));

    // Create /products/{productId} resource and GET/PUT/DELETE methods
    const productIdResource = productsResource.addResource('{productId}');
    productIdResource.addMethod('GET', new apigateway.LambdaIntegration(getProductsByIdFunction));
    productIdResource.addMethod('PUT', new apigateway.LambdaIntegration(updateProductFunction));
    productIdResource.addMethod('DELETE', new apigateway.LambdaIntegration(deleteProductFunction));

    // Stack outputs
    this.apiEndpoint = api.url;

    new cdk.CfnOutput(this, 'ProductServiceApiEndpoint', {
      value: api.url,
      description: 'Product Service API Endpoint',
      exportName: 'ProductServiceApiEndpoint',
    });

    new cdk.CfnOutput(this, 'GetProductsListEndpoint', {
      value: `${api.url}products`,
      description: 'Get Products List Endpoint',
    });

    new cdk.CfnOutput(this, 'GetProductsByIdEndpoint', {
      value: `${api.url}products/{productId}`,
      description: 'Get Product by ID Endpoint',
    });

    new cdk.CfnOutput(this, 'CreateProductEndpoint', {
      value: `${api.url}products`,
      description: 'Create Product Endpoint',
    });

    new cdk.CfnOutput(this, 'UpdateProductEndpoint', {
      value: `${api.url}products/{productId}`,
      description: 'Update Product Endpoint',
    });

    new cdk.CfnOutput(this, 'DeleteProductEndpoint', {
      value: `${api.url}products/{productId}`,
      description: 'Delete Product Endpoint',
    });
  }
}

