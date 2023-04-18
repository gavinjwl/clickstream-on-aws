import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel


class Event(BaseModel):
    messageId: str  # Common
    timestamp: datetime.datetime = datetime.datetime.utcnow()

    type: str

    userId: Optional[str] = None  # Common
    anonymousId: Optional[str] = None  # Common
    context: Optional[Dict] = dict()  # Common
    integrations: Optional[Dict] = dict()  # Common
    traits: Optional[Dict] = dict()  # Identify

    event: Optional[str] = None  # Track
    properties: Optional[Dict] = dict()  # Track

    previousId: Optional[str] = None  # Alias

    groupId: Optional[str] = None  # Group

    category: Optional[str] = None  # Page
    name: Optional[str] = None  # Page

    writeKey: Optional[str] = None  # compatible with Python SDK
    sentAt: Optional[datetime.datetime] = None


class BatchEvent(BaseModel):
    batch: List[Event]

    writeKey: Optional[str] = None  # compatible with Python SDK
    sentAt: Optional[datetime.datetime] = None
