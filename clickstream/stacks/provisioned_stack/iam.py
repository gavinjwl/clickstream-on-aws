from aws_cdk import CfnOutput, CfnParameter, Duration, Stack
from aws_cdk import aws_apigateway as aws_apigw
from aws_cdk import aws_redshift as redshift
from aws_cdk import aws_iam, aws_kinesis, aws_lambda, aws_redshiftserverless
from constructs import Construct


class IAMStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        # Data warehouse
        self.redshift_service_role = aws_iam.Role(
            self, id='ClickstreamRedshiftRole',
            role_name='ClickstreamRedshiftRole',
            assumed_by=aws_iam.ServicePrincipal('redshift.amazonaws.com'),
            managed_policies=[
                aws_iam.ManagedPolicy.from_aws_managed_policy_name(
                    'AmazonRedshiftAllCommandsFullAccess')
            ]
        )
