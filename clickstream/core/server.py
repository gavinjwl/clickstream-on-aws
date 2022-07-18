import gzip
import json
import os
import secrets
from typing import Callable

from fastapi.encoders import jsonable_encoder
import boto3
from fastapi import Depends, FastAPI, HTTPException, Request, Response, BackgroundTasks
from fastapi.exceptions import RequestValidationError
from fastapi.routing import APIRoute
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from models import Events


class GzipRequest(Request):
    async def body(self) -> bytes:
        if not hasattr(self, "_body"):
            body = await super().body()
            if "gzip" in self.headers.getlist("Content-Encoding"):
                body = gzip.decompress(body)
            self._body = body
        return self._body


class CustomRoute(APIRoute):
    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            request = GzipRequest(request.scope, request.receive)
            try:
                return await original_route_handler(request)
            except RequestValidationError as exc:
                body = await request.body()
                detail = {"errors": exc.errors(), "body": body.decode()}
                raise HTTPException(status_code=422, detail=detail)
        return custom_route_handler


app = FastAPI()
app.router.route_class = CustomRoute
security = HTTPBasic()

kinesis_stream_name = os.environ['KINESIS_STREAM_NAME']
write_key = os.environ['WRITE_KEY']


def authn(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, write_key)
    correct_password = secrets.compare_digest(credentials.password, "")
    return True if correct_username and correct_password else False


def processing(events: Events, request: Request, debug: bool):
    request_context = request.scope['aws.event']['requestContext']
    new_context = {
        'ip': request_context['identity']['sourceIp'],
        'userAgent': request_context['identity']['userAgent'],
    } if request.scope.get('aws.event') else dict()

    records = list()
    for event in events.batch:
        if event.context:
            new_context.update(event.context)
        event.context = new_context

        records.append({
            'Data': json.dumps(
                jsonable_encoder(event, exclude_none=True, exclude_unset=True)
            ).encode('utf-8'),
            'PartitionKey': event.messageId,
        })

    if debug:
        print(records)
    else:
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


@app.post("/v1/batch")
async def batch(
    events: Events, request: Request, background_tasks: BackgroundTasks,
    debug: bool = False,
    is_authn: bool = Depends(authn),
):
    if is_authn:
        background_tasks.add_task(processing, events, request, debug)
    return
