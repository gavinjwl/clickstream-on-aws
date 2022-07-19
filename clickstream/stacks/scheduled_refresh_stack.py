import os

from aws_cdk.aws_redshiftserverless import CfnWorkgroup
from aws_cdk.aws_iam import Role
from aws_cdk import Stack, aws_lambda
from aws_cdk.aws_events import Rule, Schedule
from aws_cdk.aws_events_targets import LambdaFunction as LambdaTask
from constructs import Construct


class ScheduledRefreshStack(Stack):
    def __init__(self, scope: Construct, id: str,
                 workgroup: CfnWorkgroup,
                 clickstream_redshift_role: Role,
                 lambda_code_dir: str,
                 **kwargs):
        super().__init__(scope, id, **kwargs)

        #
        # Scheduled refresh MV
        #
        refresh_mv_function = aws_lambda.Function(
            self, id='RefreshMvFunction',
            function_name='RefreshMvFunction',
            code=aws_lambda.EcrImageCode.from_asset_image(lambda_code_dir),
            handler=aws_lambda.Handler.FROM_IMAGE,
            runtime=aws_lambda.Runtime.FROM_IMAGE,
            memory_size=128,
            role=clickstream_redshift_role,
            environment={
                'REDSHIFT_NAME': workgroup.workgroup_name,
            }
        )

        Rule(
            self, id='RedshiftRefreshRule',
            rule_name='RedshiftRefreshRule',
            schedule=Schedule.cron(minute='*'),
            targets=[
                LambdaTask(refresh_mv_function),
            ]
        )
