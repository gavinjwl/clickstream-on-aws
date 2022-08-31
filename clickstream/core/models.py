from typing import Dict, Union, List
from pydantic import BaseModel
import datetime


class Event(BaseModel):
    messageId: str  # Common
    timestamp: datetime.datetime = datetime.datetime.utcnow()

    type: str

    userId: Union[str, None] = None  # Common
    anonymousId: Union[str, None] = None  # Common
    context: Union[Dict, None] = None  # Common
    integrations: Union[Dict, None] = None  # Common
    traits: Union[Dict, None] = None  # Identify

    event: Union[str, None] = None  # Track
    properties: Union[Dict, None] = None  # Track

    previousId: Union[str, None] = None  # Alias

    groupId: Union[str, None] = None  # Group

    category: Union[str, None] = None  # Page
    name: Union[str, None] = None  # Page

    writeKey: Union[str, None] = None  # compatible with Python SDK
    sentAt: Union[datetime.datetime, None] = None


class BatchEvent(BaseModel):
    batch: List[Event]

    writeKey: Union[str, None] = None  # compatible with Python SDK
    sentAt: Union[datetime.datetime, None] = None
