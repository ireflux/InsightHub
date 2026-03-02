import httpx
import logging
from bs4 import BeautifulSoup
from typing import List
from insighthub.sources.base import BaseSource
from insighthub.models import NewsItem

logger = logging.getLogger(__name__)

class SlashdotSource(BaseSource):
    """
    Source for fetching news from Slashdot via RSS.
    """
    
    RSS_URL = "https://rss.slashdot.org/Slashdot/slashdotMain"
    
    def __init__(
        self,
        max_items: int = 8,
        discover_timeout: float = 20.0,
        content_fetch_concurrency: int = 4,
        content_fetch_timeout: float = 10.0,
    ):
        super().__init__(
            name="Slashdot",
            max_items=max_items,
            discover_timeout=discover_timeout,
            content_fetch_concurrency=content_fetch_concurrency,
            content_fetch_timeout=content_fetch_timeout,
        )

    async def discover_raw(self) -> str:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        async with httpx.AsyncClient(timeout=self.discover_timeout, headers=headers) as client:
            try:
                response = await client.get(self.RSS_URL, follow_redirects=True)
                response.raise_for_status()
                return response.text
            except Exception as e:
                raise self.source_fetch_error(f"Slashdot fetch failed: {e}")

    def normalize_raw(self, xml_content: str) -> List[NewsItem]:
        """
        Parses the Slashdot RSS XML to extract stories.
        """
        soup = BeautifulSoup(xml_content, "xml")
        items = []
        
        for item_tag in soup.find_all("item")[:self.max_items]:
            try:
                title = item_tag.title.get_text(strip=True) if item_tag.title else "No Title"
                url = item_tag.link.get_text(strip=True) if item_tag.link else ""
                description = item_tag.description.get_text(strip=True) if item_tag.description else ""
                
                if not url:
                    continue

                items.append(NewsItem(
                    id=f"slashdot_{url}",
                    title=title,
                    url=url,
                    source=self.name,
                    content=description,
                    original_data={}
                ))
            except Exception as e:
                logger.warning(f"Failed to parse a Slashdot RSS item: {e}")
                continue
                
        return items

    async def enrich_items(self, items: List[NewsItem]) -> List[NewsItem]:
        logger.info(
            "Fetching full content for Slashdot items.",
            extra={"event": "source.enrich.start", "source": self.name, "items_count": len(items)},
        )
        contents = await self._fetch_page_contents([item.url for item in items])
        for item, full_content in zip(items, contents):
            if full_content:
                item.content = full_content
        return items
