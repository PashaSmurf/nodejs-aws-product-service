import * as cdk from 'aws-cdk-lib';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as apigateway from 'aws-cdk-lib/aws-apigateway';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as s3_notifications from 'aws-cdk-lib/aws-s3-notifications';
import * as lambda_event_sources from 'aws-cdk-lib/aws-lambda-event-sources';
import * as iam from 'aws-cdk-lib/aws-iam';
import { Construct } from 'constructs';
import * as path from 'path';

export class ImportServiceStack extends cdk.Stack {
  public readonly apiEndpoint: string;
  public readonly bucket: s3.IBucket;

  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // Create S3 bucket for imports
    const bucketName = 'import-service-bucket-' + this.account.slice(-8).toLowerCase();
    
    const bucket = new s3.Bucket(this, 'ImportBucket', {
      bucketName: bucketName,
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      versioned: false,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      autoDeleteObjects: true,
      cors: [
        {
          allowedMethods: [s3.HttpMethods.GET, s3.HttpMethods.PUT, s3.HttpMethods.POST],
          allowedOrigins: ['*'],
          allowedHeaders: ['*'],
          maxAge: 3600, // 1 hour in seconds
        },
      ],
    });

    this.bucket = bucket;

    // Create 'uploaded' and 'parsed' folders by creating empty objects
    const uploadedFolderKey = 'uploaded/.keep';
    const parsedFolderKey = 'parsed/.keep';

    // Note: Folders don't actually exist in S3, they're just prefix conventions
    // But we can log that they will be used
    cdk.Tags.of(this).add('BucketStructure', 'uploaded/ and parsed/ folders');

