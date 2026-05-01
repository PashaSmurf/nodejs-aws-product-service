#!/usr/bin/env node
import * as cdk from 'aws-cdk-lib';
import { ProductServiceStack } from './product_stack';

const app = new cdk.App();

new ProductServiceStack(app, 'ProductServiceStack', {
  stackName: 'product-service-stack',
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION || 'us-east-1',
  },
});

