from aws_cdk import Duration, Stack
from aws_cdk.aws_cloudwatch import Dashboard, GraphWidget, PeriodOverride, Metric, SingleValueWidget, MathExpression, YAxisProps, Unit
from constructs import Construct
from aws_cdk.aws_apigateway import LambdaRestApi
from aws_cdk.aws_lambda import Function as LambdaFunction
from aws_cdk.aws_kinesis import Stream as KinesisStream


class DashboardStack(Stack):
    def __init__(self, scope: Construct, id: str,
                 clickstream_backend_api: LambdaRestApi,
                 clickstream_backend_function: LambdaFunction,
                 kinesis_stream: KinesisStream,
                 **kwargs):
        super().__init__(scope, id, **kwargs)

        #
        # CloudWatch Dashboard
        #
        dashboard = Dashboard(
            self, id='ClickstreamDashboard',
            dashboard_name='Clickstream',
            period_override=PeriodOverride.INHERIT,
            start='-PT3H',
        )

        # row 1
        dashboard.add_widgets(
            SingleValueWidget(
                title='BackendAPI',
                width=8, height=6,
                metrics=[
                    clickstream_backend_api.metric_latency(
                        label='Latency(p95)', statistic='p95',
                        period=Duration.minutes(1)
                    ),
                    clickstream_backend_api.metric_integration_latency(
                        label='IntegrationLatency(p95)', statistic='p95',
                        period=Duration.minutes(1)
                    ),
                    clickstream_backend_api.metric_count(
                        statistic='Sum',
                        period=Duration.minutes(1)
                    ),
                    clickstream_backend_api.metric_client_error(
                        statistic='Sum',
                        period=Duration.minutes(1)
                    ),
                    clickstream_backend_api.metric_server_error(
                        statistic='Sum',
                        period=Duration.minutes(1)
                    ),
                ],
            ),
            SingleValueWidget(
                title='BackendFunction',
                width=8, height=6,
                metrics=[
                    clickstream_backend_function.metric_invocations(
                        statistic='Sum',
                        period=Duration.minutes(1)
                    ),
                    clickstream_backend_function.metric_duration(
                        label='Duration(p95)', statistic='p95',
                        period=Duration.minutes(1)
                    ),
                    clickstream_backend_function.metric_throttles(
                        statistic='Sum',
                        period=Duration.minutes(1)
                    ),
                    clickstream_backend_function.metric_errors(
                        statistic='Sum',
                        period=Duration.minutes(1)
                    ),
                ],
            ),
            SingleValueWidget(
                title='KinesisStream',
                width=8, height=6,
                metrics=[
                    kinesis_stream.metric_incoming_records(
                        statistic='sum',
                        period=Duration.minutes(1)
                    ),
                    kinesis_stream.metric_get_records(
                        statistic='sum',
                        period=Duration.minutes(1)
                    ),
                    kinesis_stream.metric_put_records_latency(
                        label='PutRecords.Latency(p95)', statistic='p95',
                        period=Duration.minutes(1)
                    ),
                    kinesis_stream.metric_get_records_latency(
                        label='GetRecords.Latency(p95)', statistic='p95',
                        period=Duration.minutes(1)
                    )
                ]
            )
        )

        metric_compute_capacity = Metric(
            namespace='AWS/Redshift-Serverless',
            metric_name='ComputeCapacity',
            dimensions_map={
                'Workgroup': 'clickstream-workgroup'
            },
            statistic='sum',
            period=Duration.minutes(1),
            unit=Unit.COUNT,
        )
        metric_compute_seconds = Metric(
            namespace='AWS/Redshift-Serverless',
            metric_name='ComputeSeconds',
            dimensions_map={
                'Workgroup': 'clickstream-workgroup'
            },
            statistic='sum',
            period=Duration.minutes(1),
            unit=Unit.SECONDS,
        )

        compute_cost = MathExpression(
            label='ComputeCost',
            expression='sum_compute_seconds / 60 / 60 * 0.494',
            using_metrics={
                'sum_compute_seconds': metric_compute_seconds
            },
            period=Duration.minutes(1)
        )

        # row 2
        dashboard.add_widgets(
            GraphWidget(
                title='RPU resource',
                width=12, height=6,
                left=[metric_compute_capacity],
                left_y_axis=YAxisProps(label='RPU', show_units=False),
                right=[metric_compute_seconds],
                right_y_axis=YAxisProps(label='Seconds', show_units=False)
            ),
            GraphWidget(
                title='RPU cost',
                width=12, height=6,
                left=[metric_compute_seconds],
                left_y_axis=YAxisProps(label='Seconds', show_units=False),
                right=[compute_cost],
                right_y_axis=YAxisProps(label='USD', show_units=False)
            )
        )
