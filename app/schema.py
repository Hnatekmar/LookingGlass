from typing import List

from pydantic import BaseModel


class Label(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float
    text: str


class TextBoundingBox(BaseModel):
    bbox_2d: List[float]  # [x1, y1, x2, y2] format
    text: str


class TextBoundingBoxContainer(BaseModel):
    labels: List[TextBoundingBox]

class AnnotationResponse(BaseModel):
    labels: List[Label]
