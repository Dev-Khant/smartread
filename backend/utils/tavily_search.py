import os
import json
import asyncio
import aiohttp
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
import hashlib
from concurrent.futures import ThreadPoolExecutor

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class TavilySearchClient:
    """Enhanced Tavily search client with caching and optimization"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("TAVILY_API_KEY")
        self.base_url = "https://api.tavily.com"
        self.session = None
        self.cache = {}
        self.cache_ttl = timedelta(hours=6)  # Cache results for 6 hours
        
        if not self.api_key:
            logger.warning("Tavily API key not found. Search functionality will be limited.")
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def search(
        self,
        query: str,
        search_depth: str = "basic",
        topic: str = "general",
        max_results: int = 5,
        include_domains: Optional[List[str]] = None,
        exclude_domains: Optional[List[str]] = None,
        include_answer: bool = True,
        include_raw_content: bool = False,
        include_images: bool = True
    ) -> Dict[str, Any]:
        """
        Perform search using Tavily API
        
        Args:
            query: Search query
            search_depth: "basic" or "advanced"
            topic: "general" or "news"
            max_results: Maximum number of results (1-20)
            include_domains: List of domains to include
            exclude_domains: List of domains to exclude
            include_answer: Include AI-generated answer
            include_raw_content: Include raw content
            include_images: Include images in results
        
        Returns:
            Search results from Tavily
        """
        if not self.api_key:
            logger.error("Tavily API key not configured")
            return {"error": "Tavily API key not configured"}
        
        # Check cache first
        cache_key = self._generate_cache_key(query, search_depth, topic, max_results)
        cached_result = self._get_from_cache(cache_key)
        if cached_result:
            logger.info(f"Using cached result for query: {query}")
            return cached_result
        
        # Prepare request payload
        payload = {
            "api_key": self.api_key,
            "query": query,
            "search_depth": search_depth,
            "topic": topic,
            "max_results": max_results,
            "include_answer": include_answer,
            "include_raw_content": include_raw_content,
            "include_images": include_images
        }
        
        if include_domains:
            payload["include_domains"] = include_domains
        if exclude_domains:
            payload["exclude_domains"] = exclude_domains
        
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            async with self.session.post(
                f"{self.base_url}/search",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    # Cache the result
                    self._cache_result(cache_key, result)
                    logger.info(f"Successfully searched for: {query}")
                    return result
                else:
                    error_text = await response.text()
                    logger.error(f"Tavily search failed: {response.status} - {error_text}")
                    return {"error": f"Search failed: {response.status}"}
                    
        except asyncio.TimeoutError:
            logger.error(f"Tavily search timeout for query: {query}")
            return {"error": "Search timeout"}
        except Exception as e:
            logger.error(f"Tavily search error: {str(e)}")
            return {"error": str(e)}
    
    async def search_news(
        self,
        query: str,
        max_results: int = 5,
        days: int = 7
    ) -> Dict[str, Any]:
        """
        Search for recent news articles
        
        Args:
            query: Search query
            max_results: Maximum number of results
            days: Number of days to look back
        
        Returns:
            News search results
        """
        return await self.search(
            query=query,
            search_depth="basic",
            topic="news",
            max_results=max_results
        )
    
    async def search_academic(
        self,
        query: str,
        max_results: int = 5
    ) -> Dict[str, Any]:
        """
        Search for academic content
        
        Args:
            query: Search query
            max_results: Maximum number of results
        
        Returns:
            Academic search results
        """
        # Include academic domains
        academic_domains = [
            "arxiv.org",
            "scholar.google.com",
            "pubmed.ncbi.nlm.nih.gov",
            "ieee.org",
            "acm.org",
            "springer.com",
            "sciencedirect.com",
            "nature.com",
            "science.org"
        ]
        
        return await self.search(
            query=query,
            search_depth="advanced",
            max_results=max_results,
            include_domains=academic_domains
        )
    
    async def search_videos(
        self,
        query: str,
        max_results: int = 5
    ) -> Dict[str, Any]:
        """
        Search for video content
        
        Args:
            query: Search query
            max_results: Maximum number of results
        
        Returns:
            Video search results
        """
        # Include video platforms
        video_domains = [
            "youtube.com",
            "vimeo.com",
            "dailymotion.com"
        ]
        
        # Add video-specific terms to query
        video_query = f"{query} video tutorial explanation"
        
        return await self.search(
            query=video_query,
            search_depth="basic",
            max_results=max_results,
            include_domains=video_domains,
            include_images=True
        )
    
    def _generate_cache_key(self, query: str, search_depth: str, topic: str, max_results: int) -> str:
        """Generate cache key for search query"""
        content = f"{query}:{search_depth}:{topic}:{max_results}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _get_from_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get result from cache"""
        if cache_key in self.cache:
            cached_item = self.cache[cache_key]
            if datetime.now() - cached_item["timestamp"] < self.cache_ttl:
                return cached_item["result"]
            else:
                # Remove expired cache
                del self.cache[cache_key]
        return None
    
    def _cache_result(self, cache_key: str, result: Dict[str, Any]):
        """Cache search result"""
        self.cache[cache_key] = {
            "result": result,
            "timestamp": datetime.now()
        }
        
        # Limit cache size
        if len(self.cache) > 100:
            # Remove oldest entries
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k]["timestamp"])
            del self.cache[oldest_key]


