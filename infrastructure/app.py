#!/usr/bin/env python3
"""AWS CDK app for RedditSentinel infrastructure."""

import os

import aws_cdk as cdk

from stacks.pipeline_stack import PipelineStack
from stacks.application_stack import ApplicationStack


app = cdk.App()

env = cdk.Environment(
    account=os.environ.get("CDK_DEFAULT_ACCOUNT"),
    region=os.environ.get("CDK_DEFAULT_REGION", "us-east-1"),
)

# CI/CD Pipeline - deploys itself and the application
PipelineStack(
    app,
    "RedditSentinelPipeline",
    env=env,
    description="CI/CD pipeline for RedditSentinel",
)

# Application stack (can also be deployed standalone for dev)
ApplicationStack(
    app,
    "RedditSentinelApp",
    env=env,
    description="RedditSentinel application infrastructure",
)

app.synth()
