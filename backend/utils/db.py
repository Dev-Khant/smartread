import os
import base64
import asyncio
from typing import Optional, Tuple, Dict, Any

from pymongo import MongoClient
from motor.motor_asyncio import AsyncIOMotorClient
import redis
from dotenv import load_dotenv

load_dotenv()

# Initialize database connections
def _init_database():
    """
    Initialize MongoDB database connection
    """
    mongodb_url = os.getenv("MONGODB_URL")
    if not mongodb_url:
        raise ValueError("MongoDB URL not configured")

    client = MongoClient(mongodb_url)
    return client.smartread

def _init_async_database():
    """
    Initialize async MongoDB database connection
    """
    mongodb_url = os.getenv("MONGODB_URL")
    if not mongodb_url:
        raise ValueError("MongoDB URL not configured")

    client = AsyncIOMotorClient(mongodb_url)
    return client.smartread

def _init_redis():
    """
    Initialize Redis connection for caching
    """
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    try:
        return redis.from_url(redis_url, decode_responses=True)
    except Exception as e:
        print(f"Redis connection failed: {e}. Continuing without cache.")
        return None

# Global instances
db = _init_database()
async_db = _init_async_database()
redis_client = _init_redis()

# Cache TTL in seconds (1 hour)
CACHE_TTL = 3600


def store_page(url: str, page_number: int, page_data: dict, total_pages: int):
    """
    Store page data in MongoDB with HTML content encoded in base64
    """
    collection = db.pages

    document_id = f"{base64.b64encode(url.encode()).decode()}"

    page_data["content"] = base64.b64encode(page_data["content"].encode()).decode()

    if "resources" in page_data:
        page_data["resources"] = {str(k): v for k, v in page_data["resources"].items()}

    # Insert the document
    collection.insert_one(
        {
            "document_id": document_id,
            "url": url,
            "page_number": page_number,
            "page_data": page_data,
            "total_pages": total_pages,
        }
    )
    return document_id


def check_page_exists(url: str, page_number: int) -> bool:
    """
    Check if a specific page exists for a URL
    Returns: bool indicating if the page exists
    """
    collection = db.pages

    document_id = f"{base64.b64encode(url.encode()).decode()}"
    return (
        collection.count_documents(
            {"document_id": document_id, "page_number": page_number}
        )
        > 0
    )


def get_page(url: str, page_number: int):
    """
    Retrieve page data from MongoDB and total page count
    Returns: (page_data, total_pages) with decoded HTML content
    """
    collection = db.pages

    document_id = f"{base64.b64encode(url.encode()).decode()}"
    page_data = collection.find_one(
        {"document_id": document_id, "page_number": page_number}
    )

    if page_data and "page_data" in page_data and "content" in page_data["page_data"]:
        page_data["page_data"]["content"] = base64.b64decode(
            page_data["page_data"]["content"]
        ).decode()

    return page_data, 15


def get_highlights(url: str):
    """
    Retrieve highlights from MongoDB
    Returns: List of highlights
    """
    document_id = f"{base64.b64encode(url.encode()).decode()}"
    pages = db.pages.find({"document_id": document_id})

    highlights_dict = {}
    for page in pages:
        highlights_dict[page["page_number"] - 1] = page["page_data"]["highlights"]

    return highlights_dict


# Async versions with caching
async def store_page_async(url: str, page_number: int, page_data: dict, total_pages: int):
    """
    Async version of store_page with caching
    """
    collection = async_db.pages
    document_id = f"{base64.b64encode(url.encode()).decode()}"

    # Encode content
    page_data_copy = page_data.copy()
    page_data_copy["content"] = base64.b64encode(page_data_copy["content"].encode()).decode()

    if "resources" in page_data_copy:
        page_data_copy["resources"] = {str(k): v for k, v in page_data_copy["resources"].items()}

    # Store in database
    await collection.insert_one({
        "document_id": document_id,
        "url": url,
        "page_number": page_number,
        "page_data": page_data_copy,
        "total_pages": total_pages,
    })

    # Cache the page data
    if redis_client:
        cache_key = f"page:{document_id}:{page_number}"
        try:
            await asyncio.to_thread(
                redis_client.setex,
                cache_key,
                CACHE_TTL,
                base64.b64encode(str(page_data).encode()).decode()
            )
        except Exception as e:
            print(f"Cache write failed: {e}")

    return document_id


async def get_page_async(url: str, page_number: int) -> Tuple[Optional[Dict], int]:
    """
    Async version of get_page with caching
    """
    document_id = f"{base64.b64encode(url.encode()).decode()}"
    cache_key = f"page:{document_id}:{page_number}"

    # Try cache first
    if redis_client:
        try:
            cached_data = await asyncio.to_thread(redis_client.get, cache_key)
            if cached_data:
                # Decode and return cached data
                decoded_data = eval(base64.b64decode(cached_data).decode())
                return decoded_data, 15  # Return with default total pages
        except Exception as e:
            print(f"Cache read failed: {e}")

    # Fallback to database
    collection = async_db.pages
    page_data = await collection.find_one({
        "document_id": document_id,
        "page_number": page_number
    })

    if page_data and "page_data" in page_data and "content" in page_data["page_data"]:
        page_data["page_data"]["content"] = base64.b64decode(
            page_data["page_data"]["content"]
        ).decode()

        # Cache the result
        if redis_client:
            try:
                await asyncio.to_thread(
                    redis_client.setex,
                    cache_key,
                    CACHE_TTL,
                    base64.b64encode(str(page_data).encode()).decode()
                )
            except Exception as e:
                print(f"Cache write failed: {e}")

    return page_data, 15


async def check_page_exists_async(url: str, page_number: int) -> bool:
    """
    Async version of check_page_exists with caching
    """
    document_id = f"{base64.b64encode(url.encode()).decode()}"
    cache_key = f"exists:{document_id}:{page_number}"

    # Check cache first
    if redis_client:
        try:
            cached_result = await asyncio.to_thread(redis_client.get, cache_key)
            if cached_result is not None:
                return cached_result == "true"
        except Exception as e:
            print(f"Cache read failed: {e}")

    # Check database
    collection = async_db.pages
    exists = await collection.count_documents({
        "document_id": document_id,
        "page_number": page_number
    }) > 0

    # Cache the result
    if redis_client:
        try:
            await asyncio.to_thread(
                redis_client.setex,
                cache_key,
                CACHE_TTL,
                "true" if exists else "false"
            )
        except Exception as e:
            print(f"Cache write failed: {e}")

    return exists
