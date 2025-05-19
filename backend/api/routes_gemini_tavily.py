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

# Import enhanced processors
from utils.gemini_processor import get_gemini_processor, GeminiProcessor
from utils.tavily_search import prepare_resources_tavily, check_tavily_health
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

# Initialize services
init_cloudinary()
gemini_processor = get_gemini_processor("flash")

@router.get(
    "/",
    response_model=HealthCheck,
    tags=["Health"],
    summary="Health Check",
    description="Check if the API is running with Gemini + Tavily integration",
)
async def root():
    return HealthCheck(status="ok", message="Welcome to SmartRead API (Gemini + Tavily)")


async def process_single_page_enhanced(page_data: Dict[str, Any], url: str, total_pages: int) -> None:
    """Enhanced page processing with Gemini and Tavily"""
    page_number = page_data.get("index", 1)

    # Skip if page already exists
    if await check_page_exists_async(url, page_number):
        logger.info(f"Page {page_number} already exists, skipping")
        return

    try:
        # Extract content from Gemini result
        content = page_data.get("markdown", "")
        highlights = page_data.get("highlights", [])
        html = page_data.get("html", "")
        highlight_mapping = page_data.get("highlight_mapping", {})
        
        # If we don't have processed content, use Gemini to process
        if not html or not highlights:
            highlights_text = await gemini_processor.extract_highlights(content)
            html, highlight_mapping = await gemini_processor.format_to_html(content, highlights_text)
            highlights = list(highlight_mapping.values())
        
        # Prepare resources using Tavily
        resources = await prepare_resources_tavily(highlight_mapping)

        # Process images (if any)
        page_images = []
        for image in page_data.get("images", []):
            image_uuid = str(uuid.uuid4())
            cloudinary_img_url = await asyncio.to_thread(
                upload_to_cloudinary,
                image.get("image_base64", ""),
                f"url_{hash(url)}_page_{page_number}_image_{image_uuid}",
                file_type="image"
            )
            
            if cloudinary_img_url:
                page_images.append(
                    Images(
                        id=image.get("id", image_uuid),
                        top_left_x=image.get("top_left_x", 0),
                        top_left_y=image.get("top_left_y", 0),
                        bottom_right_x=image.get("bottom_right_x", 100),
                        bottom_right_y=image.get("bottom_right_y", 100),
                        image_url=cloudinary_img_url,
                    )
                )

        # Create page object
        page_obj = Page(
            index=page_number,
            content=html,
            highlights=highlights,
            dimensions=Dimensions(
                dpi=page_data.get("dimensions", {}).get("dpi", 72),
                height=page_data.get("dimensions", {}).get("height", 842),
                width=page_data.get("dimensions", {}).get("width", 595),
            ),
            images=page_images,
            resources=resources,
        )
        
        # Store page asynchronously
        final_page = page_obj.model_dump()
        await store_page_async(url, page_number, final_page, total_pages)
        
        logger.info(f"Successfully processed page {page_number} with Gemini + Tavily")
        
    except Exception as e:
        logger.error(f"Error processing page {page_number}: {str(e)}")
        raise


async def process_remaining_pages_enhanced(gemini_result: Dict[str, Any], url: str, total_pages: int):
    """Enhanced background task to process remaining pages"""
    try:
        # For Gemini, we typically get all content at once
        # So we might need to split it into pages or process additional pages
        pages = gemini_result.get("pages", [])
        
        # Process remaining pages (skip first one as it's already processed)
        for page_data in pages[1:]:
            await process_single_page_enhanced(page_data, url, total_pages)
            
        logger.info(f"Completed processing {len(pages) - 1} remaining pages")
        
    except Exception as e:
        logger.error(f"Error in enhanced background task: {str(e)}")


