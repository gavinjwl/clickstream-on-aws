import os

from aws_cdk import App, Environment

from clickstream.stacks.provisioned_stack import ECSStack, RedshiftStreamingIngestionStack

app = App()

ecs_stack = ECSStack(
    app, 'ECSStack',
    env=Environment(
        account=os.environ.get("CDK_DEPLOY_ACCOUNT", os.environ["CDK_DEFAULT_ACCOUNT"]),
        region=os.environ.get("CDK_DEPLOY_REGION", os.environ["CDK_DEFAULT_REGION"])
    )
)

app.synth()
