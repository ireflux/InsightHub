import httpx
import logging
import asyncio
from typing import List, Optional
from insighthub.sources.base import BaseSource
from insighthub.models import NewsItem

logger = logging.getLogger(__name__)

class V2EXHotSource(BaseSource):
    """
    Source for fetching hot topics from V2EX.
    """
    
    API_URL = "https://www.v2ex.com/api/topics/hot.json"
    
    def __init__(self, max_items: int = 8):
        """
        Initializes the V2EXHotSource.
        
        Args:
            max_items: Maximum number of items to fetch.
        """
        super().__init__(name="V2EX Hot", max_items=max_items)
        
    async def fetch(self) -> List[NewsItem]:
        """
        Fetches hot topics from V2EX's API and returns them in the unified data format.
        """
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        async with httpx.AsyncClient(headers=headers, timeout=20.0) as client:
            try:
                response = await client.get(self.API_URL)
                response.raise_for_status()
                items = self._parse_json(response.json())
                
                # Fetch full content for top items if needed
                # Actually V2EX hot API already provides some content, but let's 
                # use _fetch_page_content to get more if it's truncated or just to be consistent.
                # However, the API content is usually good enough.
                # Let's see if we should fetch more.
                
                # For consistency with other sources, let's try to fetch full page content
                logger.info(f"Fetching full content for {len(items)} V2EX topics...")
                content_tasks = [self._fetch_page_content(item.url) for item in items]
                contents = await asyncio.gather(*content_tasks)
                
                for item, full_content in zip(items, contents):
                    if full_content:
                        item.content = full_content
                
                return items
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error occurred while fetching V2EX Hot list: {e}")
                return []
            except Exception as e:
                logger.error(f"An error occurred while fetching V2EX Hot list: {e}", exc_info=True)
                return []

    def _parse_json(self, json_data: List[dict]) -> List[NewsItem]:
        """
        Parses the JSON response from V2EX's API and returns list of NewsItem.
        """
        items = []
        for item in json_data:
            if len(items) >= self.max_items:
                break
                
            title = item.get("title", "No Title")
            url = item.get("url", "")
            if not url:
                continue

            content = item.get("content", "No content available.")
            
            items.append(NewsItem(
                id=url,
                title=title,
                url=url,
                source=self.name,
                content=content,
                original_data=item
            ))
        return items
