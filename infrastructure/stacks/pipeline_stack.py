"""CI/CD Pipeline stack using AWS CodePipeline and CodeBuild."""

from aws_cdk import (
    RemovalPolicy,
    Stack,
)
from aws_cdk import (
    aws_codebuild as codebuild,
)
from aws_cdk import (
    aws_codepipeline as codepipeline,
)
from aws_cdk import (
    aws_codepipeline_actions as codepipeline_actions,
)
from aws_cdk import (
    aws_codestarconnections as codestar,
)
from aws_cdk import (
    aws_ecr as ecr,
)
from aws_cdk import (
    aws_iam as iam,
)
from aws_cdk import (
    aws_s3 as s3,
)
from constructs import Construct


class PipelineStack(Stack):
    """CI/CD Pipeline for RedditSentinel."""

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # ECR Repository for Docker images
        self.ecr_repo = ecr.Repository(
            self,
            "EcrRepo",
            repository_name="reddit-sentinel",
            removal_policy=RemovalPolicy.RETAIN,
            lifecycle_rules=[
                ecr.LifecycleRule(
                    max_image_count=10,
                    description="Keep only 10 images",
                )
            ],
        )

        # S3 bucket for pipeline artifacts
        artifact_bucket = s3.Bucket(
            self,
            "ArtifactBucket",
            bucket_name=f"reddit-sentinel-artifacts-{self.account}",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            encryption=s3.BucketEncryption.S3_MANAGED,
        )

        # CodeStar connection to GitHub (must be manually activated in console)
        github_connection = codestar.CfnConnection(
            self,
            "GitHubConnection",
            connection_name="reddit-sentinel-github",
            provider_type="GitHub",
        )

        # Source artifact
        source_output = codepipeline.Artifact("SourceOutput")

        # Source action - GitHub via CodeStar connection
        source_action = codepipeline_actions.CodeStarConnectionsSourceAction(
            action_name="GitHub_Source",
            owner="mattymil",
            repo="reddit-sentinel",
            branch="main",
            connection_arn=github_connection.attr_connection_arn,
            output=source_output,
            trigger_on_push=True,
        )

        # CodeBuild project for testing
        test_project = codebuild.PipelineProject(
            self,
            "TestProject",
            project_name="reddit-sentinel-test",
            description="Run tests and linting for RedditSentinel",
            environment=codebuild.BuildEnvironment(
                build_image=codebuild.LinuxBuildImage.STANDARD_7_0,
                compute_type=codebuild.ComputeType.SMALL,
            ),
            build_spec=codebuild.BuildSpec.from_source_filename("buildspec-test.yml"),
            cache=codebuild.Cache.local(codebuild.LocalCacheMode.DOCKER_LAYER),
        )

        # CodeBuild project for building Docker image
        build_project = codebuild.PipelineProject(
            self,
            "BuildProject",
            project_name="reddit-sentinel-build",
            description="Build and push Docker image for RedditSentinel",
            environment=codebuild.BuildEnvironment(
                build_image=codebuild.LinuxBuildImage.STANDARD_7_0,
                compute_type=codebuild.ComputeType.SMALL,
                privileged=True,  # Required for Docker builds
            ),
            environment_variables={
                "ECR_REPO_URI": codebuild.BuildEnvironmentVariable(
                    value=self.ecr_repo.repository_uri
                ),
                "AWS_ACCOUNT_ID": codebuild.BuildEnvironmentVariable(
                    value=self.account
                ),
            },
            build_spec=codebuild.BuildSpec.from_source_filename("buildspec-build.yml"),
            cache=codebuild.Cache.local(codebuild.LocalCacheMode.DOCKER_LAYER),
        )

        # Grant ECR permissions to build project
        self.ecr_repo.grant_pull_push(build_project)

        # CodeBuild project for CDK deploy
        deploy_project = codebuild.PipelineProject(
            self,
            "DeployProject",
            project_name="reddit-sentinel-deploy",
            description="Deploy RedditSentinel infrastructure via CDK",
            environment=codebuild.BuildEnvironment(
                build_image=codebuild.LinuxBuildImage.STANDARD_7_0,
                compute_type=codebuild.ComputeType.SMALL,
            ),
            environment_variables={
                "ECR_REPO_URI": codebuild.BuildEnvironmentVariable(
                    value=self.ecr_repo.repository_uri
                ),
            },
            build_spec=codebuild.BuildSpec.from_source_filename("buildspec-deploy.yml"),
        )

        # Grant CDK deploy permissions
        deploy_project.add_to_role_policy(
            iam.PolicyStatement(
                actions=["sts:AssumeRole"],
                resources=[f"arn:aws:iam::{self.account}:role/cdk-*"],
            )
        )

        # Build output artifact
        build_output = codepipeline.Artifact("BuildOutput")

        # Pipeline
        pipeline = codepipeline.Pipeline(
            self,
            "Pipeline",
            pipeline_name="reddit-sentinel",
            artifact_bucket=artifact_bucket,
            stages=[
                codepipeline.StageProps(
                    stage_name="Source",
                    actions=[source_action],
                ),
                codepipeline.StageProps(
                    stage_name="Test",
                    actions=[
                        codepipeline_actions.CodeBuildAction(
                            action_name="Test",
                            project=test_project,
                            input=source_output,
                        )
                    ],
                ),
                codepipeline.StageProps(
                    stage_name="Build",
                    actions=[
                        codepipeline_actions.CodeBuildAction(
                            action_name="Build",
                            project=build_project,
                            input=source_output,
                            outputs=[build_output],
                        )
                    ],
                ),
                codepipeline.StageProps(
                    stage_name="Deploy",
                    actions=[
                        codepipeline_actions.CodeBuildAction(
                            action_name="Deploy",
                            project=deploy_project,
                            input=source_output,
                            extra_inputs=[build_output],
                        )
                    ],
                ),
            ],
        )
