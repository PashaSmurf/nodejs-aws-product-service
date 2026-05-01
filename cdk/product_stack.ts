import * as cdk from 'aws-cdk-lib';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as apigateway from 'aws-cdk-lib/aws-apigateway';
import { Construct } from 'constructs';
import * as path from 'path';

export class ProductServiceStack extends cdk.Stack {
  public readonly apiEndpoint: string;

  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

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
      }
    );

    // Create /products resource and GET method
    const productsResource = api.root.addResource('products');
    productsResource.addMethod('GET', new apigateway.LambdaIntegration(getProductsListFunction));

    // Create /products/{productId} resource and GET method
    const productIdResource = productsResource.addResource('{productId}');
    productIdResource.addMethod('GET', new apigateway.LambdaIntegration(getProductsByIdFunction));

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
  }
}

