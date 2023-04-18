from aws_cdk import Duration, NestedStack
from aws_cdk import aws_kinesis
from constructs import Construct


class KinesisStack(NestedStack):
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        self.kinesis_stream = aws_kinesis.Stream(
            self, id='KinesisStream',
            stream_name='clickstream_kinesis_stream',
            stream_mode=aws_kinesis.StreamMode.ON_DEMAND,
            retention_period=Duration.days(7),
        )
