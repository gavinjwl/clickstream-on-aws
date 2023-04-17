import os

from aws_cdk import App, Environment, Tags

from clickstream.stack import ProvisionedStack
# from clickstream.stack import ServerlessStack

app = App()

Tags.of(app).add('Project', 'Clickstream')

env = Environment(
    account=os.environ.get('CDK_DEPLOY_ACCOUNT', os.environ['CDK_DEFAULT_ACCOUNT']),
    region=os.environ.get('CDK_DEPLOY_REGION', os.environ['CDK_DEFAULT_REGION'])
)

ProvisionedStack(app, 'Clickstream', env=env)

# ServerlessStack(app, 'Clickstream-Serverless')

app.synth()
