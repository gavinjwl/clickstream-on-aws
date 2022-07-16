'''
Scheduled invoke `Refresh MV`
'''
import os
import boto3

is_serverless = os.environ['REDSHIFT_MODE'].lower() == 'serverless'

redshift_name = os.environ['REDSHIFT_NAME']

redshift_database = os.environ['REDSHIFT_DATABASE']
clickstream_schema = os.environ['CLICKSTREAM_SCHEMA']
clickstream_mv = os.environ['CLICKSTREAM_MV']


def lambda_handler(event, context):
    print(event)

    client = boto3.client('redshift-data')
    api_parameters = serverless_parameters() if is_serverless else provisioned_parameters()
    response = client.batch_execute_statement(**api_parameters)

    print(response)
    return

def serverless_parameters():
    return {
        'WorkgroupName': redshift_name,
        'Database': redshift_database,
        'Sqls': [
            'SET enable_case_sensitive_identifier TO true;',
            f'REFRESH MATERIALIZED VIEW {clickstream_schema}.{clickstream_mv};',
        ],
        'StatementName': f'REFRESH-{clickstream_mv}',
        'WithEvent': True,
    }

def provisioned_parameters():
    return {
        'ClusterIdentifier': redshift_name,
        'Database': redshift_database,
        'DbUser': os.environ['REDSHIFT_USER'],
        'Sqls': [
            'SET enable_case_sensitive_identifier TO true;',
            f'REFRESH MATERIALIZED VIEW {clickstream_schema}.{clickstream_mv};',
        ],
        'StatementName': f'REFRESH-{clickstream_mv}',
        'WithEvent': True,
    }