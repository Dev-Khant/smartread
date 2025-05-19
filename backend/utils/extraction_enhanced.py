import os
import re
import asyncio
import logging
from typing import Optional, Tuple, Dict, Any, Union
from enum import Enum

from dotenv import load_dotenv

# Import existing processors
from .extraction import (
    extract_data as extract_data_mistral,
    extract_highlights as extract_highlights_groq,
    format_to_html as format_to_html_groq
)

# Import new Gemini processor
from .gemini_processor import (
    extract_data_gemini,
    extract_highlights_gemini,
    format_to_html_gemini,
    get_gemini_processor
)

load_dotenv()

logger = logging.getLogger(__name__)

class ProcessingMode(Enum):
    """Processing mode options"""
    MISTRAL_GROQ = "mistral_groq"  # Original: Mistral OCR + Groq processing
    GEMINI_ONLY = "gemini_only"    # New: Gemini for everything
    HYBRID = "hybrid"              # Smart: Choose based on document size
    AUTO = "auto"                  # Automatic: Fallback between methods

class EnhancedExtractor:
    """Enhanced extractor with multiple AI backends"""
    
    def __init__(self, mode: ProcessingMode = ProcessingMode.AUTO):
        self.mode = mode
        self.gemini_processor = None
        self._initialize_processors()
        
    def _initialize_processors(self):
        """Initialize available processors"""
        try:
            # Check if Gemini is available
            if os.getenv("GEMINI_API_KEY"):
                self.gemini_processor = get_gemini_processor("flash")
                logger.info("Gemini processor initialized")
            else:
                logger.warning("Gemini API key not found")
                
            # Check if Mistral/Groq are available
            mistral_available = bool(os.getenv("MISTRAL_API_KEY"))
            groq_available = bool(os.getenv("GROQ_API_KEY"))
            
            if mistral_available and groq_available:
                logger.info("Mistral + Groq processors available")
            else:
                logger.warning("Mistral or Groq API keys missing")
                
        except Exception as e:
            logger.error(f"Error initializing processors: {str(e)}")
    
    async def extract_data(self, url: str) -> Dict[str, Any]:
        """
        Extract data from document using the best available method
        
        Args:
            url: Document URL
            
        Returns:
            Extracted data with metadata about processing method
        """
        try:
            # Determine processing method
            processing_method = await self._determine_processing_method(url)
            
            if processing_method == "gemini":
                logger.info(f"Processing {url} with Gemini")
                result = await self._extract_with_gemini(url)
            else:
                logger.info(f"Processing {url} with Mistral + Groq")
                result = await self._extract_with_mistral_groq(url)
            
            # Add metadata
            result["processing_method"] = processing_method
            result["processing_timestamp"] = asyncio.get_event_loop().time()
            
            return result
            
        except Exception as e:
            logger.error(f"Error extracting data: {str(e)}")
            # Try fallback method
            return await self._extract_with_fallback(url)
    
    async def _determine_processing_method(self, url: str) -> str:
        """Determine the best processing method for the document"""
        if self.mode == ProcessingMode.GEMINI_ONLY:
            return "gemini"
        elif self.mode == ProcessingMode.MISTRAL_GROQ:
            return "mistral_groq"
        elif self.mode == ProcessingMode.HYBRID:
            # Check document size/complexity
            doc_size = await self._estimate_document_size(url)
            if doc_size > 50:  # Large document (>50 pages)
                return "gemini"  # Use Gemini for large docs
            else:
                return "mistral_groq"  # Use Mistral+Groq for smaller docs
        else:  # AUTO mode
            # Try Gemini first if available, fallback to Mistral+Groq
            if self.gemini_processor and os.getenv("GEMINI_API_KEY"):
                return "gemini"
            else:
                return "mistral_groq"
    
    async def _estimate_document_size(self, url: str) -> int:
        """Estimate document size (number of pages)"""
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.head(url) as response:
                    content_length = response.headers.get('content-length')
                    if content_length:
                        # Rough estimate: 1 page ≈ 100KB
                        estimated_pages = int(content_length) // (100 * 1024)
                        return max(1, estimated_pages)
            return 10  # Default estimate
        except:
            return 10  # Default estimate
    
    async def _extract_with_gemini(self, url: str) -> Dict[str, Any]:
        """Extract using Gemini with full document processing"""
        try:
            # Use Gemini's comprehensive processing
            result = await extract_data_gemini(url)
            
            # Convert to expected format
            if isinstance(result, dict) and "extracted_text" in result:
                # Gemini returns comprehensive data
                return {
                    "pages": self._convert_gemini_to_pages(result),
                    "total_pages": result.get("metadata", {}).get("page_count", 1),
                    "processing_method": "gemini",
                    "gemini_metadata": result.get("metadata", {}),
                    "summary": result.get("summary", ""),
                    "key_topics": result.get("key_topics", [])
                }
            else:
                # Fallback if Gemini returns unexpected format
                return await self._extract_with_mistral_groq(url)
                
        except Exception as e:
            logger.error(f"Gemini extraction failed: {str(e)}")
            # Fallback to Mistral+Groq
            return await self._extract_with_mistral_groq(url)
    
    def _convert_gemini_to_pages(self, gemini_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Convert Gemini result to pages format"""
        try:
            # Create a single page object from Gemini's comprehensive result
            page = {
                "index": 0,
                "markdown": gemini_result.get("extracted_text", ""),
                "html": gemini_result.get("formatted_html", ""),
                "highlights": gemini_result.get("highlights", []),
                "highlight_mapping": gemini_result.get("highlight_mapping", {}),
                "images": [],  # Gemini handles images differently
                "dimensions": {"dpi": 72, "height": 842, "width": 595}  # Default A4
            }
            return [page]
        except Exception as e:
            logger.error(f"Error converting Gemini result: {str(e)}")
            return []
    
    async def _extract_with_mistral_groq(self, url: str) -> Dict[str, Any]:
        """Extract using Mistral OCR + Groq processing"""
        try:
            # Use original Mistral OCR
            ocr_response = await asyncio.to_thread(extract_data_mistral, url)
            
            if not ocr_response or not ocr_response.pages:
                raise Exception("No response from Mistral OCR")
            
            # Process pages with enhanced logic
            processed_pages = []
            for page in ocr_response.pages:
                # Extract highlights using Groq
                highlights = await asyncio.to_thread(extract_highlights_groq, page.markdown)
                
                # Format to HTML using Groq
                html, highlight_mapping = await asyncio.to_thread(
                    format_to_html_groq, page.markdown, highlights
                )
                
                processed_page = {
                    "index": page.index,
                    "markdown": page.markdown,
                    "html": html,
                    "highlights": list(highlight_mapping.values()),
                    "highlight_mapping": highlight_mapping,
                    "images": page.images,
                    "dimensions": page.dimensions
                }
                processed_pages.append(processed_page)
            
            return {
                "pages": processed_pages,
                "total_pages": len(processed_pages),
                "processing_method": "mistral_groq"
            }
            
        except Exception as e:
            logger.error(f"Mistral+Groq extraction failed: {str(e)}")
            raise
    
    async def _extract_with_fallback(self, url: str) -> Dict[str, Any]:
        """Fallback extraction method"""
        try:
            # Try Mistral+Groq first
            if os.getenv("MISTRAL_API_KEY") and os.getenv("GROQ_API_KEY"):
                return await self._extract_with_mistral_groq(url)
            
            # Try Gemini as fallback
            if self.gemini_processor:
                return await self._extract_with_gemini(url)
            
            # If all else fails, return basic structure
            return {
                "pages": [{
                    "index": 0,
                    "markdown": "Error: Unable to process document",
                    "html": "<p>Error: Unable to process document</p>",
                    "highlights": [],
                    "highlight_mapping": {},
                    "images": [],
                    "dimensions": {"dpi": 72, "height": 842, "width": 595}
                }],
                "total_pages": 1,
                "processing_method": "error",
                "error": "No available processors"
            }
            
        except Exception as e:
            logger.error(f"All extraction methods failed: {str(e)}")
            raise
    
    async def extract_highlights(self, content: str) -> str:
        """Extract highlights using the best available method"""
        try:
            if self.mode == ProcessingMode.GEMINI_ONLY and self.gemini_processor:
                return await extract_highlights_gemini(content)
            else:
                return await asyncio.to_thread(extract_highlights_groq, content)
        except Exception as e:
            logger.error(f"Error extracting highlights: {str(e)}")
            # Fallback
            if self.gemini_processor:
                return await extract_highlights_gemini(content)
            else:
                return await asyncio.to_thread(extract_highlights_groq, content)
    
    async def format_to_html(self, content: str, highlights: str) -> Tuple[str, Dict[int, str]]:
        """Format to HTML using the best available method"""
        try:
            if self.mode == ProcessingMode.GEMINI_ONLY and self.gemini_processor:
                return await format_to_html_gemini(content, highlights)
            else:
                return await asyncio.to_thread(format_to_html_groq, content, highlights)
        except Exception as e:
            logger.error(f"Error formatting to HTML: {str(e)}")
            # Fallback
            if self.gemini_processor:
                return await format_to_html_gemini(content, highlights)
            else:
                return await asyncio.to_thread(format_to_html_groq, content, highlights)


# Global extractor instance
_extractor = None

def get_extractor(mode: ProcessingMode = ProcessingMode.AUTO) -> EnhancedExtractor:
    """Get global extractor instance"""
    global _extractor
    if _extractor is None:
        _extractor = EnhancedExtractor(mode)
    return _extractor

# Convenience functions for easy integration
async def extract_data_enhanced(url: str, mode: str = "auto") -> Dict[str, Any]:
    """Enhanced data extraction with multiple backends"""
    processing_mode = ProcessingMode(mode) if isinstance(mode, str) else mode
    extractor = get_extractor(processing_mode)
    return await extractor.extract_data(url)

async def extract_highlights_enhanced(content: str, mode: str = "auto") -> str:
    """Enhanced highlight extraction"""
    processing_mode = ProcessingMode(mode) if isinstance(mode, str) else mode
    extractor = get_extractor(processing_mode)
    return await extractor.extract_highlights(content)

async def format_to_html_enhanced(content: str, highlights: str, mode: str = "auto") -> Tuple[str, Dict[int, str]]:
    """Enhanced HTML formatting"""
    processing_mode = ProcessingMode(mode) if isinstance(mode, str) else mode
    extractor = get_extractor(processing_mode)
    return await extractor.format_to_html(content, highlights)

# Configuration helper
def configure_processing_mode(mode: str):
    """Configure global processing mode"""
    global _extractor
    processing_mode = ProcessingMode(mode)
    _extractor = EnhancedExtractor(processing_mode)
    logger.info(f"Configured processing mode: {mode}")

# Health check for processors
async def check_processor_health() -> Dict[str, bool]:
    """Check health of all available processors"""
    health = {
        "mistral": False,
        "groq": False,
        "gemini": False
    }
    
    try:
        # Check Mistral
        if os.getenv("MISTRAL_API_KEY"):
            health["mistral"] = True
    except:
        pass
    
    try:
        # Check Groq
        if os.getenv("GROQ_API_KEY"):
            health["groq"] = True
    except:
        pass
    
    try:
        # Check Gemini
        if os.getenv("GEMINI_API_KEY"):
            health["gemini"] = True
    except:
        pass
    
    return health
