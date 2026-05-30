#!/usr/bin/env node
import * as cdk from 'aws-cdk-lib';
import { ProductServiceStack } from './product_stack';
import * as dotenv from 'dotenv';
import * as path from 'path';

// Load environment variables from .env file
dotenv.config({ path: path.join(__dirname, '../.env') });

const app = new cdk.App();

// Create product service stack
// The authorizer ARN should be set via BASIC_AUTHORIZER_ARN environment variable
new ProductServiceStack(app, 'ProductServiceStack', {
  stackName: 'product-service-stack',
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION || 'us-east-1',
  },
  authorizerFunctionArn: process.env.BASIC_AUTHORIZER_ARN,
});

