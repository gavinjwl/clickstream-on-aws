from fastapi import APIRouter, BackgroundTasks, Request
from kinesis_producer import produce
from models import BatchEvent

router = APIRouter()

@router.post("/v1/batch", tags=['analytics_python'])
async def batch(
    events: BatchEvent, request: Request, background_tasks: BackgroundTasks
):
    '''
    Compatible with https://github.com/segmentio/analytics-python
    '''
    background_tasks.add_task(produce, events, request)
    return
