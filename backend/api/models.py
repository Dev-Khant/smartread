from pydantic import BaseModel
from typing import List, Optional

class URLRequest(BaseModel):
    url: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://example.com/image.jpg"
            }
        }

class ErrorResponse(BaseModel):
    detail: str

class HealthCheck(BaseModel):
    status: str
    message: str

class APIResponse(BaseModel):
    status: str
    message: str
    data: dict

class Dimensions(BaseModel):
    dpi: int
    height: int
    width: int

class Images(BaseModel):
    id: str
    top_left_x: int
    top_left_y: int
    bottom_right_x: int
    bottom_right_y: int
    image_base64: Optional[str] = None

class Page(BaseModel):
    index: int
    content: str
    images: Optional[List[Images]] = []
    dimensions: Optional[Dimensions] = []

