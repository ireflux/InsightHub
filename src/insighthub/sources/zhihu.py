import httpx
import re
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
    
    def __init__(self, keyword_filter: Optional[Pattern] = None):
        """
        Initializes the ZhihuHotSource.
        
        Args:
            keyword_filter: A compiled regex pattern to filter titles.
                            Only topics with titles matching the pattern will be fetched.
        """
        super().__init__(name="Zhihu Hot")
        self.keyword_filter = keyword_filter
        
    async def fetch(self) -> List[NewsItem]:
        """
        Fetches hot topics from Zhihu's API, filters them,
        and returns them in the unified data format.
        """
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36"
        }
        async with httpx.AsyncClient(headers=headers) as client:
            try:
                response = await client.get(self.API_URL)
                response.raise_for_status()
                return self._parse_json(response.json())
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error occurred while fetching Zhihu Hot list: {e}")
                return []
            except Exception as e:
                logger.error(f"An error occurred while fetching Zhihu Hot list: {e}", exc_info=True)
                return []

    def _parse_json(self, json_data: dict) -> List[NewsItem]:
        """
        Parses the JSON response from Zhihu's API and returns list of dict items.
        """
        items = []
        for item in json_data.get("data", []):
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