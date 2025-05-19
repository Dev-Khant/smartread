import os
import re
import json
import base64
import asyncio
import aiohttp
from typing import Literal, Dict, Any, List, Union, Optional
from concurrent.futures import ThreadPoolExecutor
import hashlib

from .cloudinary_utils import upload_to_cloudinary
from .db import redis_client, CACHE_TTL


class SearchError(Exception):
    """Custom exception for search errors"""
    pass


def generate_cache_key(query: str, search_type: str) -> str:
    """Generate a cache key for search results"""
    key_string = f"search:{search_type}:{query}"
    return hashlib.md5(key_string.encode()).hexdigest()


async def get_cached_search_result(cache_key: str) -> Optional[List[Dict]]:
    """Get cached search result"""
    if not redis_client:
        return None
    
    try:
        cached_data = await asyncio.to_thread(redis_client.get, cache_key)
        if cached_data:
            return json.loads(cached_data)
    except Exception as e:
        print(f"Cache read error: {e}")
    
    return None


async def cache_search_result(cache_key: str, result: List[Dict]) -> None:
    """Cache search result"""
    if not redis_client:
        return
    
    try:
        await asyncio.to_thread(
            redis_client.setex,
            cache_key,
            CACHE_TTL,
            json.dumps(result)
        )
    except Exception as e:
        print(f"Cache write error: {e}")


def extract_youtube_video_id(url: str) -> Optional[str]:
    """Extract video ID from YouTube URL"""
    patterns = [
        r"(?:youtube\.com\/watch\?v=|youtu.be\/)([^&\n?]*)",
        r"youtube.com/embed/([^&\n?]*)",
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


async def get_hd_thumbnail_base64_async(video_id: str) -> Optional[str]:
    """Get HD thumbnail as base64 encoded string asynchronously"""
    urls = [
        f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg",
        f"https://img.youtube.com/vi/{video_id}/mqdefault.jpg"
    ]
    
    async with aiohttp.ClientSession() as session:
        for url in urls:
            try:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        content = await response.read()
                        return base64.b64encode(content).decode("utf-8")
            except Exception as e:
                print(f"Error fetching thumbnail from {url}: {e}")
                continue
    
    return None


async def serper_search_async(
    query: str,
    search_type: Literal["search", "videos"] = "search",
    max_retries: int = 3
) -> List[Dict[str, Any]]:
    """
    Async version of serper_search with caching and retry logic.
    
    Args:
        query (str): The search query
        search_type (str): Type of search - either "search" or "videos"
        max_retries (int): Maximum number of retry attempts
    
    Returns:
        List[Dict]: Formatted search results
    """
    # Check cache first
    cache_key = generate_cache_key(query, search_type)
    cached_result = await get_cached_search_result(cache_key)
    if cached_result:
        return cached_result
    
    base_url = "https://google.serper.dev"
    url = f"{base_url}/{search_type}"
    
    base_query = (
        f"Find relevant videos about this: {query}"
        if search_type == "videos"
        else query
    )
    payload = json.dumps({"q": base_query})
    
    headers = {
        "X-API-KEY": os.getenv("SERPER_API_KEY"),
        "Content-Type": "application/json",
    }
    
    for attempt in range(max_retries):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, data=payload, timeout=30) as response:
                    response.raise_for_status()
                    result = await response.json()
                    
                    # Format results based on search type
                    formatted_results = await format_search_results(result, search_type)
                    
                    # Cache the results
                    await cache_search_result(cache_key, formatted_results)
                    
                    return formatted_results
                    
        except Exception as e:
            if attempt == max_retries - 1:
                raise SearchError(f"Search failed after {max_retries} attempts: {str(e)}")
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
    
    return []


async def format_search_results(result: Dict, search_type: str) -> List[Dict[str, Any]]:
    """Format search results based on type"""
    if search_type == "videos" and "videos" in result:
        return await format_video_results(result["videos"][:5])
    elif search_type == "search" and "organic" in result:
        return format_article_results(result["organic"][:5])
    return []


