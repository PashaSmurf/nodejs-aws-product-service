#!/usr/bin/env node
import * as cdk from 'aws-cdk-lib';
import { ImportServiceStack } from './import_stack';
import * as dotenv from 'dotenv';
import * as path from 'path';

// Load environment variables from .env file
dotenv.config({ path: path.join(__dirname, '../.env') });

const app = new cdk.App();

new ImportServiceStack(app, 'ImportServiceStack', {
  stackName: 'import-service-stack-v2',
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION || 'us-east-1',
  },
  authorizerFunctionArn: process.env.BASIC_AUTHORIZER_ARN,
});

