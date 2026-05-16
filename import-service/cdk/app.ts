#!/usr/bin/env node
import * as cdk from 'aws-cdk-lib';
import { ImportServiceStack } from './import_stack';

const app = new cdk.App();

new ImportServiceStack(app, 'ImportServiceStack', {
  stackName: 'import-service-stack-v2',
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION || 'us-east-1',
  },
});