async def format_video_results(videos: List[Dict]) -> List[Dict[str, Any]]:
    """Format video results with async thumbnail processing"""
    formatted_videos = []
    
    # Process videos concurrently
    tasks = [process_single_video(video) for video in videos]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    for result in results:
        if isinstance(result, dict) and not isinstance(result, Exception):
            formatted_videos.append(result)
    
    return formatted_videos


async def process_single_video(video: Dict) -> Dict[str, Any]:
    """Process a single video result"""
    video_id = extract_youtube_video_id(video.get("link", ""))
    cloudinary_img_url = None
    
    if video_id:
        thumbnail_base64 = await get_hd_thumbnail_base64_async(video_id)
        if thumbnail_base64:
            # Upload to Cloudinary in thread pool to avoid blocking
            cloudinary_img_url = await asyncio.to_thread(
                upload_to_cloudinary,
                thumbnail_base64,
                f"video_{video_id}"
            )
    
    return {
        "title": video.get("title", ""),
        "link": video.get("link", ""),
        "duration": video.get("duration", ""),
        "image_url": cloudinary_img_url,
    }


def format_article_results(articles: List[Dict]) -> List[Dict[str, Any]]:
    """Format article results"""
    formatted_results = []
    for item in articles:
        formatted_result = {
            "title": item.get("title", ""),
            "link": item.get("link", ""),
            "snippet": item.get("snippet", ""),
        }
        formatted_results.append(formatted_result)
    return formatted_results


async def prepare_resources_async(highlight_mapping: Dict[int, str], max_concurrent: int = 5) -> Dict[int, Dict]:
    """
    Async version of prepare_resources with better concurrency control.
    
    Args:
        highlight_mapping (dict): A dictionary mapping highlight indexes to their sentences
        max_concurrent (int): Maximum number of concurrent search operations
    
    Returns:
        dict: A dictionary of resources indexed by highlight index
    """
    resources = {}
    
    # Create semaphore to limit concurrent operations
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def search_for_highlight(index: int, sentence: str):
        async with semaphore:
            try:
                # Run both searches concurrently
                articles_task = serper_search_async(sentence, "search")
                videos_task = serper_search_async(sentence, "videos")
                
                articles, videos = await asyncio.gather(articles_task, videos_task)
                
                return index, {"articles": articles, "videos": videos}
            except Exception as e:
                print(f"Error searching for highlight {index}: {e}")
                return index, {"articles": [], "videos": []}
    
    # Create tasks for all highlights
    tasks = [
        search_for_highlight(index, sentence)
        for index, sentence in highlight_mapping.items()
    ]
    
    # Execute all tasks
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Process results
    for result in results:
        if isinstance(result, tuple) and len(result) == 2:
            index, resource_data = result
            resources[index] = resource_data
        elif isinstance(result, Exception):
            print(f"Task failed with exception: {result}")
    
    return resources


# Utility functions for search optimization
async def batch_search_queries(queries: List[str], search_type: str = "search") -> List[List[Dict]]:
    """
    Batch multiple search queries with rate limiting.
    
    Args:
        queries: List of search queries
        search_type: Type of search
    
    Returns:
        List of search results for each query
    """
    # Limit concurrent searches to avoid rate limiting
    semaphore = asyncio.Semaphore(3)
    
    async def search_with_semaphore(query: str):
        async with semaphore:
            return await serper_search_async(query, search_type)
    
    tasks = [search_with_semaphore(query) for query in queries]
    return await asyncio.gather(*tasks, return_exceptions=True)


async def search_with_fallback(query: str, search_types: List[str] = ["search", "videos"]) -> Dict[str, List]:
    """
    Search with multiple fallback options.
    
    Args:
        query: Search query
        search_types: List of search types to try
    
    Returns:
        Dictionary with results for each search type
    """
    results = {}
    
    for search_type in search_types:
        try:
            results[search_type] = await serper_search_async(query, search_type)
        except Exception as e:
            print(f"Search type {search_type} failed for query '{query}': {e}")
            results[search_type] = []
    
    return results
