from typing import List, Optional

from pydantic import BaseModel


class Label(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float
    text: str


class AnnotationResponse(BaseModel):
    labels: List[Label]


# --- SSE Event Models for Streaming ---

class SSELabelsEventData(BaseModel):
    """Data for a 'labels' SSE event — labels from one tile."""
    tile: int
    labels: List[Label]


class SSETranslateUpdate(BaseModel):
    """A single label translation update."""
    index: int
    text: str


class SSETranslateEventData(BaseModel):
    """Data for a 'translate' SSE event."""
    updates: List[SSETranslateUpdate]


class SSEErrorEventData(BaseModel):
    """Data for an 'error' SSE event."""
    detail: str


class SSECompleteEventData(BaseModel):
    """Data for the terminal 'complete' SSE event."""
    pass


# Union type for SSE events (used for type safety, not serialized as a union)
SSEEventData = SSELabelsEventData | SSETranslateEventData | SSEErrorEventData | SSECompleteEventData
