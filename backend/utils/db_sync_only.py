import os
import base64
from typing import Dict, Optional, Tuple
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

# MongoDB connection (synchronous only)
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017/")
client = MongoClient(MONGODB_URL)
db = client.smartread

# Redis connection (optional)
redis_client = None
try:
    import redis
    REDIS_URL = os.getenv("REDIS_URL")
    if REDIS_URL:
        redis_client = redis.from_url(REDIS_URL)
except ImportError:
    pass

def store_page(url: str, page_number: int, page_data: dict, total_pages: int):
    """Store page in MongoDB (synchronous)"""
    document_id = f"{base64.b64encode(url.encode()).decode()}"
    
    # Encode content
    page_data_copy = page_data.copy()
    if "content" in page_data_copy:
        page_data_copy["content"] = base64.b64encode(page_data_copy["content"].encode()).decode()
    
    if "resources" in page_data_copy:
        page_data_copy["resources"] = {str(k): v for k, v in page_data_copy["resources"].items()}
    
    # Store in database
    db.pages.insert_one({
        "document_id": document_id,
        "url": url,
        "page_number": page_number,
        "page_data": page_data_copy,
        "total_pages": total_pages,
    })
    
    return document_id

def get_page(url: str, page_number: int) -> Tuple[Optional[Dict], int]:
    """Get page from MongoDB (synchronous)"""
    document_id = f"{base64.b64encode(url.encode()).decode()}"
    
    page_data = db.pages.find_one({
        "document_id": document_id,
        "page_number": page_number
    })
    
    if page_data and "page_data" in page_data and "content" in page_data["page_data"]:
        page_data["page_data"]["content"] = base64.b64decode(
            page_data["page_data"]["content"]
        ).decode()
    
    return page_data, 15

def check_page_exists(url: str, page_number: int) -> bool:
    """Check if page exists in MongoDB (synchronous)"""
    document_id = f"{base64.b64encode(url.encode()).decode()}"
    
    return db.pages.count_documents({
        "document_id": document_id,
        "page_number": page_number
    }) > 0

def get_highlights(url: str):
    """Retrieve highlights from MongoDB (synchronous)"""
    document_id = f"{base64.b64encode(url.encode()).decode()}"
    pages = db.pages.find({"document_id": document_id})

    highlights_dict = {}
    for page in pages:
        highlights_dict[page["page_number"] - 1] = page["page_data"]["highlights"]

    return highlights_dict
