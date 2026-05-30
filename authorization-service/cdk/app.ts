#!/usr/bin/env node
import * as cdk from 'aws-cdk-lib';
import { AuthorizationServiceStack } from './authorization_stack';

const app = new cdk.App();

new AuthorizationServiceStack(app, 'AuthorizationServiceStack', {
  stackName: 'authorization-service-stack-v1',
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION || 'us-east-1',
  },
});

