from aws_cdk import Duration, Stack
from aws_cdk.aws_cloudwatch import Dashboard, GraphWidget, PeriodOverride, Metric, SingleValueWidget, MathExpression, YAxisProps
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
            period_override=PeriodOverride.AUTO,
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
                    ),
                    clickstream_backend_api.metric_integration_latency(
                        label='IntegrationLatency(p95)', statistic='p95',
                    ),
                    clickstream_backend_api.metric_count(
                        statistic='Sum',
                    ),
                    clickstream_backend_api.metric_client_error(
                        statistic='Sum',
                    ),
                    clickstream_backend_api.metric_server_error(
                        statistic='Sum',
                    ),
                ],
            ),
            SingleValueWidget(
                title='BackendFunction',
                width=8, height=6,
                metrics=[
                    clickstream_backend_function.metric_invocations(
                        statistic='Sum',
                    ),
                    clickstream_backend_function.metric_duration(
                        label='Duration(p95)', statistic='p95',
                    ),
                    clickstream_backend_function.metric_throttles(
                        statistic='Sum',
                    ),
                    clickstream_backend_function.metric_errors(
                        statistic='Sum',
                    ),
                ],
            ),
            SingleValueWidget(
                title='KinesisStream',
                width=8, height=6,
                metrics=[
                    kinesis_stream.metric_put_records_success(
                        statistic='sum'),
                    kinesis_stream.metric_get_records_success(
                        statistic='sum'),
                    kinesis_stream.metric_put_records_latency(
                        label='PutRecords.Latency(p95)', statistic='p95',
                    ),
                    kinesis_stream.metric_get_records_latency(
                        label='PutRecords.Latency(p95)', statistic='p95',
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
        )
        metric_compute_seconds = Metric(
            namespace='AWS/Redshift-Serverless',
            metric_name='ComputeSeconds',
            dimensions_map={
                'Workgroup': 'clickstream-workgroup'
            },
            statistic='sum',
        )
        metric_data_storage = Metric(
            namespace='AWS/Redshift-Serverless',
            metric_name='DataStorage',
            dimensions_map={
                'Namespace': 'clickstream-namespace'
            },
            statistic='sum',
        )

        compute_cost = MathExpression(
            label='ComputeCost',
            expression='sum_compute_seconds / 60 / 60 * 0.494',
            using_metrics={
                'sum_compute_seconds': metric_compute_seconds
            }
        )
        storage_cost = MathExpression(
            label='StorageCost',
            expression='sum_data_storage / 1024 * 0.0261',
            using_metrics={
                'sum_data_storage': metric_data_storage
            }
        )

        # row 2
        dashboard.add_widgets(
            GraphWidget(
                title='RedshiftServerless - Compute',
                width=12, height=6,
                left=[metric_compute_capacity, metric_compute_seconds],
                right=[compute_cost],
                right_y_axis=YAxisProps(label='PerComputeCost (USD)')
            ),
            GraphWidget(
                title='RedshiftServerless - Storage',
                width=12, height=6,
                left=[metric_data_storage],
                right=[storage_cost],
                right_y_axis=YAxisProps(label='CurrentStorageCost (USD)')
            )
        )
