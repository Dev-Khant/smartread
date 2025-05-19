import os
import uuid
import asyncio
import logging
from typing import Dict, Any
from urllib.parse import urlparse

from fastapi import APIRouter, HTTPException, BackgroundTasks, Request
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

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
from utils.extraction_async import (
    extract_data_async,
    extract_highlights_async,
    format_to_html_async,
    process_pages_batch,
    ExtractionError,
)
from utils.search_async import prepare_resources_async, SearchError
from utils.db import (
    store_page_async,
    get_page_async,
    check_page_exists_async,
    get_highlights,
)
from utils.cloudinary_utils import init_cloudinary, upload_to_cloudinary
from utils.download import download_and_highlight_pdf

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)
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


async def process_single_page_async(page, url: str, total_pages: int) -> None:
    """Async version of process_single_page with better error handling"""
    page_number = page.index + 1

    # Skip if page already exists
    if await check_page_exists_async(url, page_number):
        logger.info(f"Page {page_number} already exists, skipping")
        return

    try:
        # Extract highlights and format to HTML
        highlights = await extract_highlights_async(page.markdown)
        html, highlight_mapping = await format_to_html_async(page.markdown, highlights)

        # Prepare resources asynchronously
        resources = await prepare_resources_async(highlight_mapping)

        # Process images
        page_images = []
        for image in page.images:
            image_uuid = str(uuid.uuid4())
            # Upload to Cloudinary in thread pool
            cloudinary_img_url = await asyncio.to_thread(
                upload_to_cloudinary,
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

        # Create page object
        page_obj = Page(
            index=page_number,
            content=html,
            highlights=list(highlight_mapping.values()),
            dimensions=Dimensions(
                dpi=page.dimensions.dpi,
                height=page.dimensions.height,
                width=page.dimensions.width,
            ),
            images=page_images,
            resources=resources,
        )

        # Store page asynchronously
        final_page = page_obj.model_dump()
        await store_page_async(url, page_number, final_page, total_pages)

        logger.info(f"Successfully processed page {page_number}")

    except Exception as e:
        logger.error(f"Error processing page {page_number}: {str(e)}")
        raise


async def process_remaining_pages_async(ocr_response, url: str, total_pages: int):
    """Async background task to process remaining pages"""
    try:
        # Process remaining pages in batches
        remaining_pages = ocr_response.pages[1:]
        if remaining_pages:
            await process_pages_batch(remaining_pages, url, batch_size=3)
            logger.info(f"Completed processing {len(remaining_pages)} remaining pages")
    except Exception as e:
        logger.error(f"Error in background task: {str(e)}")


@router.post(
    "/api/extract",
    response_model=APIResponse,
    responses={
        200: {"description": "Successfully processed the image"},
        400: {"model": ErrorResponse, "description": "Invalid URL provided"},
        429: {"description": "Rate limit exceeded"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
        202: {"description": "Page is currently being processed"},
    },
    tags=["OCR"],
    summary="Extract Text from Image",
    description="Process an image from a given URL using Mistral OCR to extract text",
)
@limiter.limit("10/minute")  # Rate limit: 10 requests per minute per IP
async def extract_from_url_async(request: Request, url_request: URLRequest, background_tasks: BackgroundTasks):
    try:
        # Validate URL
        try:
            result = urlparse(url_request.url)
            if not all([result.scheme, result.netloc]):
                raise ValueError("Invalid URL")
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid URL provided")

        # Check if page already exists
        existing_page, total_pages = await get_page_async(url_request.url, url_request.page_number)

        if existing_page:
            logger.info(f"Page {url_request.page_number} found in cache")
            return {
                "status": "success",
                "message": "Retrieved from cache",
                "data": {
                    "total_pages": total_pages,
                    "page": existing_page["page_data"],
                },
            }

        # Extract data using async version
        try:
            ocr_response = await extract_data_async(url_request.url)
        except ExtractionError as e:
            raise HTTPException(status_code=500, detail=str(e))

        if not ocr_response or not ocr_response.pages:
            raise HTTPException(
                status_code=500, detail="No response received from Mistral API"
            )

        # Process first page immediately if it's the requested page
        first_page = ocr_response.pages[0]
        first_page_number = first_page.index + 1

        if url_request.page_number == first_page_number:
            try:
                # Process first page
                highlights = await extract_highlights_async(first_page.markdown)
                html, highlight_mapping = await format_to_html_async(first_page.markdown, highlights)
                resources = await prepare_resources_async(highlight_mapping)

                # Process images
                page_images = []
                for image in first_page.images:
                    image_uuid = str(uuid.uuid4())
                    cloudinary_img_url = await asyncio.to_thread(
                        upload_to_cloudinary,
                        image.image_base64,
                        f"url_{url_request.url}_page_{first_page.index}_image_{image_uuid}",
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

                # Create page object
                page_obj = Page(
                    index=first_page_number,
                    content=html,
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
                response_page = final_page.copy()

                # Store page asynchronously
                await store_page_async(
                    url_request.url, first_page_number, final_page, len(ocr_response.pages)
                )

                # Schedule remaining pages for background processing
                if len(ocr_response.pages) > 1:
                    background_tasks.add_task(
                        process_remaining_pages_async,
                        ocr_response,
                        url_request.url,
                        len(ocr_response.pages),
                    )

                return {
                    "status": "success",
                    "message": "Page processed successfully",
                    "data": {"total_pages": len(ocr_response.pages), "page": response_page},
                }

            except (ExtractionError, SearchError) as e:
                raise HTTPException(status_code=500, detail=str(e))

        # If requested page is not the first page, return processing status
        return JSONResponse(
            status_code=202,
            content={
                "status": "processing",
                "message": f"Page {url_request.page_number} is being processed",
                "data": {"total_pages": len(ocr_response.pages)},
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in extract_from_url_async: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post(
    "/pdf/download",
    response_model=dict,
    responses={
        200: {"description": "Successfully downloaded the PDF"},
        400: {"model": ErrorResponse, "description": "Failed to download PDF"},
        429: {"description": "Rate limit exceeded"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    tags=["PDF"],
    summary="Download PDF",
    description="Download a PDF from a given URL",
)
@limiter.limit("5/minute")  # Rate limit: 5 downloads per minute per IP
async def download_pdf_async(request: Request, download_request: DownloadPDFRequest):
    try:
        # Get highlights (this could also be made async)
        highlights = await asyncio.to_thread(get_highlights, download_request.pdf_url)

        # Download and highlight PDF in thread pool
        success, original_filename, highlighted_pdf_path = await asyncio.to_thread(
            download_and_highlight_pdf,
            download_request.pdf_url,
            highlights
        )

        if not success:
            raise HTTPException(status_code=400, detail="Failed to download PDF")

        # Upload to Cloudinary
        pdf_url = await asyncio.to_thread(
            upload_to_cloudinary,
            highlighted_pdf_path,
            f"{'_'.join(original_filename.split('.')[:-1])}",
            file_type="pdf",
        )

        return {
            "status": "success",
            "message": "PDF Ready",
            "data": {"pdf_url": pdf_url},
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in download_pdf_async: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Add rate limit exceeded handler
@router.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    response = JSONResponse(
        status_code=429,
        content={"detail": f"Rate limit exceeded: {exc.detail}"}
    )
    response = await _rate_limit_exceeded_handler(request, exc)
    return response


# Health check with more detailed information
@router.get(
    "/health",
    response_model=dict,
    tags=["Health"],
    summary="Detailed Health Check",
    description="Get detailed health information about the API",
)
async def health_check():
    """Detailed health check endpoint"""
    try:
        # Check database connectivity
        from utils.db import async_db
        await async_db.command("ping")
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    # Check Redis connectivity
    try:
        from utils.db import redis_client
        if redis_client:
            await asyncio.to_thread(redis_client.ping)
            cache_status = "healthy"
        else:
            cache_status = "not configured"
    except Exception as e:
        cache_status = f"unhealthy: {str(e)}"

    return {
        "status": "ok",
        "timestamp": asyncio.get_event_loop().time(),
        "services": {
            "database": db_status,
            "cache": cache_status,
            "api": "healthy"
        }
    }
