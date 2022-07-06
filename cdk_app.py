import os

from aws_cdk import App, CfnParameter, Duration, Stack
from aws_cdk import aws_apigateway as aws_apigw
from aws_cdk import aws_iam, aws_kinesis, aws_lambda
from constructs import Construct
from aws_cdk.aws_events import Rule, Schedule
from aws_cdk.aws_events_targets import LambdaFunction as LambdaTask


class ClickstreamStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        write_key = CfnParameter(self, id='WriteKey',)

        redshift_mode = CfnParameter(
            self, id='RedshiftMode',
            allowed_values=['provisioned', 'serverless'])
        redshift_name = CfnParameter(
            self, id='RedshiftName',
            description='please input redshift_cluster_identifier if provisioned, or redshift_workgroup_name if serverless')

        redshift_database = CfnParameter(self, id='RedshiftDatabase',)
        kinesis_schema = CfnParameter(self, id='KinesisSchema',)
        clickstream_schema = CfnParameter(self, id='ClickstreamSchema',)
        clickstream_mv = CfnParameter(
            self, id='ClickstreamMaterializedView',
            default='mv_kinesisSource')

        #
        # Resources
        #

        kinesis_stream = aws_kinesis.Stream(
            self, id='ClickstreamKinesisStream',
            stream_name='ClickstreamKinesisStream',
            stream_mode=aws_kinesis.StreamMode.ON_DEMAND,
            retention_period=Duration.days(7),
        )

        clickstream_backend_function = aws_lambda.Function(
            self, id='ClickstreamBackendFunction',
            function_name='ClickstreamBackendFunction',
            code=aws_lambda.EcrImageCode.from_asset_image(
                directory=os.path.join(
                    os.path.dirname(os.path.realpath(__file__)), 'clickstream'
                )),
            handler=aws_lambda.Handler.FROM_IMAGE,
            runtime=aws_lambda.Runtime.FROM_IMAGE,
            memory_size=128,
            environment={
                'KINESIS_STREAM_NAME': kinesis_stream.stream_name,
                'WRITE_KEY': write_key.value_as_string,
            },
            reserved_concurrent_executions=10,
            timeout=Duration.seconds(30),
        )

        kinesis_stream.grant_read_write(clickstream_backend_function)

        # ANY /*
        aws_apigw.LambdaRestApi(
            self, id='ClickstreamBackendAPI',
            rest_api_name='ClickstreamBackendAPI',
            handler=clickstream_backend_function,
            deploy_options=aws_apigw.StageOptions(
                throttling_rate_limit=1,
                throttling_burst_limit=1,
            ),
        )

        redshift_clickstream_role = aws_iam.Role(
            self, id='ClickstreamRedshiftRole',
            role_name='ClickstreamRedshiftRole',
            assumed_by=aws_iam.ServicePrincipal('lambda.amazonaws.com'),
            managed_policies=[
                aws_iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole")
            ],
        )

        redshift_clickstream_role.add_to_policy(aws_iam.PolicyStatement(
            effect=aws_iam.Effect.ALLOW,
            actions=[
                "redshift-data:BatchExecuteStatement",
                "redshift-data:ExecuteStatement",
                "redshift-data:CancelStatement",
                "redshift-data:ListStatements",
                "redshift-data:GetStatementResult",
                "redshift-data:DescribeStatement",
                "redshift-data:ListDatabases",
                "redshift-data:ListSchemas",
                "redshift-data:ListTables",
                "redshift-data:DescribeTable",
                "redshift:GetClusterCredentials" if redshift_mode == 'provisioned' else "redshift-serverless:GetCredentials",
            ],
            resources=["*"],
        ))

        refresh_mv_function = aws_lambda.Function(
            self, id='ClickstreamRefreshMvFunction',
            function_name='ClickstreamRefreshMvFunction',
            code=aws_lambda.EcrImageCode.from_asset_image(
                directory=os.path.join(
                    os.path.dirname(os.path.realpath(__file__)),
                    'refresh_mv_function',
                )),
            handler=aws_lambda.Handler.FROM_IMAGE,
            runtime=aws_lambda.Runtime.FROM_IMAGE,
            memory_size=128,
            role=redshift_clickstream_role,
            environment={
                'REDSHIFT_MODE': redshift_mode.value_as_string,
                'REDSHIFT_NAME': redshift_name.value_as_string,
                'REDSHIFT_USER': f'IAMR:{redshift_clickstream_role.role_name}',
                'REDSHIFT_DATABASE': redshift_database.value_as_string,
                'CLICKSTREAM_SCHEMA': clickstream_schema.value_as_string,
                'CLICKSTREAM_MV': clickstream_mv.value_as_string,
            }
        )

        refresh_rule = Rule(
            self, id='ClickstreamRedshiftRefreshRule',
            rule_name='ClickstreamRedshiftRefreshRule',
            schedule=Schedule.cron(minute='*'),
            targets=[
                LambdaTask(refresh_mv_function),
            ]
        )


app = App()

ClickstreamStack(app, 'ClickstreamStack')

app.synth()
