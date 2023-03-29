from aws_cdk import CfnOutput, CfnParameter, CfnTag, Duration, Stack
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_ecs as ecs
from aws_cdk import aws_iam as iam
from aws_cdk import aws_kinesis as kinesis
from aws_cdk import aws_redshift as redshift
from constructs import Construct


class RedshiftStreamingIngestionStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        master_user_password = CfnParameter(self, id='MasterUserPassword', no_echo=True)

        vpc = ec2.Vpc.from_lookup(self, 'vpc', vpc_id=self.node.try_get_context('vpc-id'))

        # Redshift role
        redshift_role = iam.Role(
            self, id='ClickstreamRedshiftRole',
            role_name='ClickstreamRedshiftRole',
            assumed_by=iam.ServicePrincipal('redshift.amazonaws.com'),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    'AmazonRedshiftAllCommandsFullAccess')
            ]
        )

        # RedshiftSubnetGroup
        cfn_cluster_subnet_group = redshift.CfnClusterSubnetGroup(
            self, "ClickstreamRedshiftSubnetGroup",
            description="Clickstream redshift subnet group",
            subnet_ids=vpc.select_subnets(
                subnet_type=ec2.SubnetType.PRIVATE_WITH_NAT
            ),

            # the properties below are optional
            tags=[
                CfnTag(
                    key="Name",
                    value="ClickstreamRedshiftSubnetGroup"
                ),
                CfnTag(
                    key="clickstream",
                    value="true"
                )
            ]
        )

        # Redshift
        self.cfn_cluster = redshift.CfnCluster(
            self, "ClickstreamRedshift",
            db_name="clickstream",
            master_username="awsuser",
            master_user_password=master_user_password.value_as_string,
            node_type="ra3.xlplus",
            number_of_nodes=2,

            # the properties below are optional
            availability_zone_relocation=True,
            cluster_subnet_group_name=cfn_cluster_subnet_group.ref,
            encrypted=True,
            enhanced_vpc_routing=True,
            iam_roles=[
                redshift_role.role_arn
            ],
            tags=[
                CfnTag(
                    key="Name",
                    value="ClickstreamRedshift"
                ),
                CfnTag(
                    key="clickstream",
                    value="true"
                )
            ],
            # vpc_security_group_ids=["vpcSecurityGroupIds"]
        )

        # Streaming
        self.kinesis_stream = kinesis.Stream(
            self, id='ClickstreamKinesisStream',
            stream_name='ClickstreamKinesisStream',
            stream_mode=kinesis.StreamMode.PROVISIONED,
            retention_period=Duration.days(7),
            shard_count=2,
        )
        self.kinesis_stream.grant_read(redshift_role)
