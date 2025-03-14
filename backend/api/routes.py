import os
import uuid
import tempfile
import asyncio
import logging
from tqdm import tqdm
from copy import deepcopy

from fastapi.responses import JSONResponse
from fastapi import APIRouter, HTTPException, BackgroundTasks
from urllib.parse import urlparse
from .models import (
    URLRequest,
    HealthCheck,
    ErrorResponse,
    APIResponse,
    Page,
    Dimensions,
    Images,
    DownloadPDFRequest,
)
from utils.extraction import extract_data, extract_highlights, format_to_html
from utils.search import prepare_resources
from utils.db import store_page, get_page, check_page_exists, get_highlights
from utils.cloudinary_utils import init_cloudinary, upload_to_cloudinary
from utils.download import download_and_highlight_pdf


# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize Cloudinary
init_cloudinary()


@router.get(
    "/",
    response_model=HealthCheck,
    tags=["Health"],
    summary="Health Check",
    description="Check if the API is running",
)
async def root():
    return HealthCheck(status="ok", message="Welcome to SmartRead API")


async def process_single_page(page, url: str, total_pages: int) -> None:
    """Process a single page and store it in the database"""
    page_number = page.index + 1

    # Skip if page already exists
    if check_page_exists(url, page_number):
        return

    try:
        highlights = extract_highlights(page.markdown)
        html, highlight_mapping = format_to_html(page.markdown, highlights)
        resources = prepare_resources(highlight_mapping)

        page_images = []
        for image in page.images:
            image_uuid = str(uuid.uuid4())
            cloudinary_img_url = upload_to_cloudinary(
                image.image_base64,
                f"url_{url}_page_{page.index}_image_{image_uuid}",
            )
            page_images.append(
                Images(
                    id=image.id,
                    top_left_x=image.top_left_x,
                    top_left_y=image.top_left_y,
                    bottom_right_x=image.bottom_right_x,
                    bottom_right_y=image.bottom_right_y,
                    image_url=cloudinary_img_url,
                )
            )

        page_obj = Page(
            index=page_number,
            content=f"""{html}""",
            highlights=list(highlight_mapping.values()),
            dimensions=Dimensions(
                dpi=page.dimensions.dpi,
                height=page.dimensions.height,
                width=page.dimensions.width,
            ),
            images=page_images,
            resources=resources,
        )
        final_page = page_obj.model_dump()
        store_page(url, page_number, final_page, total_pages)
    except Exception as e:
        logger.error(f"Error processing page {page_number}: {str(e)}")


def process_remaining_pages(ocr_response, url, total_pages):
    """Background task to process remaining pages starting from page 2 sequentially"""
    try:
        # Process remaining pages sequentially
        for page in tqdm(ocr_response.pages[1:], desc="Processing remaining pages"):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(process_single_page(page, url, total_pages))
    except Exception as e:
        logger.error(f"Error in background task: {str(e)}")


@router.post(
    "/api/extract",
    response_model=APIResponse,
    responses={
        200: {"description": "Successfully processed the image"},
        400: {"model": ErrorResponse, "description": "Invalid URL provided"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
        202: {"description": "Page is currently being processed"},
    },
    tags=["OCR"],
    summary="Extract Text from Image",
    description="Process an image from a given URL using Mistral OCR to extract text",
)
async def extract_from_url(request: URLRequest, background_tasks: BackgroundTasks):
    try:
        # Check if page already exists
        existing_page, total_pages = get_page(request.url, request.page_number)

        if existing_page:
            return {
                "status": "success",
                "message": "Retrieved from cache",
                "data": {
                    "total_pages": total_pages,
                    "page": existing_page["page_data"],
                },
            }

        try:
            result = urlparse(request.url)
            if not all([result.scheme, result.netloc]):
                raise ValueError("Invalid URL")
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid URL provided")

        ocr_response = extract_data(request.url)
        if not ocr_response or not ocr_response.pages:
            raise HTTPException(
                status_code=500, detail="No response received from Mistral API"
            )

        # Process first page immediately if it's the requested page
        first_page = ocr_response.pages[0]
        first_page_number = first_page.index + 1

        if request.page_number == first_page_number:
            highlights = extract_highlights(first_page.markdown)
            html, highlight_mapping = format_to_html(first_page.markdown, highlights)
            resources = prepare_resources(highlight_mapping)

            page_images = []
            for image in first_page.images:
                image_uuid = str(uuid.uuid4())
                cloudinary_img_url = upload_to_cloudinary(
                    image.image_base64,
                    f"url_{request.url}_page_{first_page.index}_image_{image_uuid}",
                )
                page_images.append(
                    Images(
                        id=image.id,
                        top_left_x=image.top_left_x,
                        top_left_y=image.top_left_y,
                        bottom_right_x=image.bottom_right_x,
                        bottom_right_y=image.bottom_right_y,
                        image_url=cloudinary_img_url,
                    )
                )

            page_obj = Page(
                index=first_page_number,
                content=f"""{html}""",
                highlights=list(highlight_mapping.values()),
                dimensions=Dimensions(
                    dpi=first_page.dimensions.dpi,
                    height=first_page.dimensions.height,
                    width=first_page.dimensions.width,
                ),
                images=page_images,
                resources=resources,
            )
            final_page = page_obj.model_dump()
            response_page = deepcopy(final_page)
            store_page(
                request.url, first_page_number, final_page, len(ocr_response.pages)
            )

            # Schedule remaining pages for background processing
            if len(ocr_response.pages) > 1:
                background_tasks.add_task(
                    process_remaining_pages,
                    ocr_response,
                    request.url,
                    len(ocr_response.pages),
                )

            return {
                "status": "success",
                "message": "Page processed successfully",
                "data": {"total_pages": len(ocr_response.pages), "page": response_page},
            }

        return JSONResponse(
            status_code=202,
            content={
                "status": "processing",
                "message": f"Page {request.page_number} is being processed",
                "data": {"total_pages": len(ocr_response.pages)},
            },
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/pdf/download",
    response_model=dict,
    responses={
        200: {"description": "Successfully downloaded the PDF"},
        400: {"model": ErrorResponse, "description": "Failed to download PDF"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    tags=["PDF"],
    summary="Download PDF",
    description="Download a PDF from a given URL",
)
async def download_pdf(request: DownloadPDFRequest):
    try:
        highlights = get_highlights(request.pdf_url)
        # Create a temporary directory to work with files
        with tempfile.TemporaryDirectory() as temp_dir:
            original_pdf_path = os.path.join(temp_dir, "original.pdf")
            with open(original_pdf_path, "wb") as _:
                success, original_filename, highlighted_pdf_path = (
                    download_and_highlight_pdf(request.pdf_url, highlights)
                )
                if not success:
                    raise HTTPException(
                        status_code=400, detail="Failed to download PDF"
                    )

            # Upload to Cloudinary
            pdf_url = upload_to_cloudinary(
                highlighted_pdf_path,
                f"{'_'.join(original_filename.split('.')[:-1])}",
                type="pdf",
            )

            return {
                "status": "success",
                "message": "PDF Ready",
                "data": {"pdf_url": pdf_url},
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
