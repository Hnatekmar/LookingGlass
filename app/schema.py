from typing import List

from pydantic import BaseModel


class Label(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float
    text: str


class AnnotationResponse(BaseModel):
    labels: List[Label]