@router.post(
    "/api/extract",
    response_model=APIResponse,
    responses={
        200: {"description": "Successfully processed the document"},
        400: {"model": ErrorResponse, "description": "Invalid URL provided"},
        429: {"description": "Rate limit exceeded"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
        202: {"description": "Document is currently being processed"},
    },
    tags=["OCR"],
    summary="Extract Text from Document (Gemini + Tavily)",
    description="Process a document using Gemini AI with Tavily search integration",
)
@limiter.limit("10/minute")
async def extract_from_url_enhanced(request: Request, url_request: URLRequest, background_tasks: BackgroundTasks):
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

        # Process document with Gemini
        try:
            # Use Gemini's comprehensive processing
            gemini_result = await gemini_processor.process_document_with_cache(
                url_request.url, 
                processing_type="full"
            )
            
            if not gemini_result or "pages" not in gemini_result:
                raise Exception("No response received from Gemini")
                
        except Exception as e:
            logger.error(f"Gemini processing failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Document processing failed: {str(e)}")

        # Get pages from Gemini result
        pages = gemini_result.get("pages", [])
        if not pages:
            raise HTTPException(status_code=500, detail="No pages extracted from document")

        # Process first page immediately if it's the requested page
        first_page = pages[0]
        first_page_number = first_page.get("index", 1)

        if url_request.page_number == first_page_number:
            try:
                # Process first page with enhanced pipeline
                await process_single_page_enhanced(first_page, url_request.url, len(pages))
                
                # Get the processed page from database
                processed_page, _ = await get_page_async(url_request.url, first_page_number)
                
                if not processed_page:
                    raise Exception("Failed to retrieve processed page")

                # Schedule remaining pages for background processing
                if len(pages) > 1:
                    background_tasks.add_task(
                        process_remaining_pages_enhanced,
                        gemini_result,
                        url_request.url,
                        len(pages),
                    )

                return {
                    "status": "success",
                    "message": "Document processed successfully with Gemini + Tavily",
                    "data": {
                        "total_pages": len(pages),
                        "page": processed_page["page_data"],
                        "processing_method": "gemini_tavily",
                        "gemini_metadata": gemini_result.get("metadata", {}),
                        "summary": gemini_result.get("summary", ""),
                        "key_topics": gemini_result.get("key_topics", [])
                    },
                }
                
            except Exception as e:
                logger.error(f"Error processing first page: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))

        # If requested page is not the first page, return processing status
        return JSONResponse(
            status_code=202,
            content={
                "status": "processing",
                "message": f"Page {url_request.page_number} is being processed with Gemini",
                "data": {
                    "total_pages": len(pages),
                    "processing_method": "gemini_tavily"
                },
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in enhanced extraction: {str(e)}")
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
    summary="Download Enhanced PDF",
    description="Download a PDF with enhanced annotations",
)
@limiter.limit("5/minute")
async def download_pdf_enhanced(request: Request, download_request: DownloadPDFRequest):
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
            f"{'_'.join(original_filename.split('.')[:-1])}_enhanced",
            file_type="pdf",
        )

        return {
            "status": "success",
            "message": "Enhanced PDF Ready",
            "data": {"pdf_url": pdf_url},
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in enhanced PDF download: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/health/enhanced",
    response_model=dict,
    tags=["Health"],
    summary="Enhanced Health Check",
    description="Get detailed health information including Gemini and Tavily status",
)
async def enhanced_health_check():
    """Enhanced health check with Gemini and Tavily status"""
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
    
    # Check Gemini status
    try:
        gemini_status = "healthy" if os.getenv("GEMINI_API_KEY") else "not configured"
    except Exception as e:
        gemini_status = f"unhealthy: {str(e)}"
    
    # Check Tavily status
    try:
        tavily_healthy = await check_tavily_health()
        tavily_status = "healthy" if tavily_healthy else "unhealthy"
    except Exception as e:
        tavily_status = f"unhealthy: {str(e)}"
    
    return {
        "status": "ok",
        "timestamp": asyncio.get_event_loop().time(),
        "services": {
            "database": db_status,
            "cache": cache_status,
            "gemini": gemini_status,
            "tavily": tavily_status,
            "api": "healthy"
        },
        "features": {
            "gemini_processing": gemini_status == "healthy",
            "tavily_search": tavily_status == "healthy",
            "caching": cache_status == "healthy",
            "enhanced_pipeline": True
        }
    }


@router.get(
    "/api/search",
    response_model=dict,
    tags=["Search"],
    summary="Enhanced Search",
    description="Search for content using Tavily",
)
@limiter.limit("20/minute")
async def enhanced_search(request: Request, query: str, search_type: str = "all", max_results: int = 5):
    """Enhanced search endpoint using Tavily"""
    try:
        from utils.tavily_search import search_related_content, get_ai_summary
        
        # Search for content
        results = await search_related_content(query, search_type)
        
        # Get AI summary if requested
        summary = None
        if search_type in ["all", "summary"]:
            summary = await get_ai_summary(query)
        
        return {
            "status": "success",
            "query": query,
            "search_type": search_type,
            "results": results[:max_results],
            "summary": summary,
            "total_results": len(results)
        }
        
    except Exception as e:
        logger.error(f"Enhanced search error: {str(e)}")
        raise HTTPException(status_code=500, detail="Search failed")


# Add rate limit exceeded handler
@router.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    response = JSONResponse(
        status_code=429,
        content={"detail": f"Rate limit exceeded: {exc.detail}"}
    )
    response = await _rate_limit_exceeded_handler(request, exc)
    return response
