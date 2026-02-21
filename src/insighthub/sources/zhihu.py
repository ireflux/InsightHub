import httpx
import logging
from typing import List, Pattern, Optional
from insighthub.sources.base import BaseSource
from insighthub.models import NewsItem

logger = logging.getLogger(__name__)

class ZhihuHotSource(BaseSource):
    """
    Source for fetching hot topics from Zhihu.
    """
    
    API_URL = "https://www.zhihu.com/api/v4/trending/hot_list"
    
    def __init__(self, keyword_filter: Optional[Pattern] = None, max_items: int = 8):
        """
        Initializes the ZhihuHotSource.
        
        Args:
            keyword_filter: A compiled regex pattern to filter titles.
                            Only topics with titles matching the pattern will be fetched.
            max_items: Maximum number of items to fetch.
        """
        super().__init__(name="Zhihu Hot", max_items=max_items)
        self.keyword_filter = keyword_filter

    async def discover_raw(self) -> dict:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36"
        }
        async with httpx.AsyncClient(headers=headers, timeout=20.0) as client:
            try:
                response = await client.get(self.API_URL)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                raise self.source_fetch_error(f"Zhihu HTTP error: {e}")
            except Exception as e:
                raise self.source_fetch_error(f"Zhihu fetch failed: {e}")

    def normalize_raw(self, json_data: dict) -> List[NewsItem]:
        """
        Parses the JSON response from Zhihu's API and returns list of dict items.
        """
        items = []
        for item in json_data.get("data", []):
            if len(items) >= self.max_items:
                break
                
            target = item.get("target", {})
            title = target.get("title", "No Title")
            
            # Apply keyword filter if provided
            if self.keyword_filter and not self.keyword_filter.search(title):
                continue

            url = f"https://www.zhihu.com/question/{target['id']}" if target.get('id') else item.get('url', '')
            if not url:
                continue

            excerpt = target.get("excerpt", "No excerpt available.")
            content = f"Title: {title}\n\nExcerpt: {excerpt}"
            
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
            "Fetching full content for Zhihu items.",
            extra={"event": "source.enrich.start", "source": self.name, "items_count": len(items)},
        )
        contents = await self._fetch_page_contents([item.url for item in items])
        for item, full_content in zip(items, contents):
            if full_content:
                item.content = full_content
        return items
