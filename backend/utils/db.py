import os
import base64

from pymongo import MongoClient


# Initialize database connection at module level
def _init_database():
    """
    Initialize MongoDB database connection
    """
    mongodb_url = os.getenv("MONGODB_URL")
    if not mongodb_url:
        raise ValueError("MongoDB URL not configured")

    client = MongoClient(mongodb_url)
    return client.smartread


# Global database instance
db = _init_database()


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
