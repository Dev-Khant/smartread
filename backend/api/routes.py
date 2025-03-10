from fastapi import APIRouter, HTTPException
from mistralai import Mistral
from urllib.parse import urlparse
from .models import URLRequest, HealthCheck, ErrorResponse, APIResponse, Page, Dimensions, Images
import os
from utils.extraction import extract_data, extract_highlights, format_to_html

router = APIRouter()

@router.get("/",
    response_model=HealthCheck,
    tags=["Health"],
    summary="Health Check",
    description="Check if the API is running"
)
async def root():
    return HealthCheck(status="ok", message="Welcome to SmartRead API")


@router.post("/api/extract",
    response_model=APIResponse,
    responses={
        200: {"description": "Successfully processed the image"},
        400: {"model": ErrorResponse, "description": "Invalid URL provided"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    },
    tags=["OCR"],
    summary="Extract Text from Image",
    description="Process an image from a given URL using Mistral OCR to extract text"
)
async def extract_from_url(request: URLRequest):
    try:
        api_key = os.getenv("MISTRAL_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="Mistral API key is not configured")

        client = Mistral(api_key=api_key)

        # Validate URL
        try:
            result = urlparse(request.url)
            if not all([result.scheme, result.netloc]):
                raise ValueError("Invalid URL")
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid URL provided")

        ocr_response = extract_data(request.url)

        final_page = {}
        for page in ocr_response.pages:
            highlights = extract_highlights(page.markdown)
            html = format_to_html(page.markdown, highlights)

            page_images = [
                Images(
                    id=image.id,
                    top_left_x=image.top_left_x,
                    top_left_y=image.top_left_y,
                    bottom_right_x=image.bottom_right_x,
                    bottom_right_y=image.bottom_right_y,
                    image_base64=image.image_base64
                ) for image in page.images
            ]

            # Create Page object with all components
            page_obj = Page(
                index=page.index,
                content=f"""{html}""",  # Using the formatted HTML content
                dimensions=Dimensions(
                    dpi=page.dimensions.dpi,
                    height=page.dimensions.height,
                    width=page.dimensions.width
                ),
                images=page_images
            )
            final_page = page_obj.model_dump()
            break

        if not ocr_response:
            raise HTTPException(status_code=500, detail="No response received from Mistral API")

        result = {
            "status": "success",
            "message": "Text extracted successfully",
            "data": {"total_pages": len(ocr_response.pages), "page": final_page}
        }

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))