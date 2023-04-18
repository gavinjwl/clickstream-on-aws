from aws_cdk import CfnParameter, Stack
from aws_cdk import aws_ec2 as ec2

from clickstream.backend.infrastructure import ApiGatewayStack, EcsStack
from clickstream.data_warehouse.infrastructure import RedshiftServerlessStack, RedshiftStack
from clickstream.streaming.infrastructure import KinesisStack


class ProvisionedStack(Stack):
    def __init__(self, scope: Stack, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        # The code that defines your stack goes here

        redshift_password = CfnParameter(
            self, id='RedshiftPassword', min_length=8, max_length=64, no_echo=True,
            description='''
Must be 8-64 characters long. Must contain at least one uppercase letter, one lowercase letter and one number. Can be any printable ASCII character except “/”, ““”, or “@”.
            '''
        )

        vpc = ec2.Vpc.from_lookup(self, 'vpc', vpc_id=self.node.try_get_context('vpc-id'))

        kinesis_stack = KinesisStack(self, 'Kinesis')

        EcsStack(self, 'Ecs', vpc=vpc, stream=kinesis_stack.kinesis_stream)

        RedshiftStack(self, 'Redshift', vpc=vpc, stream=kinesis_stack.kinesis_stream,
                      redshift_password=redshift_password.value_as_string)


class ServerlessStack(Stack):
    def __init__(self, scope: Stack, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        # The code that defines your stack goes here

        redshift_password = CfnParameter(
            self, id='RedshiftPassword', min_length=8, max_length=64, no_echo=True,
            description='''
Must be 8-64 characters long. Must contain at least one uppercase letter, one lowercase letter and one number. Can be any printable ASCII character except “/”, ““”, or “@”.
            '''
        )

        vpc = ec2.Vpc.from_lookup(self, 'vpc', vpc_id=self.node.try_get_context('vpc-id'))

        kinesis_stack = KinesisStack(self, 'Kinesis')

        ApiGatewayStack(self, 'ApiGateway', stream=kinesis_stack.kinesis_stream)

        RedshiftServerlessStack(self, 'RedshiftServerless', vpc=vpc, stream=kinesis_stack.kinesis_stream,
                                redshift_password=redshift_password.value_as_string)
