import os
import re
import json
import base64
import requests
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
from typing import Literal, Dict, Any, List, Union

from utils.cloudinary_utils import upload_to_cloudinary


def extract_youtube_video_id(url: str) -> str:
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


def get_hd_thumbnail_base64(video_id: str) -> str:
    """Get HD thumbnail as base64 encoded string"""
    url = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
    response = requests.get(url)

    if response.status_code == 200:
        return base64.b64encode(response.content).decode("utf-8")

    # Fall back to medium quality if HD not available
    url = f"https://img.youtube.com/vi/{video_id}/mqdefault.jpg"
    response = requests.get(url)

    if response.status_code == 200:
        return base64.b64encode(response.content).decode("utf-8")

    return None


def serper_search(
    query: str,
    search_type: Literal["search", "videos"] = "search",
) -> Union[Dict[Any, Any], List[Dict[str, str]]]:
    """
    Perform a search using the Serper API for either web results or videos.

    Args:
        query (str): The search query
        search_type (str): Type of search - either "search" or "videos"
        api_key (str): Serper API key

    Returns:
        Union[dict, list]: For both search and videos returns list of formatted results
                          with relevant fields
    """
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

    try:
        response = requests.post(url, headers=headers, data=payload)
        response.raise_for_status()
        result = response.json()

        # Format video results if search_type is videos
        if search_type == "videos" and "videos" in result:
            formatted_videos = []
            if "videos" in result:
                for video in result["videos"][:5]:  # Get top 5 videos
                    video_id = extract_youtube_video_id(video.get("link", ""))
                    cloudinary_img_url = None
                    if video_id:
                        thumbnail_base64 = get_hd_thumbnail_base64(video_id)

                        # Upload image to Cloudinary
                        cloudinary_img_url = upload_to_cloudinary(
                            thumbnail_base64, f"video_{video_id}"
                        )

                    formatted_video = {
                        "title": video.get("title", ""),
                        "link": video.get("link", ""),
                        "duration": video.get("duration", ""),
                        "image_url": cloudinary_img_url,
                    }
                    formatted_videos.append(formatted_video)
            return formatted_videos

        # Format search results if search_type is search
        elif search_type == "search" and "organic" in result:
            formatted_results = []
            if "organic" in result:
                for item in result["organic"][:5]:  # Get top 5 search results
                    formatted_result = {
                        "title": item.get("title", ""),
                        "link": item.get("link", ""),
                        "snippet": item.get("snippet", ""),
                    }
                    formatted_results.append(formatted_result)
            return formatted_results

        return result
    except requests.exceptions.RequestException as e:
        raise Exception(f"Search request failed: {str(e)}")


def prepare_resources(highlight_mapping: dict):
    """
    Prepare resources for search based on highlight mapping, running searches in parallel.

    Args:
        highlight_mapping (dict): A dictionary mapping highlight indexes to their sentences

    Returns:
        dict: A dictionary of resources indexed by highlight index
    """
    resources = {}

    def search_both_types(sentence):
        """Helper function to perform both search types for a sentence in parallel"""
        with ThreadPoolExecutor() as inner_executor:
            article_future = inner_executor.submit(serper_search, sentence, "search")
            video_future = inner_executor.submit(serper_search, sentence, "videos")

            # Wait for both to complete and return results
            return article_future.result(), video_future.result()

    # Use ThreadPoolExecutor to run searches in parallel
    with ThreadPoolExecutor() as executor:
        future_to_index = {
            executor.submit(search_both_types, sentence): index
            for index, sentence in highlight_mapping.items()
        }

        for future in concurrent.futures.as_completed(future_to_index):
            index = future_to_index[future]
            articles, videos = future.result()
            resources[index] = {"articles": articles, "videos": videos}

    return resources
