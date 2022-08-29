import json
from typing import Union

from fastapi import APIRouter, BackgroundTasks, Request
from kinesis_producer import produce
from models import BatchEvent

from routers.commons import CustomRoute

router = APIRouter(route_class=CustomRoute)


@router.post("/v1/batch", tags=['analytics_python'])
async def batch(
    event: Union[BatchEvent, str], request: Request, background_tasks: BackgroundTasks
):
    '''
    Compatible with https://github.com/segmentio/analytics-python
    '''
    if isinstance(event, str):
        event = BatchEvent.parse_obj(json.loads(event))
    if isinstance(event, BatchEvent):
        background_tasks.add_task(produce, event.batch, request)
    return
