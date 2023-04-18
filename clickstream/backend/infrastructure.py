import os
from os import path

from aws_cdk import CfnOutput, Duration, NestedStack
from aws_cdk import aws_apigateway as aws_apigw
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_ecr_assets as ecr_assets
from aws_cdk import aws_ecs as ecs
from aws_cdk import aws_ecs_patterns as ecs_patterns
from aws_cdk import aws_kinesis as kinesis
from aws_cdk import aws_lambda
from aws_cdk import aws_logs as logs
from constructs import Construct


class EcsStack(NestedStack):

    def __init__(self, scope: Construct, id: str, vpc: ec2.IVpc, stream: kinesis.Stream, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        ecr_asset = ecr_assets.DockerImageAsset(
            self, 'DockerImageAsset',
            directory=path.join(os.path.dirname(__file__)),
        )

        cluster = ecs.Cluster(
            self, 'EcsCluster',
            vpc=vpc,
        )

        fargate_task = ecs.FargateTaskDefinition(
            self, "FargetTaskDefinition",
            cpu=1024,
            memory_limit_mib=2048,
        )
        fargate_task.add_container(
            "FargateContainer",
            image=ecs.ContainerImage.from_ecr_repository(ecr_asset.repository, tag=ecr_asset.image_tag),
            port_mappings=[ecs.PortMapping(container_port=8080)],
            environment={
                'KINESIS_STREAM_NAME': stream.stream_name,
                'WRITE_KEY': 'write_key',
            },
            logging=ecs.LogDrivers.aws_logs(
                stream_prefix='clickstream',
                log_retention=logs.RetentionDays.ONE_WEEK,
            ),
        )
        stream.grant_read_write(fargate_task.task_role)

        # TODO: enable custom domain name with ACM certificate
        fargate_service = ecs_patterns.ApplicationLoadBalancedFargateService(
            self, "FargateService",
            cluster=cluster,  # Required
            task_definition=fargate_task,
            desired_count=2,  # Default is 1
            public_load_balancer=True,  # Default is False
            # protocol='HTTPS',
            # certificate (Optional[ICertificate]) =None,
            # domain_name
            # domain_zone
            # redirect_http=True,
        )

        # Setup AutoScaling policy
        scaling_policy = fargate_service.service.auto_scale_task_count(
            min_capacity=2,
            max_capacity=10
        )
        scaling_policy.scale_on_cpu_utilization(
            "CpuScaling",
            target_utilization_percent=40,
            scale_in_cooldown=Duration.seconds(300),
            scale_out_cooldown=Duration.seconds(60),
        )

        CfnOutput(
            self, "LoadBalancerDNS",
            value=fargate_service.load_balancer.load_balancer_dns_name
        )


class ApiGatewayStack(NestedStack):
    def __init__(self, scope: Construct, id: str, stream: kinesis.Stream, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Log server used for parsing and transform
        clickstream_backend_function = aws_lambda.Function(
            self, id='ClickstreamBackendFunction',
            function_name='ClickstreamBackendFunction',
            code=aws_lambda.EcrImageCode.from_asset_image(
                directory=path.join(os.path.dirname(__file__)),
                file='lambda.dockerfile',
            ),
            handler=aws_lambda.Handler.FROM_IMAGE,
            runtime=aws_lambda.Runtime.FROM_IMAGE,
            memory_size=128,
            environment={
                'KINESIS_STREAM_NAME': stream.stream_name,
                'WRITE_KEY': 'write_key',
            },
            dead_letter_queue_enabled=True,
            timeout=Duration.seconds(30),
        )
        stream.grant_read_write(clickstream_backend_function)

        # Log API endpoint
        # ANY /*
        clickstream_backend_api = aws_apigw.LambdaRestApi(
            self, id='ClickstreamBackendAPI',
            rest_api_name='ClickstreamBackendAPI',
            handler=clickstream_backend_function,
            deploy_options=aws_apigw.StageOptions(
                throttling_rate_limit=20,
                throttling_burst_limit=10,
            ),
        )
