import os
from typing import Dict, Optional

import cloudinary
import cloudinary.uploader

def init_cloudinary():
    """Initialize Cloudinary configuration"""
    cloudinary.config(
        cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
        api_key=os.getenv("CLOUDINARY_API_KEY"),
        api_secret=os.getenv("CLOUDINARY_API_SECRET"),
        secure=True,
    )


def upload_to_cloudinary(
    file: str, public_id: str, type: str = "image"
) -> Optional[Dict]:
    """
    Upload a file to Cloudinary and generate thumbnails
    Returns: Dictionary containing image URLs and metadata
    """
    try:
        if type == "image":
            if "data:image" not in file:
                file = f"data:image/png;base64,{file}"

        upload_result = cloudinary.uploader.upload(
            file=file, public_id=public_id, folder="smartread", overwrite=False
        )

        # Get URLs for different versions
        original_url = upload_result["secure_url"]

        return original_url
    except Exception as e:
        print(f"Error uploading image: {str(e)}")
        return None
