import json
from typing import List

import boto3
from fastapi import Request
from fastapi.encoders import jsonable_encoder

from env import kinesis_stream_name
from models import Event


def produce(events: List[Event], request: Request):
    if request.scope.get('aws.event'):
        request_context = request.scope['aws.event']['requestContext']
        new_context = {
            'ip': request_context['identity']['sourceIp'],
            'userAgent': request_context['identity']['userAgent'],
        }
    else:
        new_context = dict()

    records = list()
    for event in events:
        if event.context:
            new_context.update(event.context)
        event.context = new_context

        records.append({
            'Data': json.dumps(
                jsonable_encoder(event, exclude_none=True, exclude_unset=True)
            ).encode('utf-8'),
            'PartitionKey': event.messageId,
        })

    if kinesis_stream_name:
        kinesis_client = boto3.client('kinesis')
        response = kinesis_client.put_records(
            Records=records,
            StreamName=kinesis_stream_name
        )
        print(json.dumps({
            'FailedRecordCount': response['FailedRecordCount'],
            'SuccessedRecordCount': len(response['Records']),
            'EncryptionType': response['EncryptionType'],
            'ResponseMetadata': response['ResponseMetadata'],
        }))
        # TODO response FailedRecordCount handle
    else:
        print(records)