class SmartReadTavilyIntegration:
    """SmartRead integration with Tavily for enhanced search"""
    
    def __init__(self):
        self.tavily_client = TavilySearchClient()
        self.executor = ThreadPoolExecutor(max_workers=5)
    
    async def prepare_resources_enhanced(
        self,
        highlight_mapping: Dict[int, str],
        max_concurrent: int = 3
    ) -> Dict[int, Dict[str, Any]]:
        """
        Enhanced resource preparation using Tavily
        
        Args:
            highlight_mapping: Dictionary mapping highlight indexes to sentences
            max_concurrent: Maximum concurrent searches
        
        Returns:
            Dictionary of resources indexed by highlight index
        """
        resources = {}
        
        # Create semaphore to limit concurrent operations
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def search_for_highlight(index: int, sentence: str):
            async with semaphore:
                try:
                    # Search for articles and videos concurrently
                    async with self.tavily_client:
                        articles_task = self._search_articles(sentence)
                        videos_task = self._search_videos(sentence)
                        academic_task = self._search_academic(sentence)
                        
                        articles, videos, academic = await asyncio.gather(
                            articles_task, videos_task, academic_task,
                            return_exceptions=True
                        )
                    
                    # Handle exceptions
                    if isinstance(articles, Exception):
                        articles = []
                    if isinstance(videos, Exception):
                        videos = []
                    if isinstance(academic, Exception):
                        academic = []
                    
                    return index, {
                        "articles": articles,
                        "videos": videos,
                        "academic": academic,
                        "query": sentence
                    }
                    
                except Exception as e:
                    logger.error(f"Error searching for highlight {index}: {str(e)}")
                    return index, {
                        "articles": [],
                        "videos": [],
                        "academic": [],
                        "query": sentence,
                        "error": str(e)
                    }
        
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
                logger.error(f"Task failed with exception: {result}")
        
        return resources
    
    async def _search_articles(self, query: str) -> List[Dict[str, Any]]:
        """Search for articles related to the query"""
        try:
            result = await self.tavily_client.search(
                query=query,
                search_depth="basic",
                max_results=3,
                include_answer=True,
                exclude_domains=["youtube.com", "vimeo.com"]  # Exclude video sites
            )
            
            if "error" in result:
                logger.error(f"Article search error: {result['error']}")
                return []
            
            articles = []
            for item in result.get("results", [])[:3]:
                article = {
                    "title": item.get("title", ""),
                    "link": item.get("url", ""),
                    "snippet": item.get("content", "")[:200] + "...",
                    "score": item.get("score", 0),
                    "published_date": item.get("published_date", "")
                }
                articles.append(article)
            
            # Add AI-generated answer if available
            if result.get("answer"):
                articles.insert(0, {
                    "title": "AI Summary",
                    "link": "#",
                    "snippet": result["answer"][:200] + "...",
                    "score": 1.0,
                    "type": "ai_summary"
                })
            
            return articles
            
        except Exception as e:
            logger.error(f"Error searching articles: {str(e)}")
            return []
    
    async def _search_videos(self, query: str) -> List[Dict[str, Any]]:
        """Search for videos related to the query"""
        try:
            result = await self.tavily_client.search_videos(query, max_results=3)
            
            if "error" in result:
                logger.error(f"Video search error: {result['error']}")
                return []
            
            videos = []
            for item in result.get("results", [])[:3]:
                # Extract video information
                video = {
                    "title": item.get("title", ""),
                    "link": item.get("url", ""),
                    "snippet": item.get("content", "")[:200] + "...",
                    "score": item.get("score", 0),
                    "thumbnail": self._extract_video_thumbnail(item.get("url", "")),
                    "duration": self._extract_video_duration(item.get("content", ""))
                }
                videos.append(video)
            
            return videos
            
        except Exception as e:
            logger.error(f"Error searching videos: {str(e)}")
            return []
    
    async def _search_academic(self, query: str) -> List[Dict[str, Any]]:
        """Search for academic content related to the query"""
        try:
            result = await self.tavily_client.search_academic(query, max_results=2)
            
            if "error" in result:
                logger.error(f"Academic search error: {result['error']}")
                return []
            
            academic = []
            for item in result.get("results", [])[:2]:
                paper = {
                    "title": item.get("title", ""),
                    "link": item.get("url", ""),
                    "snippet": item.get("content", "")[:200] + "...",
                    "score": item.get("score", 0),
                    "published_date": item.get("published_date", ""),
                    "type": "academic"
                }
                academic.append(paper)
            
            return academic
            
        except Exception as e:
            logger.error(f"Error searching academic content: {str(e)}")
            return []
    
    def _extract_video_thumbnail(self, url: str) -> Optional[str]:
        """Extract video thumbnail URL"""
        try:
            if "youtube.com" in url or "youtu.be" in url:
                # Extract YouTube video ID
                import re
                patterns = [
                    r"(?:youtube\.com\/watch\?v=|youtu.be\/)([^&\n?]*)",
                    r"youtube.com/embed/([^&\n?]*)",
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, url)
                    if match:
                        video_id = match.group(1)
                        return f"https://img.youtube.com/vi/{video_id}/mqdefault.jpg"
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting video thumbnail: {str(e)}")
            return None
    
    def _extract_video_duration(self, content: str) -> Optional[str]:
        """Extract video duration from content"""
        try:
            # Look for duration patterns in content
            import re
            duration_patterns = [
                r"(\d+:\d+:\d+)",  # HH:MM:SS
                r"(\d+:\d+)",      # MM:SS
                r"(\d+)\s*minutes?",  # X minutes
                r"(\d+)\s*hours?",    # X hours
            ]
            
            for pattern in duration_patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    return match.group(1)
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting video duration: {str(e)}")
            return None
    
    async def search_related_topics(self, main_topic: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Search for topics related to the main topic"""
        try:
            # Generate related search queries
            related_queries = [
                f"{main_topic} tutorial",
                f"{main_topic} examples",
                f"{main_topic} applications",
                f"{main_topic} research",
                f"latest {main_topic} developments"
            ]
            
            all_results = []
            async with self.tavily_client:
                for query in related_queries[:3]:  # Limit to 3 related searches
                    result = await self.tavily_client.search(
                        query=query,
                        max_results=2,
                        search_depth="basic"
                    )
                    
                    if "error" not in result:
                        for item in result.get("results", []):
                            all_results.append({
                                "title": item.get("title", ""),
                                "link": item.get("url", ""),
                                "snippet": item.get("content", "")[:150] + "...",
                                "score": item.get("score", 0),
                                "query": query
                            })
            
            # Sort by score and return top results
            all_results.sort(key=lambda x: x.get("score", 0), reverse=True)
            return all_results[:max_results]
            
        except Exception as e:
            logger.error(f"Error searching related topics: {str(e)}")
            return []
    
    async def get_topic_summary(self, topic: str) -> Optional[str]:
        """Get AI-generated summary for a topic"""
        try:
            async with self.tavily_client:
                result = await self.tavily_client.search(
                    query=f"What is {topic}? Explain {topic}",
                    search_depth="advanced",
                    max_results=1,
                    include_answer=True
                )
            
            if "error" not in result and result.get("answer"):
                return result["answer"]
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting topic summary: {str(e)}")
            return None


# Global instance for easy access
tavily_integration = SmartReadTavilyIntegration()

# Convenience functions
async def prepare_resources_tavily(highlight_mapping: Dict[int, str]) -> Dict[int, Dict[str, Any]]:
    """Prepare resources using Tavily (replaces Serper)"""
    return await tavily_integration.prepare_resources_enhanced(highlight_mapping)

async def search_related_content(query: str, content_type: str = "all") -> List[Dict[str, Any]]:
    """Search for related content using Tavily"""
    async with TavilySearchClient() as client:
        if content_type == "articles":
            result = await client.search(query, max_results=5)
        elif content_type == "videos":
            result = await client.search_videos(query, max_results=5)
        elif content_type == "academic":
            result = await client.search_academic(query, max_results=5)
        else:
            result = await client.search(query, max_results=5)
        
        return result.get("results", [])

async def get_ai_summary(query: str) -> Optional[str]:
    """Get AI-generated summary using Tavily"""
    async with TavilySearchClient() as client:
        result = await client.search(query, include_answer=True, max_results=1)
        return result.get("answer")

# Health check
async def check_tavily_health() -> bool:
    """Check if Tavily API is accessible"""
    try:
        async with TavilySearchClient() as client:
            result = await client.search("test", max_results=1)
            return "error" not in result
    except:
        return False
