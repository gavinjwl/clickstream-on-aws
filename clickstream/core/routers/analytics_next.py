import json
from typing import Union

from fastapi import APIRouter, BackgroundTasks, Request
from kinesis_producer import produce
from models import BatchEvent, Event

from routers.commons import CustomRoute

router = APIRouter(route_class=CustomRoute)


@router.post("/i", tags=['analytics_next'])
@router.post("/t", tags=['analytics_next'])
@router.post("/g", tags=['analytics_next'])
@router.post("/a", tags=['analytics_next'])
@router.post("/p", tags=['analytics_next'])
async def single_event(
    event: Union[Event, str], request: Request, background_tasks: BackgroundTasks,
):
    '''
    Compatible with https://github.com/segmentio/analytics-next
    '''
    if isinstance(event, str):
        event = Event.parse_obj(json.loads(event))
    if isinstance(event, Event):
        background_tasks.add_task(produce, [event], request)
    return


@router.post("/b", tags=['analytics_next'])
async def batch(
    event: Union[BatchEvent, str], request: Request, background_tasks: BackgroundTasks,
):
    '''
    Compatible with https://github.com/segmentio/analytics-next
    '''
    if isinstance(event, str):
        event = BatchEvent.parse_obj(json.loads(event))
    if isinstance(event, BatchEvent):
        background_tasks.add_task(produce, event.batch, request)
    return
