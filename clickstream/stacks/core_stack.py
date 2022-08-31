from aws_cdk import CfnOutput, CfnParameter, Duration, Stack
from aws_cdk import aws_apigateway as aws_apigw
from aws_cdk import aws_iam, aws_kinesis, aws_lambda, aws_redshiftserverless
from constructs import Construct


class CoreStack(Stack):
    def __init__(self, scope: Construct, id: str, lambda_code_dir: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        write_key = CfnParameter(self, id='WriteKey', no_echo=True)

        subnet_ids = CfnParameter(
            self, id='RedshiftServerlessSubnetIds',
            type='List<AWS::EC2::Subnet::Id>',
        )
        security_group_ids = CfnParameter(
            self, id='RedshiftServerlessSecurityGroupIds',
            type='List<AWS::EC2::SecurityGroup::Id>',
        )

        # https://docs.aws.amazon.com/apigateway/latest/developerguide/limits.html#apigateway-account-level-limits-table
        rate_limit = CfnParameter(
            self, id='RateLimit', type='Number', default='20', min_value=1, max_value=10000,)
        burst_limit = CfnParameter(
            self, id='BurstLimit', type='Number', default='10', min_value=1, max_value=5000,)

        # Data warehouse
        redshift_service_role = aws_iam.Role(
            self, id='ClickstreamRedshiftServiceRole',
            role_name='ClickstreamRedshiftServiceRole',
            assumed_by=aws_iam.ServicePrincipal('redshift.amazonaws.com'),
            managed_policies=[
                aws_iam.ManagedPolicy.from_aws_managed_policy_name(
                    'AmazonRedshiftAllCommandsFullAccess')
            ]
        )
        self.namespace = aws_redshiftserverless.CfnNamespace(
            self, id='ClickstreamNamespace',
            namespace_name='clickstream-namespace',
            default_iam_role_arn=redshift_service_role.role_arn,
            iam_roles=[redshift_service_role.role_arn],
            log_exports=['userlog', 'connectionlog', 'useractivitylog'],
        )
        self.workgroup = aws_redshiftserverless.CfnWorkgroup(
            self, id='ClickstreamWorkgroup',
            namespace_name=self.namespace.namespace_name,
            workgroup_name='clickstream-workgroup',
            base_capacity=32,
            subnet_ids=subnet_ids.value_as_list,
            security_group_ids=security_group_ids.value_as_list,
            publicly_accessible=False,
            enhanced_vpc_routing=False,
        )
        self.workgroup.add_depends_on(self.namespace)

        # role used by MV refresh statement
        self.clickstream_redshift_role = aws_iam.Role(
            self, id='ClickstreamRedshiftRole',
            role_name='ClickstreamRedshiftRole',
            assumed_by=aws_iam.ServicePrincipal('lambda.amazonaws.com'),
            managed_policies=[
                aws_iam.ManagedPolicy.from_aws_managed_policy_name(
                    'service-role/AWSLambdaBasicExecutionRole')
            ],
        )
        self.clickstream_redshift_role.add_to_policy(aws_iam.PolicyStatement(
            effect=aws_iam.Effect.ALLOW,
            actions=[
                'redshift-data:BatchExecuteStatement',
                'redshift-data:ExecuteStatement',
                'redshift-data:CancelStatement',
                'redshift-data:ListStatements',
                'redshift-data:GetStatementResult',
                'redshift-data:DescribeStatement',
                'redshift-data:ListDatabases',
                'redshift-data:ListSchemas',
                'redshift-data:ListTables',
                'redshift-data:DescribeTable',
                'redshift-serverless:GetCredentials',
            ],
            resources=['*'],
        ))

        # Streaming
        self.kinesis_stream = aws_kinesis.Stream(
            self, id='ClickstreamKinesisStream',
            stream_name='ClickstreamKinesisStream',
            stream_mode=aws_kinesis.StreamMode.ON_DEMAND,
            retention_period=Duration.days(7),
        )

        self.kinesis_stream.grant_read(redshift_service_role)

        # Log server used for parsing and transform
        self.clickstream_backend_function = aws_lambda.Function(
            self, id='ClickstreamBackendFunction',
            function_name='ClickstreamBackendFunction',
            code=aws_lambda.EcrImageCode.from_asset_image(lambda_code_dir),
            handler=aws_lambda.Handler.FROM_IMAGE,
            runtime=aws_lambda.Runtime.FROM_IMAGE,
            memory_size=128,
            environment={
                'KINESIS_STREAM_NAME': self.kinesis_stream.stream_name,
                'WRITE_KEY': write_key.value_as_string,
            },
            dead_letter_queue_enabled=True,
            timeout=Duration.seconds(30),
        )
        self.kinesis_stream.grant_read_write(self.clickstream_backend_function)

        # Log API endpoint
        # ANY /*
        self.clickstream_backend_api = aws_apigw.LambdaRestApi(
            self, id='ClickstreamBackendAPI',
            rest_api_name='ClickstreamBackendAPI',
            handler=self.clickstream_backend_function,
            deploy_options=aws_apigw.StageOptions(
                throttling_rate_limit=rate_limit.value_as_number,
                throttling_burst_limit=burst_limit.value_as_number,
            ),
        )

        # Outputs
        CfnOutput(
            self, id='ClickstreamRole',
            value=self.clickstream_redshift_role.role_name
        )
