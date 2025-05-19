import os
import base64
import hashlib
import logging
from typing import Optional, Union
from pathlib import Path
import uuid

logger = logging.getLogger(__name__)

# Create storage directories
STORAGE_DIR = Path("storage")
IMAGES_DIR = STORAGE_DIR / "images"
PDFS_DIR = STORAGE_DIR / "pdfs"
THUMBNAILS_DIR = STORAGE_DIR / "thumbnails"

# Create directories if they don't exist
for directory in [STORAGE_DIR, IMAGES_DIR, PDFS_DIR, THUMBNAILS_DIR]:
    directory.mkdir(exist_ok=True)

def init_local_storage():
    """Initialize local storage directories"""
    logger.info("Local storage initialized")
    return True

def save_to_local_storage(
    file_data: Union[str, bytes, Path], 
    filename: str, 
    file_type: str = "image"
) -> Optional[str]:
    """
    Save file to local storage
    
    Args:
        file_data: Base64 string, bytes, or file path
        filename: Name for the file
        file_type: Type of file (image, pdf, thumbnail)
    
    Returns:
        Local URL path or None if failed
    """
    try:
        # Determine storage directory
        if file_type == "image":
            storage_dir = IMAGES_DIR
        elif file_type == "pdf":
            storage_dir = PDFS_DIR
        elif file_type == "thumbnail":
            storage_dir = THUMBNAILS_DIR
        else:
            storage_dir = STORAGE_DIR
        
        # Handle different input types
        if isinstance(file_data, str):
            if file_data.startswith("data:"):
                # Base64 data URL
                header, data = file_data.split(",", 1)
                file_bytes = base64.b64decode(data)
            elif file_data.startswith("/") or file_data.startswith("C:"):
                # File path
                with open(file_data, "rb") as f:
                    file_bytes = f.read()
            else:
                # Assume base64 string
                file_bytes = base64.b64decode(file_data)
        elif isinstance(file_data, bytes):
            file_bytes = file_data
        elif isinstance(file_data, Path):
            with open(file_data, "rb") as f:
                file_bytes = f.read()
        else:
            raise ValueError(f"Unsupported file_data type: {type(file_data)}")
        
        # Generate unique filename if needed
        if not filename.endswith(('.png', '.jpg', '.jpeg', '.pdf', '.webp')):
            if file_type == "pdf":
                filename += ".pdf"
            else:
                filename += ".png"
        
        # Save file
        file_path = storage_dir / filename
        with open(file_path, "wb") as f:
            f.write(file_bytes)
        
        # Return relative URL path
        relative_path = file_path.relative_to(STORAGE_DIR)
        url = f"/storage/{relative_path}"
        
        logger.info(f"Successfully saved {file_type} to local storage: {filename}")
        return url
        
    except Exception as e:
        logger.error(f"Error saving {file_type} to local storage: {str(e)}")
        return None

def get_file_info(file_path: str) -> Optional[dict]:
    """Get information about a stored file"""
    try:
        full_path = STORAGE_DIR / file_path.lstrip("/storage/")
        if full_path.exists():
            stat = full_path.stat()
            return {
                "size": stat.st_size,
                "created": stat.st_ctime,
                "modified": stat.st_mtime,
                "exists": True
            }
        return {"exists": False}
    except Exception as e:
        logger.error(f"Error getting file info: {str(e)}")
        return None

def delete_file(file_path: str) -> bool:
    """Delete a file from local storage"""
    try:
        full_path = STORAGE_DIR / file_path.lstrip("/storage/")
        if full_path.exists():
            full_path.unlink()
            logger.info(f"Deleted file: {file_path}")
            return True
        return False
    except Exception as e:
        logger.error(f"Error deleting file: {str(e)}")
        return False

# Alternative implementations for different storage backends

class S3Storage:
    """AWS S3 storage implementation"""
    
    def __init__(self, bucket_name: str, region: str = "us-east-1"):
        try:
            import boto3
            self.s3 = boto3.client('s3', region_name=region)
            self.bucket = bucket_name
            logger.info(f"S3 storage initialized: {bucket_name}")
        except ImportError:
            raise ImportError("boto3 required for S3 storage. Install with: pip install boto3")
    
    def upload(self, file_data: bytes, key: str) -> Optional[str]:
        """Upload file to S3"""
        try:
            self.s3.put_object(Bucket=self.bucket, Key=key, Body=file_data)
            url = f"https://{self.bucket}.s3.amazonaws.com/{key}"
            return url
        except Exception as e:
            logger.error(f"S3 upload error: {str(e)}")
            return None

class MinIOStorage:
    """MinIO storage implementation (self-hosted S3-compatible)"""
    
    def __init__(self, endpoint: str, access_key: str, secret_key: str, bucket_name: str):
        try:
            from minio import Minio
            self.client = Minio(
                endpoint,
                access_key=access_key,
                secret_key=secret_key,
                secure=False  # Set to True for HTTPS
            )
            self.bucket = bucket_name
            
            # Create bucket if it doesn't exist
            if not self.client.bucket_exists(bucket_name):
                self.client.make_bucket(bucket_name)
            
            logger.info(f"MinIO storage initialized: {bucket_name}")
        except ImportError:
            raise ImportError("minio required for MinIO storage. Install with: pip install minio")
    
    def upload(self, file_data: bytes, key: str) -> Optional[str]:
        """Upload file to MinIO"""
        try:
            from io import BytesIO
            self.client.put_object(
                self.bucket, 
                key, 
                BytesIO(file_data), 
                length=len(file_data)
            )
            # Generate presigned URL (valid for 7 days)
            url = self.client.presigned_get_object(self.bucket, key, expires=timedelta(days=7))
            return url
        except Exception as e:
            logger.error(f"MinIO upload error: {str(e)}")
            return None

# Factory function to get storage backend
def get_storage_backend():
    """Get configured storage backend"""
    storage_type = os.getenv("STORAGE_TYPE", "local").lower()
    
    if storage_type == "s3":
        return S3Storage(
            bucket_name=os.getenv("S3_BUCKET_NAME"),
            region=os.getenv("S3_REGION", "us-east-1")
        )
    elif storage_type == "minio":
        return MinIOStorage(
            endpoint=os.getenv("MINIO_ENDPOINT"),
            access_key=os.getenv("MINIO_ACCESS_KEY"),
            secret_key=os.getenv("MINIO_SECRET_KEY"),
            bucket_name=os.getenv("MINIO_BUCKET_NAME")
        )
    else:
        # Default to local storage
        return None  # Use local storage functions directly
