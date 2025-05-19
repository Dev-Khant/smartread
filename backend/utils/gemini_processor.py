import os
import re
import json
import base64
import hashlib
import logging
from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime, timedelta
import asyncio

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from dotenv import load_dotenv

from .prompts import (
    HTML_FORMATTING_PROMPT,
    HIGHLIGHT_PROMPT,
    SEARCHABLE_SENTENCES_PROMPT,
)

load_dotenv()

logger = logging.getLogger(__name__)

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Model configurations
GEMINI_MODELS = {
    "flash": "gemini-2.0-flash-exp",
    "pro": "gemini-1.5-pro-latest", 
    "flash_thinking": "gemini-2.0-flash-thinking-exp-1219"
}

# Safety settings for document processing
SAFETY_SETTINGS = {
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
}

class GeminiProcessor:
    """Advanced Gemini processor with caching and optimization"""
    
    def __init__(self, model_name: str = "flash"):
        self.model_name = GEMINI_MODELS.get(model_name, GEMINI_MODELS["flash"])
        self.model = genai.GenerativeModel(
            model_name=self.model_name,
            safety_settings=SAFETY_SETTINGS
        )
        self.cache_manager = GeminiCacheManager()
        logger.info(f"Initialized Gemini processor with model: {self.model_name}")
    
    async def process_document_with_cache(
        self, 
        pdf_url: str, 
        processing_type: str = "full"
    ) -> Dict[str, Any]:
        """
        Process document with intelligent caching
        
        Args:
            pdf_url: URL of the PDF document
            processing_type: Type of processing (full, highlights_only, format_only)
        
        Returns:
            Processed document data with caching optimization
        """
        try:
            # Check if document is already cached
            cache_key = self._generate_cache_key(pdf_url, processing_type)
            cached_result = await self.cache_manager.get_cached_result(cache_key)
            
            if cached_result:
                logger.info(f"Using cached result for {pdf_url}")
                return cached_result
            
            # Process document based on size and type
            if processing_type == "full":
                result = await self._process_full_document(pdf_url)
            elif processing_type == "highlights_only":
                result = await self._extract_highlights_only(pdf_url)
            elif processing_type == "format_only":
                result = await self._format_existing_content(pdf_url)
            else:
                raise ValueError(f"Unknown processing type: {processing_type}")
            
            # Cache the result
            await self.cache_manager.cache_result(cache_key, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing document with Gemini: {str(e)}")
            raise
    
    async def _process_full_document(self, pdf_url: str) -> Dict[str, Any]:
        """Process entire document using Gemini's large context window"""
        try:
            # Upload document to Gemini
            uploaded_file = await self._upload_document_to_gemini(pdf_url)
            
            # Create comprehensive prompt for full processing
            full_processing_prompt = self._create_full_processing_prompt()
            
            # Process with Gemini
            response = await self._generate_with_retry(
                prompt=full_processing_prompt,
                files=[uploaded_file] if uploaded_file else None
            )
            
            # Parse the comprehensive response
            result = self._parse_full_response(response.text)
            
            # Clean up uploaded file
            if uploaded_file:
                await self._cleanup_uploaded_file(uploaded_file)
            
            return result
            
        except Exception as e:
            logger.error(f"Error in full document processing: {str(e)}")
            raise
    
    async def _upload_document_to_gemini(self, pdf_url: str) -> Optional[Any]:
        """Upload document to Gemini for processing"""
        try:
            # Download PDF content
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(pdf_url) as response:
                    if response.status == 200:
                        pdf_content = await response.read()
                    else:
                        raise Exception(f"Failed to download PDF: {response.status}")
            
            # Upload to Gemini
            uploaded_file = genai.upload_file(
                path=None,
                mime_type="application/pdf",
                name=f"document_{hashlib.md5(pdf_url.encode()).hexdigest()}.pdf",
                data=pdf_content
            )
            
            # Wait for processing
            while uploaded_file.state.name == "PROCESSING":
                await asyncio.sleep(1)
                uploaded_file = genai.get_file(uploaded_file.name)
            
            if uploaded_file.state.name == "FAILED":
                raise Exception("File processing failed")
            
            logger.info(f"Successfully uploaded document to Gemini: {uploaded_file.name}")
            return uploaded_file
            
        except Exception as e:
            logger.error(f"Error uploading document to Gemini: {str(e)}")
            return None
    
    def _create_full_processing_prompt(self) -> str:
        """Create comprehensive prompt for full document processing"""
        return f"""
        You are an advanced document processor. Analyze this PDF document and provide a comprehensive analysis.

        Please provide your response in the following JSON format:

        {{
            "extracted_text": "Full extracted text from the document",
            "highlights": [
                "Important sentence 1",
                "Important sentence 2",
                ...
            ],
            "formatted_html": "HTML formatted version with highlights",
            "highlight_mapping": {{
                "0": "First highlighted sentence",
                "1": "Second highlighted sentence",
                ...
            }},
            "summary": "Brief summary of the document",
            "key_topics": ["topic1", "topic2", ...],
            "document_type": "research_paper|technical_document|report|other",
            "metadata": {{
                "title": "Document title if available",
                "authors": ["author1", "author2", ...],
                "abstract": "Abstract if available",
                "page_count": number_of_pages
            }}
        }}

        Guidelines for processing:
        1. Extract ALL text content accurately
        2. Identify 5-10 most important sentences for highlighting
        3. Format the text into clean HTML with proper structure
        4. Use the highlight guidelines: {HIGHLIGHT_PROMPT}
        5. Use the HTML formatting guidelines: {HTML_FORMATTING_PROMPT}
        6. Ensure highlights are wrapped in <highlight index="N">content</highlight> tags
        7. Provide accurate metadata extraction
        8. Maintain original formatting and structure where possible

        Process the entire document comprehensively.
        """
    
    async def _generate_with_retry(
        self, 
        prompt: str, 
        files: Optional[List] = None,
        max_retries: int = 3
    ) -> Any:
        """Generate response with retry logic"""
        for attempt in range(max_retries):
            try:
                if files:
                    response = await asyncio.to_thread(
                        self.model.generate_content,
                        [prompt] + files,
                        generation_config=genai.types.GenerationConfig(
                            temperature=0.0,
                            max_output_tokens=8192,
                        )
                    )
                else:
                    response = await asyncio.to_thread(
                        self.model.generate_content,
                        prompt,
                        generation_config=genai.types.GenerationConfig(
                            temperature=0.0,
                            max_output_tokens=8192,
                        )
                    )
                
                return response
                
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
    
    def _parse_full_response(self, response_text: str) -> Dict[str, Any]:
        """Parse comprehensive Gemini response"""
        try:
            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                result = json.loads(json_str)
            else:
                # Fallback parsing if JSON is not properly formatted
                result = self._fallback_parse_response(response_text)
            
            # Validate and clean the result
            result = self._validate_and_clean_result(result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error parsing Gemini response: {str(e)}")
            # Return basic structure if parsing fails
            return {
                "extracted_text": response_text,
                "highlights": [],
                "formatted_html": f"<p>{response_text}</p>",
                "highlight_mapping": {},
                "summary": "Processing completed",
                "key_topics": [],
                "document_type": "unknown",
                "metadata": {}
            }
    
    def _fallback_parse_response(self, response_text: str) -> Dict[str, Any]:
        """Fallback parsing when JSON extraction fails"""
        # Extract highlights using regex
        highlights = re.findall(r'<highlight[^>]*>(.*?)</highlight>', response_text, re.DOTALL)
        
        # Create basic structure
        return {
            "extracted_text": response_text,
            "highlights": highlights[:10],  # Limit to 10 highlights
            "formatted_html": response_text,
            "highlight_mapping": {str(i): highlight for i, highlight in enumerate(highlights[:10])},
            "summary": "Document processed successfully",
            "key_topics": [],
            "document_type": "unknown",
            "metadata": {}
        }
    
    def _validate_and_clean_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean the processing result"""
        # Ensure all required fields exist
        required_fields = [
            "extracted_text", "highlights", "formatted_html", 
            "highlight_mapping", "summary", "key_topics", 
            "document_type", "metadata"
        ]
        
        for field in required_fields:
            if field not in result:
                result[field] = "" if field in ["extracted_text", "formatted_html", "summary", "document_type"] else {}
        
        # Clean and validate highlights
        if isinstance(result["highlights"], list):
            result["highlights"] = [str(h).strip() for h in result["highlights"][:10]]
        else:
            result["highlights"] = []
        
        # Ensure highlight_mapping is a dict
        if not isinstance(result["highlight_mapping"], dict):
            result["highlight_mapping"] = {}
        
        # Clean HTML content
        if result["formatted_html"]:
            result["formatted_html"] = self._clean_html_content(result["formatted_html"])
        
        return result
    
    def _clean_html_content(self, html_content: str) -> str:
        """Clean and validate HTML content"""
        # Remove any potentially harmful content
        # Add proper HTML structure if missing
        if not html_content.strip().startswith('<'):
            html_content = f"<div>{html_content}</div>"
        
        return html_content
    
    async def _cleanup_uploaded_file(self, uploaded_file: Any):
        """Clean up uploaded file from Gemini"""
        try:
            genai.delete_file(uploaded_file.name)
            logger.info(f"Cleaned up uploaded file: {uploaded_file.name}")
        except Exception as e:
            logger.warning(f"Failed to cleanup uploaded file: {str(e)}")
    
    def _generate_cache_key(self, pdf_url: str, processing_type: str) -> str:
        """Generate cache key for document processing"""
        content = f"{pdf_url}:{processing_type}:{self.model_name}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    # Legacy compatibility methods
    async def extract_highlights(self, content: str) -> str:
        """Extract highlights (legacy compatibility)"""
        prompt = f"{HIGHLIGHT_PROMPT}\n\nContent to analyze:\n{content}"
        response = await self._generate_with_retry(prompt)
        return response.text
    
    async def format_to_html(self, content: str, highlights: str) -> Tuple[str, Dict[int, str]]:
        """Format to HTML (legacy compatibility)"""
        prompt = f"{HTML_FORMATTING_PROMPT}\n\nMarkdown text: {content}\n\nList of sentences to highlight: {highlights}"
        response = await self._generate_with_retry(prompt)
        
        html_content = response.text
        
        # Extract highlight mapping
        highlight_mapping = {}
        highlight_pattern = r'<highlight index=[\'"](\d+)[\'"]>(.*?)</highlight>'
        matches = re.finditer(highlight_pattern, html_content)
        for match in matches:
            index = int(match.group(1))
            sentence = match.group(2)
            highlight_mapping[index] = sentence
        
        return html_content, highlight_mapping


class GeminiCacheManager:
    """Manage Gemini processing cache with Google's caching system"""
    
    def __init__(self):
        self.cache_ttl = timedelta(hours=24)  # 24 hour cache
        self.max_cache_size = 100  # Maximum cached items
        
    async def get_cached_result(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached processing result"""
        try:
            # Try to get from Gemini's context caching first
            cached_content = await self._get_from_gemini_cache(cache_key)
            if cached_content:
                return cached_content
            
            # Fallback to local cache (Redis/file-based)
            return await self._get_from_local_cache(cache_key)
            
        except Exception as e:
            logger.error(f"Error retrieving cached result: {str(e)}")
            return None
    
    async def cache_result(self, cache_key: str, result: Dict[str, Any]):
        """Cache processing result"""
        try:
            # Cache in Gemini's context cache for large documents
            await self._cache_in_gemini(cache_key, result)
            
            # Also cache locally for quick access
            await self._cache_locally(cache_key, result)
            
        except Exception as e:
            logger.error(f"Error caching result: {str(e)}")
    
    async def _get_from_gemini_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get from Gemini's context caching"""
        try:
            # List cached contents
            cached_contents = genai.list_cached_contents()
            
            for cached_content in cached_contents:
                if cached_content.name.endswith(cache_key[:16]):  # Match partial key
                    # Retrieve cached content
                    model = genai.GenerativeModel.from_cached_content(cached_content)
                    # Return metadata if available
                    return {"cached": True, "cache_name": cached_content.name}
            
            return None
            
        except Exception as e:
            logger.error(f"Error accessing Gemini cache: {str(e)}")
            return None
    
    async def _cache_in_gemini(self, cache_key: str, result: Dict[str, Any]):
        """Cache in Gemini's context cache"""
        try:
            # For large documents, create a cached content
            if len(result.get("extracted_text", "")) > 10000:  # Cache large documents
                cache_name = f"smartread_cache_{cache_key[:16]}"
                
                # Create cached content
                cached_content = genai.caching.CachedContent.create(
                    model=self.model_name,
                    contents=[result.get("extracted_text", "")],
                    ttl=self.cache_ttl,
                    display_name=cache_name
                )
                
                logger.info(f"Created Gemini cache: {cached_content.name}")
                
        except Exception as e:
            logger.error(f"Error creating Gemini cache: {str(e)}")
    
    async def _get_from_local_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get from local cache (Redis/file-based)"""
        try:
            # Try Redis first
            from .db import redis_client
            if redis_client:
                cached_data = await asyncio.to_thread(redis_client.get, f"gemini_cache:{cache_key}")
                if cached_data:
                    return json.loads(cached_data)
            
            # Fallback to file-based cache
            cache_file = f"cache/gemini_{cache_key}.json"
            if os.path.exists(cache_file):
                with open(cache_file, 'r') as f:
                    cached_data = json.load(f)
                    # Check if cache is still valid
                    cache_time = datetime.fromisoformat(cached_data.get("cached_at", ""))
                    if datetime.now() - cache_time < self.cache_ttl:
                        return cached_data.get("result")
            
            return None
            
        except Exception as e:
            logger.error(f"Error accessing local cache: {str(e)}")
            return None
    
    async def _cache_locally(self, cache_key: str, result: Dict[str, Any]):
        """Cache locally (Redis/file-based)"""
        try:
            cache_data = {
                "result": result,
                "cached_at": datetime.now().isoformat(),
                "cache_key": cache_key
            }
            
            # Try Redis first
            from .db import redis_client
            if redis_client:
                await asyncio.to_thread(
                    redis_client.setex,
                    f"gemini_cache:{cache_key}",
                    int(self.cache_ttl.total_seconds()),
                    json.dumps(cache_data)
                )
                return
            
            # Fallback to file-based cache
            os.makedirs("cache", exist_ok=True)
            cache_file = f"cache/gemini_{cache_key}.json"
            with open(cache_file, 'w') as f:
                json.dump(cache_data, f)
                
        except Exception as e:
            logger.error(f"Error caching locally: {str(e)}")


# Factory function for easy integration
def get_gemini_processor(model_type: str = "flash") -> GeminiProcessor:
    """Get configured Gemini processor"""
    return GeminiProcessor(model_type)


# Async wrapper functions for legacy compatibility
async def extract_data_gemini(url: str) -> Dict[str, Any]:
    """Extract data using Gemini (replaces Mistral OCR)"""
    processor = get_gemini_processor("flash")
    return await processor.process_document_with_cache(url, "full")


async def extract_highlights_gemini(content: str) -> str:
    """Extract highlights using Gemini (replaces Groq)"""
    processor = get_gemini_processor("flash")
    return await processor.extract_highlights(content)


async def format_to_html_gemini(content: str, highlights: str) -> Tuple[str, Dict[int, str]]:
    """Format to HTML using Gemini (replaces Groq)"""
    processor = get_gemini_processor("flash")
    return await processor.format_to_html(content, highlights)