    // Create API Gateway REST API
    const api = new apigateway.RestApi(this, 'ImportServiceApi', {
      restApiName: 'ImportServiceApi',
      description: 'Import Service API',
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

    // Lambda function for GET /import - Generates signed URL
    const importProductsFileFunction = new lambda.Function(
      this,
      'ImportProductsFileFunction',
      {
        runtime: lambda.Runtime.PYTHON_3_11,
        code: lambda.Code.fromAsset(path.join(__dirname, '../src'), {
          exclude: ['*.pyc', '__pycache__', '*.egg-info', '.pytest_cache'],
        }),
        handler: 'handlers.import_products_file.lambda_handler',
        description: 'Generate signed URL for CSV file upload',
        environment: {
          IMPORT_BUCKET_NAME: bucket.bucketName,
        },
        timeout: cdk.Duration.seconds(30),
      }
    );

    // Lambda function for S3 event - Parses CSV
    const importFileParserFunction = new lambda.Function(
      this,
      'ImportFileParserFunction',
      {
        runtime: lambda.Runtime.PYTHON_3_11,
        code: lambda.Code.fromAsset(path.join(__dirname, '../src'), {
          exclude: ['*.pyc', '__pycache__', '*.egg-info', '.pytest_cache'],
        }),
        handler: 'handlers.import_file_parser.lambda_handler',
        description: 'Parse CSV file from S3 and log records',
        environment: {
          IMPORT_BUCKET_NAME: bucket.bucketName,
          PRODUCTS_TABLE: 'products',
          STOCKS_TABLE: 'stocks',
        },
        timeout: cdk.Duration.seconds(60),
        memorySize: 512,
      }
    );

    // Grant permissions to Lambda functions
    // Permission for importProductsFileFunction to generate signed URLs
    bucket.grantWrite(importProductsFileFunction, 'uploaded/*');
    bucket.grantRead(importProductsFileFunction);

    // Permission for importFileParserFunction to read from uploaded and write to parsed
    bucket.grantRead(importFileParserFunction, 'uploaded/*');
    bucket.grantWrite(importFileParserFunction, 'parsed/*');
    bucket.grantDelete(importFileParserFunction, 'uploaded/*');

    // Grant Lambda permission to be invoked by S3
    importFileParserFunction.addPermission('AllowS3Invocation', {
      principal: new iam.ServicePrincipal('s3.amazonaws.com'),
      action: 'lambda:InvokeFunction',
      sourceArn: bucket.bucketArn,
    });

    // Grant DynamoDB permissions to importFileParserFunction
    importFileParserFunction.addToRolePolicy(
      new iam.PolicyStatement({
        actions: [
          'dynamodb:PutItem',
          'dynamodb:UpdateItem',
          'dynamodb:GetItem',
          'dynamodb:Query',
        ],
        resources: [
          `arn:aws:dynamodb:${this.region}:${this.account}:table/products`,
          `arn:aws:dynamodb:${this.region}:${this.account}:table/stocks`,
        ],
      })
    );

    // Configure S3 event notification for ObjectCreated events in 'uploaded' folder using S3EventSource
    importFileParserFunction.addEventSource(
      new lambda_event_sources.S3EventSource(bucket, {
        events: [s3.EventType.OBJECT_CREATED],
        filters: [{ prefix: 'uploaded/' }],
      })
    );

    // Create /import resource and GET method
    const importResource = api.root.addResource('import');

    const getMethod = importResource.addMethod('GET', new apigateway.LambdaIntegration(importProductsFileFunction, {
      integrationResponses: [
        {
          statusCode: '200',
          responseParameters: {
            'method.response.header.Content-Type': 'integration.response.header.Content-Type',
            'method.response.header.Access-Control-Allow-Origin': 'integration.response.header.Access-Control-Allow-Origin',
            'method.response.header.Access-Control-Allow-Methods': 'integration.response.header.Access-Control-Allow-Methods',
            'method.response.header.Access-Control-Allow-Headers': 'integration.response.header.Access-Control-Allow-Headers',
          },
        },
        {
          statusCode: '400',
          responseParameters: {
            'method.response.header.Access-Control-Allow-Origin': 'integration.response.header.Access-Control-Allow-Origin',
            'method.response.header.Access-Control-Allow-Methods': 'integration.response.header.Access-Control-Allow-Methods',
            'method.response.header.Access-Control-Allow-Headers': 'integration.response.header.Access-Control-Allow-Headers',
          },
        },
        {
          statusCode: '500',
          responseParameters: {
            'method.response.header.Access-Control-Allow-Origin': 'integration.response.header.Access-Control-Allow-Origin',
            'method.response.header.Access-Control-Allow-Methods': 'integration.response.header.Access-Control-Allow-Methods',
            'method.response.header.Access-Control-Allow-Headers': 'integration.response.header.Access-Control-Allow-Headers',
          },
        },
      ],
    }), {
      requestParameters: {
        'method.request.querystring.name': true, // name is required
      },
      methodResponses: [
        {
          statusCode: '200',
          responseParameters: {
            'method.response.header.Content-Type': true,
            'method.response.header.Access-Control-Allow-Origin': true,
            'method.response.header.Access-Control-Allow-Methods': true,
            'method.response.header.Access-Control-Allow-Headers': true,
          },
        },
        {
          statusCode: '400',
          responseParameters: {
            'method.response.header.Access-Control-Allow-Origin': true,
            'method.response.header.Access-Control-Allow-Methods': true,
            'method.response.header.Access-Control-Allow-Headers': true,
          },
        },
        {
          statusCode: '500',
          responseParameters: {
            'method.response.header.Access-Control-Allow-Origin': true,
            'method.response.header.Access-Control-Allow-Methods': true,
            'method.response.header.Access-Control-Allow-Headers': true,
          },
        },
      ],
    });

    // Stack outputs
    this.apiEndpoint = api.url;

    new cdk.CfnOutput(this, 'ImportServiceApiEndpoint', {
      value: api.url,
      description: 'Import Service API Endpoint',
      exportName: 'ImportServiceApiEndpoint',
    });

    new cdk.CfnOutput(this, 'ImportProductsFileEndpoint', {
      value: `${api.url}import`,
      description: 'Import Products File Endpoint - GET /import?name=<filename.csv>',
    });

    new cdk.CfnOutput(this, 'ImportBucketName', {
      value: bucket.bucketName,
      description: 'S3 Bucket Name for imports',
      exportName: 'ImportBucketName',
    });

    new cdk.CfnOutput(this, 'ImportBucketArn', {
      value: bucket.bucketArn,
      description: 'S3 Bucket ARN for imports',
      exportName: 'ImportBucketArn',
    });
  }
}

