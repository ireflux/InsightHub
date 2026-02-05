import httpx
import logging
import asyncio
from bs4 import BeautifulSoup
from typing import List
from insighthub.sources.base import BaseSource
from insighthub.models import NewsItem

logger = logging.getLogger(__name__)

class HackerNewsSource(BaseSource):
    """
    Source for fetching top stories from Hacker News.
    """
    
    BASE_URL = "https://news.ycombinator.com/"
    
    def __init__(self, max_items: int = 8):
        super().__init__(name="Hacker News", max_items=max_items)
        
    async def fetch(self) -> List[NewsItem]:
        """
        Fetches top stories from Hacker News and returns them as NewsItem objects.
        Now fetches full content for each item to support Reading Mode.
        """
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        async with httpx.AsyncClient(timeout=20.0, headers=headers) as client:
            try:
                response = await client.get(self.BASE_URL, follow_redirects=True)
                response.raise_for_status()
                items = self._parse_html(response.text)
                
                # Fetch full content for each item in parallel to support Reading Mode
                logger.info(f"Fetching full content for {len(items)} Hacker News items...")
                content_tasks = [self._fetch_page_content(item.url) for item in items]
                contents = await asyncio.gather(*content_tasks)
                
                for item, full_content in zip(items, contents):
                    if full_content:
                        item.content = full_content
                
                return items
            except Exception as e:
                logger.error(f"An error occurred while fetching Hacker News: {e}", exc_info=True)
                return []

    def _parse_html(self, html: str) -> List[NewsItem]:
        """
        Parses the Hacker News HTML to extract stories.
        """
        soup = BeautifulSoup(html, "lxml")
        items = []
        
        # Each story is in a <tr class="athing">
        for tr in soup.select("tr.athing")[:self.max_items]:
            try:
                title_line = tr.select_one("span.titleline")
                if not title_line or not title_line.a:
                    continue
                
                a_tag = title_line.a
                title = a_tag.get_text(strip=True)
                url = a_tag["href"]
                
                # If it's a relative URL (HN internal link), prepend the base URL
                if url.startswith("item?id="):
                    url = f"{self.BASE_URL}{url}"
                
                story_id = tr.get("id", url)
                
                # Hacker News front page doesn't show excerpts easily without a second request per item.
                # For now, we use the title as the content context.
                content = f"Hacker News Story: {title}\nURL: {url}"

                items.append(NewsItem(
                    id=f"hn_{story_id}",
                    title=title,
                    url=url,
                    source=self.name,
                    content=content,
                    original_data={}
                ))
            except Exception as e:
                logger.warning(f"Failed to parse a Hacker News item: {e}")
                continue
                
        return items
