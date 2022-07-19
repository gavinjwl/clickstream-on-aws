import os
from aws_cdk import App

from clickstream.stacks import CoreStack, DashboardStack, ScheduledRefreshStack

app = App()

core_stack = CoreStack(
    app, 'CoreStack',
    os.path.join(
        os.path.dirname(os.path.realpath(__file__)), 'clickstream', 'core'
    )
)

scheduled_refresh_stack = ScheduledRefreshStack(
    app, 'ScheduledRefreshStack',
    core_stack.workgroup,
    core_stack.clickstream_redshift_role,
    os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        'clickstream', 'scheduled_refresh'
    )
)

dashboard_stack = DashboardStack(
    app, 'DashboardStack',
    core_stack.clickstream_backend_api,
    core_stack.clickstream_backend_function,
    core_stack.kinesis_stream,
)

app.synth()
