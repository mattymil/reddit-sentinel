"""Application infrastructure stack - ECS, Redis, networking."""

from aws_cdk import (
    CfnOutput,
    Duration,
    RemovalPolicy,
    Stack,
)
from aws_cdk import (
    aws_ec2 as ec2,
)
from aws_cdk import (
    aws_ecr as ecr,
)
from aws_cdk import (
    aws_ecs as ecs,
)
from aws_cdk import (
    aws_ecs_patterns as ecs_patterns,
)
from aws_cdk import (
    aws_elasticache as elasticache,
)
from aws_cdk import (
    aws_logs as logs,
)
from aws_cdk import (
    aws_secretsmanager as secretsmanager,
)
from constructs import Construct


class ApplicationStack(Stack):
    """RedditSentinel application infrastructure."""

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # VPC - public subnets only to avoid NAT Gateway costs (~$32/mo)
        vpc = ec2.Vpc(
            self,
            "Vpc",
            max_azs=2,
            nat_gateways=0,  # No NAT Gateway - ECS will use public IP
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24,
                ),
            ],
        )

        # Security group for Redis
        redis_sg = ec2.SecurityGroup(
            self,
            "RedisSg",
            vpc=vpc,
            description="Security group for Redis",
            allow_all_outbound=False,
        )

        # Security group for ECS tasks
        ecs_sg = ec2.SecurityGroup(
            self,
            "EcsSg",
            vpc=vpc,
            description="Security group for ECS tasks",
            allow_all_outbound=True,
        )

        # Allow ECS to connect to Redis
        redis_sg.add_ingress_rule(
            peer=ecs_sg,
            connection=ec2.Port.tcp(6379),
            description="Allow ECS tasks to connect to Redis",
        )

        # ElastiCache subnet group (using public subnets since no private)
        redis_subnet_group = elasticache.CfnSubnetGroup(
            self,
            "RedisSubnetGroupPublic",
            description="Subnet group for Redis (public)",
            subnet_ids=[subnet.subnet_id for subnet in vpc.public_subnets],
            cache_subnet_group_name="reddit-sentinel-redis-public",
        )

        # ElastiCache Redis cluster (single node for cost)
        redis_cluster = elasticache.CfnCacheCluster(
            self,
            "RedisClusterPublic",
            cache_node_type="cache.t3.micro",
            engine="redis",
            num_cache_nodes=1,
            cluster_name="reddit-sentinel-v2",
            vpc_security_group_ids=[redis_sg.security_group_id],
            cache_subnet_group_name=redis_subnet_group.cache_subnet_group_name,
        )
        redis_cluster.add_dependency(redis_subnet_group)

        # Secrets for Reddit API credentials
        reddit_secrets = secretsmanager.Secret(
            self,
            "RedditSecrets",
            secret_name="reddit-sentinel/reddit-api",
            description="Reddit API credentials for RedditSentinel",
            generate_secret_string=secretsmanager.SecretStringGenerator(
                secret_string_template='{"client_id":"","user_agent":"RedditSentinel/0.1.0"}',
                generate_string_key="client_secret",
                exclude_punctuation=True,
            ),
        )

        # ECS Cluster
        cluster = ecs.Cluster(
            self,
            "Cluster",
            vpc=vpc,
            cluster_name="reddit-sentinel",
            container_insights_v2=ecs.ContainerInsights.DISABLED,  # Cost optimization
        )

        # Reference existing ECR repo (created by pipeline stack)
        ecr_repo = ecr.Repository.from_repository_name(
            self,
            "EcrRepo",
            repository_name="reddit-sentinel",
        )

        # Log group
        log_group = logs.LogGroup(
            self,
            "LogGroup",
            log_group_name="/ecs/reddit-sentinel",
            retention=logs.RetentionDays.ONE_WEEK,
            removal_policy=RemovalPolicy.DESTROY,
        )

        # ECS Fargate Service with ALB
        fargate_service = ecs_patterns.ApplicationLoadBalancedFargateService(
            self,
            "FargateService",
            cluster=cluster,
            service_name="reddit-sentinel-api",
            cpu=256,
            memory_limit_mib=512,
            desired_count=1,
            task_image_options=ecs_patterns.ApplicationLoadBalancedTaskImageOptions(
                image=ecs.ContainerImage.from_ecr_repository(ecr_repo, tag="latest"),
                container_port=8000,
                log_driver=ecs.LogDrivers.aws_logs(
                    stream_prefix="api",
                    log_group=log_group,
                ),
                environment={
                    "API_HOST": "0.0.0.0",
                    "API_PORT": "8000",
                    "SCORE_CACHE_TTL_HOURS": "48",
                    "LOG_LEVEL": "INFO",
                    "REDIS_URL": f"redis://{redis_cluster.attr_redis_endpoint_address}:6379/0",
                },
                secrets={
                    "REDDIT_CLIENT_ID": ecs.Secret.from_secrets_manager(
                        reddit_secrets, "client_id"
                    ),
                    "REDDIT_CLIENT_SECRET": ecs.Secret.from_secrets_manager(
                        reddit_secrets, "client_secret"
                    ),
                    "REDDIT_USER_AGENT": ecs.Secret.from_secrets_manager(
                        reddit_secrets, "user_agent"
                    ),
                },
            ),
            public_load_balancer=True,
            assign_public_ip=True,  # Public IP for internet access without NAT
            task_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
            security_groups=[ecs_sg],
        )

        # Health check
        fargate_service.target_group.configure_health_check(
            path="/v1/health",
            healthy_http_codes="200",
            interval=Duration.seconds(30),
            timeout=Duration.seconds(5),
        )

        # Auto-scaling (minimal for personal use)
        scaling = fargate_service.service.auto_scale_task_count(
            min_capacity=1,
            max_capacity=2,
        )
        scaling.scale_on_cpu_utilization(
            "CpuScaling",
            target_utilization_percent=80,
            scale_in_cooldown=Duration.seconds(300),
            scale_out_cooldown=Duration.seconds(60),
        )

        # Outputs
        CfnOutput(
            self,
            "ApiUrl",
            value=f"http://{fargate_service.load_balancer.load_balancer_dns_name}",
            description="API endpoint URL",
        )

        CfnOutput(
            self,
            "RedisEndpoint",
            value=redis_cluster.attr_redis_endpoint_address,
            description="Redis endpoint",
        )

        CfnOutput(
            self,
            "SecretsArn",
            value=reddit_secrets.secret_arn,
            description="ARN of Reddit API secrets (update in AWS Console)",
        )
