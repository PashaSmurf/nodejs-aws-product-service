import * as cdk from 'aws-cdk-lib';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as iam from 'aws-cdk-lib/aws-iam';
import { Construct } from 'constructs';
import * as path from 'path';
import * as fs from 'fs';

// Load and parse .env file for credentials
function loadEnvVars(): { [key: string]: string } {
  const envVars: { [key: string]: string } = {};
  const envPath = path.join(__dirname, '../.env');

  try {
    const envContent = fs.readFileSync(envPath, 'utf-8');
    const lines = envContent.split('\n');

    for (const line of lines) {
      const trimmed = line.trim();
      // Skip empty lines and comments
      if (!trimmed || trimmed.startsWith('#')) {
        continue;
      }

      // Parse KEY=VALUE pairs
      const [key, ...valueParts] = trimmed.split('=');
      if (key && valueParts.length > 0) {
        const cleanKey = key.trim();
        const cleanValue = valueParts.join('=').trim();

        // Only include valid environment variable names (alphanumeric and underscore)
        if (/^[a-zA-Z_][a-zA-Z0-9_]*$/.test(cleanKey) && cleanValue) {
          envVars[cleanKey] = cleanValue;
        }
      }
    }
  } catch (error) {
    console.warn('Warning: Could not read .env file:', error);
  }

  return envVars;
}

export class AuthorizationServiceStack extends cdk.Stack {
  public readonly basicAuthorizerFunction: lambda.Function;
  public readonly basicAuthorizerArn: string;

  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // Load environment variables from .env file
    const envVars = loadEnvVars();

    // Create Lambda function for Basic Authorization
    this.basicAuthorizerFunction = new lambda.Function(
      this,
      'BasicAuthorizerFunction',
      {
        runtime: lambda.Runtime.PYTHON_3_11,
        code: lambda.Code.fromAsset(path.join(__dirname, '../src'), {
          exclude: ['*.pyc', '__pycache__', '*.egg-info', '.pytest_cache'],
        }),
        handler: 'handlers.basic_authorizer.lambda_handler',
        description: 'Lambda authorizer for Basic Authentication',
        environment: envVars,
        timeout: cdk.Duration.seconds(30),
      }
    );

    // Grant API Gateway permission to invoke this Lambda as an authorizer
    this.basicAuthorizerFunction.addPermission('AllowAPIGatewayInvoked', {
      principal: new iam.ServicePrincipal('apigateway.amazonaws.com'),
      action: 'lambda:InvokeFunction',
      sourceArn: `arn:aws:apigateway:${this.region}::/restapis/*/authorizers/*`,
    });

    this.basicAuthorizerArn = this.basicAuthorizerFunction.functionArn;

    // Stack outputs
    new cdk.CfnOutput(this, 'BasicAuthorizerFunctionArn', {
      value: this.basicAuthorizerFunction.functionArn,
      description: 'ARN of the Basic Authorizer Lambda function',
      exportName: 'BasicAuthorizerFunctionArn',
    });

    new cdk.CfnOutput(this, 'BasicAuthorizerFunctionName', {
      value: this.basicAuthorizerFunction.functionName,
      description: 'Name of the Basic Authorizer Lambda function',
      exportName: 'BasicAuthorizerFunctionName',
    });
  }
}

