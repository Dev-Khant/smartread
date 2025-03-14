from pydantic import BaseModel
from typing import List, Dict, Optional


class URLRequest(BaseModel):
    url: str
    page_number: int = 1

    class Config:
        json_schema_extra = {
            "example": {"url": "https://example.com/image.jpg", "page_number": 1}
        }


class ErrorResponse(BaseModel):
    detail: str


class HealthCheck(BaseModel):
    status: str
    message: str


class APIResponse(BaseModel):
    status: str
    message: str
    data: Dict


class Dimensions(BaseModel):
    dpi: int
    height: int
    width: int


class Images(BaseModel):
    id: str
    top_left_x: float
    top_left_y: float
    bottom_right_x: float
    bottom_right_y: float
    image_url: Optional[str] = None


class Page(BaseModel):
    index: int
    content: str
    highlights: List[str]
    dimensions: Dimensions
    images: List[Images]
    resources: Dict


class DownloadPDFRequest(BaseModel):
    pdf_url: str
