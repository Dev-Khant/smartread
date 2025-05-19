import os
import re
import asyncio
import aiohttp
from typing import Optional, Tuple, Dict, Any
from mistralai import Mistral
from groq import Groq
from dotenv import load_dotenv

from .prompts import (
    HTML_FORMATTING_PROMPT,
    HIGHLIGHT_PROMPT,
    SEARCHABLE_SENTENCES_PROMPT,
)

load_dotenv()

MISTRAL_CLIENT = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))
GROQ_CLIENT = Groq(api_key=os.getenv("GROQ_API_KEY"))


class ExtractionError(Exception):
    """Custom exception for extraction errors"""
    pass


async def extract_data_async(url: str, max_retries: int = 3):
    """
    Async version of extract_data with retry logic and better error handling.
    
    Args:
        url (str): The URL of the document to extract text from.
        max_retries (int): Maximum number of retry attempts.
    
    Returns:
        OCR response object or raises ExtractionError.
    """
    for attempt in range(max_retries):
        try:
            # Run the blocking OCR call in a thread pool
            ocr_response = await asyncio.to_thread(
                MISTRAL_CLIENT.ocr.process,
                model="mistral-ocr-latest",
                document={"type": "document_url", "document_url": url},
                include_image_base64=True,
            )
            return ocr_response
        except Exception as e:
            if attempt == max_retries - 1:
                raise ExtractionError(f"Failed to extract data after {max_retries} attempts: {str(e)}")
            await asyncio.sleep(2 ** attempt)  # Exponential backoff


async def extract_highlights_async(content: str, max_retries: int = 3) -> str:
    """
    Async version of extract_highlights with retry logic.
    
    Args:
        content (str): The text to extract highlights from.
        max_retries (int): Maximum number of retry attempts.
    
    Returns:
        str: The extracted highlights from the text.
    """
    for attempt in range(max_retries):
        try:
            response = await asyncio.to_thread(
                GROQ_CLIENT.chat.completions.create,
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": HIGHLIGHT_PROMPT},
                    {"role": "user", "content": content},
                ],
                temperature=0.0,
            )
            return response.choices[0].message.content
        except Exception as e:
            if attempt == max_retries - 1:
                raise ExtractionError(f"Failed to extract highlights after {max_retries} attempts: {str(e)}")
            await asyncio.sleep(2 ** attempt)


async def format_to_html_async(content: str, highlights: str, max_retries: int = 3) -> Tuple[str, Dict[int, str]]:
    """
    Async version of format_to_html with retry logic.
    
    Args:
        content (str): The extracted text.
        highlights (str): The extracted highlights.
        max_retries (int): Maximum number of retry attempts.
    
    Returns:
        tuple: A tuple containing:
            - str: The formatted HTML with indexed highlight tags
            - dict: A dictionary mapping highlight indexes to their sentences
    """
    for attempt in range(max_retries):
        try:
            response = await asyncio.to_thread(
                GROQ_CLIENT.chat.completions.create,
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": HTML_FORMATTING_PROMPT},
                    {
                        "role": "user",
                        "content": f"Markdown text: {content}\n\nList of sentences to highlight: {highlights}",
                    },
                ],
                temperature=0.0,
            )
            
            html_content = response.choices[0].message.content
            
            # Extract highlight mapping
            highlight_mapping = {}
            highlight_pattern = r'<highlight index=[\'"](\d+)[\'"]>(.*?)</highlight>'
            matches = re.finditer(highlight_pattern, html_content)
            for match in matches:
                index = int(match.group(1))
                sentence = match.group(2)
                highlight_mapping[index] = sentence
            
            return html_content, highlight_mapping
        except Exception as e:
            if attempt == max_retries - 1:
                raise ExtractionError(f"Failed to format HTML after {max_retries} attempts: {str(e)}")
            await asyncio.sleep(2 ** attempt)


async def extract_searchable_sentences_async(content: str, max_retries: int = 3) -> str:
    """
    Async version of extract_searchable_sentences with retry logic.
    
    Args:
        content (str): The text to extract searchable sentences from.
        max_retries (int): Maximum number of retry attempts.
    
    Returns:
        str: The extracted searchable sentences from the text.
    """
    for attempt in range(max_retries):
        try:
            response = await asyncio.to_thread(
                GROQ_CLIENT.chat.completions.create,
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": SEARCHABLE_SENTENCES_PROMPT},
                    {"role": "user", "content": content},
                ],
                temperature=0.0,
            )
            return response.choices[0].message.content
        except Exception as e:
            if attempt == max_retries - 1:
                raise ExtractionError(f"Failed to extract searchable sentences after {max_retries} attempts: {str(e)}")
            await asyncio.sleep(2 ** attempt)


async def validate_url_async(url: str) -> bool:
    """
    Validate if URL is accessible and returns a PDF.
    
    Args:
        url (str): URL to validate
    
    Returns:
        bool: True if valid PDF URL, False otherwise
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.head(url, timeout=10) as response:
                content_type = response.headers.get('content-type', '').lower()
                return response.status == 200 and 'pdf' in content_type
    except Exception:
        return False


# Batch processing utilities
async def process_pages_batch(pages: list, url: str, batch_size: int = 3) -> list:
    """
    Process multiple pages in batches to avoid overwhelming the APIs.
    
    Args:
        pages: List of page objects to process
        url: Source URL
        batch_size: Number of pages to process concurrently
    
    Returns:
        List of processed page results
    """
    results = []
    
    for i in range(0, len(pages), batch_size):
        batch = pages[i:i + batch_size]
        batch_tasks = [
            process_single_page_async(page, url, len(pages))
            for page in batch
        ]
        
        batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
        results.extend(batch_results)
        
        # Small delay between batches to be respectful to APIs
        if i + batch_size < len(pages):
            await asyncio.sleep(1)
    
    return results


async def process_single_page_async(page, url: str, total_pages: int) -> Optional[Dict[str, Any]]:
    """
    Async version of process_single_page with better error handling.
    """
    try:
        page_number = page.index + 1
        
        # Extract highlights and format to HTML
        highlights = await extract_highlights_async(page.markdown)
        html, highlight_mapping = await format_to_html_async(page.markdown, highlights)
        
        # Process images (this could also be made async if needed)
        page_images = []
        for image in page.images:
            # Image processing logic here
            pass
        
        return {
            "page_number": page_number,
            "content": html,
            "highlights": list(highlight_mapping.values()),
            "highlight_mapping": highlight_mapping,
            "images": page_images,
            "success": True
        }
    except Exception as e:
        return {
            "page_number": page.index + 1 if hasattr(page, 'index') else 0,
            "error": str(e),
            "success": False
        }
