import os
import logging
from typing import Dict, Optional, Union
from pathlib import Path

import cloudinary
import cloudinary.uploader
import cloudinary.utils

logger = logging.getLogger(__name__)

def init_cloudinary():
    """Initialize Cloudinary configuration with validation"""
    required_vars = ["CLOUDINARY_CLOUD_NAME", "CLOUDINARY_API_KEY", "CLOUDINARY_API_SECRET"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        raise ValueError(f"Missing Cloudinary environment variables: {missing_vars}")

    cloudinary.config(
        cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
        api_key=os.getenv("CLOUDINARY_API_KEY"),
        api_secret=os.getenv("CLOUDINARY_API_SECRET"),
        secure=True,
    )

    logger.info("Cloudinary initialized successfully")


def upload_to_cloudinary(
    file: Union[str, Path],
    public_id: str,
    file_type: str = "image",
    **kwargs
) -> Optional[str]:
    """
    Upload a file to Cloudinary with enhanced options

    Args:
        file: File path, base64 string, or file-like object
        public_id: Unique identifier for the file
        file_type: Type of file (image, pdf, video, etc.)
        **kwargs: Additional Cloudinary upload options

    Returns:
        Secure URL of uploaded file or None if failed
    """
    try:
        # Prepare upload options
        upload_options = {
            "public_id": public_id,
            "folder": "smartread",
            "overwrite": False,
            "resource_type": "auto",  # Auto-detect resource type
            **kwargs
        }

        # Handle different file types
        if file_type == "image":
            if isinstance(file, str) and not file.startswith("data:image"):
                file = f"data:image/png;base64,{file}"

            # Add image-specific optimizations
            upload_options.update({
                "quality": "auto:good",  # Automatic quality optimization
                "fetch_format": "auto",  # Automatic format selection
                "flags": "progressive",  # Progressive JPEG loading
            })

        elif file_type == "pdf":
            upload_options.update({
                "resource_type": "raw",  # PDFs are raw files
                "format": "pdf",
            })

        # Upload to Cloudinary
        upload_result = cloudinary.uploader.upload(file, **upload_options)

        # Log successful upload
        logger.info(f"Successfully uploaded {file_type} to Cloudinary: {public_id}")

        return upload_result["secure_url"]

    except Exception as e:
        logger.error(f"Error uploading {file_type} to Cloudinary: {str(e)}")
        return None


def generate_optimized_url(
    public_id: str,
    width: Optional[int] = None,
    height: Optional[int] = None,
    quality: str = "auto:good",
    format: str = "auto"
) -> str:
    """
    Generate optimized URL for an existing Cloudinary asset

    Args:
        public_id: The public ID of the uploaded asset
        width: Desired width in pixels
        height: Desired height in pixels
        quality: Quality setting (auto:good, auto:best, etc.)
        format: Format setting (auto, webp, jpg, etc.)

    Returns:
        Optimized Cloudinary URL
    """
    transformations = {
        "quality": quality,
        "fetch_format": format,
    }

    if width:
        transformations["width"] = width
    if height:
        transformations["height"] = height

    # If both width and height are specified, use smart cropping
    if width and height:
        transformations["crop"] = "fill"
        transformations["gravity"] = "auto"

    return cloudinary.utils.cloudinary_url(public_id, **transformations)[0]


def delete_from_cloudinary(public_id: str, resource_type: str = "image") -> bool:
    """
    Delete a file from Cloudinary

    Args:
        public_id: The public ID of the asset to delete
        resource_type: Type of resource (image, raw, video)

    Returns:
        True if successful, False otherwise
    """
    try:
        result = cloudinary.uploader.destroy(public_id, resource_type=resource_type)
        success = result.get("result") == "ok"

        if success:
            logger.info(f"Successfully deleted {resource_type} from Cloudinary: {public_id}")
        else:
            logger.warning(f"Failed to delete {resource_type} from Cloudinary: {public_id}")

        return success

    except Exception as e:
        logger.error(f"Error deleting {resource_type} from Cloudinary: {str(e)}")
        return False


def get_cloudinary_info(public_id: str) -> Optional[Dict]:
    """
    Get information about a Cloudinary asset

    Args:
        public_id: The public ID of the asset

    Returns:
        Asset information or None if not found
    """
    try:
        result = cloudinary.api.resource(public_id)
        return {
            "url": result["secure_url"],
            "format": result["format"],
            "size": result["bytes"],
            "created_at": result["created_at"],
            "width": result.get("width"),
            "height": result.get("height"),
        }
    except Exception as e:
        logger.error(f"Error getting Cloudinary info: {str(e)}")
        return None
