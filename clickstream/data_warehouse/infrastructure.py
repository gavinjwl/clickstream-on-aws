from aws_cdk import CfnTag, NestedStack
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_iam as iam
from aws_cdk import aws_kinesis as kinesis
from aws_cdk import aws_logs as logs
from aws_cdk import aws_redshift as redshift
from aws_cdk import aws_redshiftserverless as redshiftserverless
from aws_cdk import custom_resources as cr
from constructs import Construct


class RedshiftStack(NestedStack):
    def __init__(self, scope: Construct, id: str, vpc: ec2.IVpc, stream: kinesis.Stream, redshift_password: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        role = iam.Role(
            self, id='RedshiftRole',
            assumed_by=iam.ServicePrincipal('redshift.amazonaws.com'),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    'AmazonRedshiftAllCommandsFullAccess')
            ]
        )
        stream.grant_read_write(role)

        selection = map(
            lambda subnet: subnet.subnet_id,
            vpc.private_subnets
        )
        subnet_group = redshift.CfnClusterSubnetGroup(
            self, "SubnetGroup",
            description="Clickstream redshift subnet group",
            subnet_ids=list(selection),
            tags=[
                CfnTag(key="Project", value="Clickstream")
            ],
        )

        cluster = redshift.CfnCluster(
            self, "Redshift",

            # required properties
            cluster_identifier='clickstream',
            # cluster_type="multi-node",
            # number_of_nodes=2,
            cluster_type="single-node",
            number_of_nodes=1,
            db_name='dev',
            master_username="awsuser",
            master_user_password=redshift_password,
            node_type="ra3.xlplus",

            # the properties below are optional
            publicly_accessible=False,
            availability_zone_relocation=True,
            cluster_subnet_group_name=subnet_group.ref,
            encrypted=True,
            enhanced_vpc_routing=True,
            iam_roles=[
                role.role_arn
            ],
            tags=[
                CfnTag(key="Project", value="Clickstream")
            ],
        )

        # AwsCustomResource for make role as default in Redshift cluster
        cr.AwsCustomResource(
            self, "RedshiftDefaultRole",
            policy=cr.AwsCustomResourcePolicy.from_sdk_calls(
                resources=[f'arn:aws:redshift:{self.region}:{self.account}:cluster:{cluster.ref}']
            ),
            log_retention=logs.RetentionDays.ONE_WEEK,
            on_create={
                "service": "Redshift",
                "action": "modifyClusterIamRoles",
                "parameters": {
                    "ClusterIdentifier": cluster.ref,
                    "DefaultIamRoleArn": role.role_arn,
                },
                "physical_resource_id": cr.PhysicalResourceId.of("RedshiftDefaultRole")
            },
            on_update={
                "service": "Redshift",
                "action": "modifyClusterIamRoles",
                "parameters": {
                    "ClusterIdentifier": cluster.ref,
                    "DefaultIamRoleArn": role.role_arn,
                },
                "physical_resource_id": cr.PhysicalResourceId.of("RedshiftDefaultRole")
            },
        )


class RedshiftServerlessStack(NestedStack):
    def __init__(self, scope: Construct, id: str, vpc: ec2.IVpc, stream: kinesis.Stream, redshift_password: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        selection = map(
            lambda subnet: subnet.subnet_id,
            vpc.private_subnets
        )
        subnet_ids = list(selection)

        default_security_group = ec2.SecurityGroup.from_lookup_by_name(
            self, id='DefaultSecurityGroup',
            security_group_name='default',
            vpc=vpc,
        )

        # Data warehouse
        redshift_service_role = iam.Role(
            self, id='ClickstreamRedshiftServiceRole',
            assumed_by=iam.ServicePrincipal('redshift.amazonaws.com'),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    'AmazonRedshiftAllCommandsFullAccess')
            ]
        )
        stream.grant_read(redshift_service_role)

        namespace = redshiftserverless.CfnNamespace(
            self, id='RedshiftServerlessNamespace',
            namespace_name='clickstream-namespace',
            default_iam_role_arn=redshift_service_role.role_arn,
            iam_roles=[redshift_service_role.role_arn],
            admin_username="awsuser",
            admin_user_password=redshift_password,
            log_exports=['userlog', 'connectionlog', 'useractivitylog'],
        )
        workgroup = redshiftserverless.CfnWorkgroup(
            self, id='RedshiftServerlessWorkgroup',
            namespace_name=namespace.namespace_name,
            workgroup_name='clickstream-workgroup',
            base_capacity=8,
            subnet_ids=subnet_ids,
            security_group_ids=[default_security_group.security_group_id],
            publicly_accessible=False,
            enhanced_vpc_routing=False,
        )
        workgroup.add_dependency(namespace)
