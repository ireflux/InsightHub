import httpx
import logging
from typing import List
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

    async def discover_raw(self) -> List[dict]:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        async with httpx.AsyncClient(headers=headers, timeout=20.0) as client:
            try:
                response = await client.get(self.API_URL)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                raise self.source_fetch_error(f"V2EX HTTP error: {e}")
            except Exception as e:
                raise self.source_fetch_error(f"V2EX fetch failed: {e}")

    def normalize_raw(self, json_data: List[dict]) -> List[NewsItem]:
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

    async def enrich_items(self, items: List[NewsItem]) -> List[NewsItem]:
        logger.info(
            "Fetching full content for V2EX items.",
            extra={"event": "source.enrich.start", "source": self.name, "items_count": len(items)},
        )
        contents = await self._fetch_page_contents([item.url for item in items])
        for item, full_content in zip(items, contents):
            if full_content:
                item.content = full_content
        return items
