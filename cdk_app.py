import os

from aws_cdk import App, Environment, Tags

from clickstream.stack import ProvisionedStack, ServerlessStack, VpcStack

app = App()

Tags.of(app).add('Project', 'Clickstream')

env = Environment(
    account=os.environ.get('CDK_DEPLOY_ACCOUNT', os.environ['CDK_DEFAULT_ACCOUNT']),
    region=os.environ.get('CDK_DEPLOY_REGION', os.environ['CDK_DEFAULT_REGION'])
)

VpcStack(app, 'Clickstream-Vpc', env=env)

ProvisionedStack(app, 'Clickstream', env=env)

ServerlessStack(app, 'Clickstream-Serverless', env=env)

app.synth()
