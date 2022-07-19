'''
Scheduled invoke `Refresh MV`
'''
import os
import boto3

REDSHIFT_NAME = os.environ['REDSHIFT_NAME']


def lambda_handler(event, context):
    print(event)

    client = boto3.client('redshift-data')
    response = client.batch_execute_statement(
        WorkgroupName=REDSHIFT_NAME,
        Database='dev',
        Sqls=[
            'SET enable_case_sensitive_identifier TO true;',
            f'REFRESH MATERIALIZED VIEW clickstream.mv_kinesisSource;',
        ],
        StatementName=f'REFRESH-mv_kinesisSource',
        WithEvent=True,
    )

    print(response)
    return
