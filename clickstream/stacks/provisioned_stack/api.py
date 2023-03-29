
from aws_cdk import (
    aws_ec2 as ec2,
    aws_ecs as ecs,
    CfnOutput, Duration, Stack,
    aws_ecs_patterns as ecs_patterns,
)
from constructs import Construct


class ECSStack(Stack):
    '''
    https://github.com/aws-samples/aws-cdk-examples/tree/master/python/ecs/fargate-load-balanced-service
    https://github.com/aws-samples/aws-cdk-examples/tree/master/python/ecs/fargate-service-with-autoscaling
    '''

    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        vpc = ec2.Vpc.from_lookup(self, 'vpc', vpc_id=self.node.try_get_context('vpc-id'))

        cluster = ecs.Cluster(
            self, 'EcsCluster',
            vpc=vpc,
            cluster_name='clickstream-ecs-cluster',
        )

        fargate_task = ecs.FargateTaskDefinition(
            self, "FargetTaskDefinition",
            cpu=256,
            memory_limit_mib=512,
        )
        fargate_task.add_container(
            "FargateContainer",
            image=ecs.ContainerImage.from_registry("amazon/amazon-ecs-sample"),
            port_mappings=[ecs.PortMapping(container_port=80)],
        )

        fargate_service = ecs_patterns.ApplicationLoadBalancedFargateService(
            self, "FargateService",
            cluster=cluster,  # Required
            service_name='clickstream-ecs-service',
            task_definition=fargate_task,
            desired_count=1,  # Default is 1
            public_load_balancer=True,  # Default is False
            # redirect_http=True,
        )

        # Setup AutoScaling policy
        scaling = fargate_service.service.auto_scale_task_count(
            max_capacity=10
        )
        scaling.scale_on_cpu_utilization(
            "CpuScaling",
            policy_name="clickstream-ecs-service-cpu-scaling",
            target_utilization_percent=40,
            scale_in_cooldown=Duration.seconds(300),
            scale_out_cooldown=Duration.seconds(60),
        )

        CfnOutput(
            self, "LoadBalancerDNS",
            value=fargate_service.load_balancer.load_balancer_dns_name
        )
