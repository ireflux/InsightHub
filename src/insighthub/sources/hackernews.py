import httpx
import logging
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
    
    def __init__(
        self,
        max_items: int = 8,
        discover_timeout: float = 20.0,
        content_fetch_concurrency: int = 4,
        content_fetch_timeout: float = 10.0,
    ):
        super().__init__(
            name="Hacker News",
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
                response = await client.get(self.BASE_URL, follow_redirects=True)
                response.raise_for_status()
                return response.text
            except Exception as e:
                raise self.source_fetch_error(f"Hacker News fetch failed: {e}")

    def normalize_raw(self, html: str) -> List[NewsItem]:
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
                subtext_row = tr.find_next_sibling("tr")
                subtext = subtext_row.select_one("td.subtext") if subtext_row else None

                hn_score = 0
                hn_comments = 0
                if subtext:
                    score_tag = subtext.select_one("span.score")
                    if score_tag:
                        score_text = score_tag.get_text(strip=True)
                        score_match = "".join(ch for ch in score_text if ch.isdigit())
                        if score_match:
                            hn_score = int(score_match)

                    for link in subtext.select("a"):
                        text = link.get_text(strip=True).lower()
                        if "comment" in text:
                            digits = "".join(ch for ch in text if ch.isdigit())
                            if digits:
                                hn_comments = int(digits)
                            break
                
                # Hacker News front page doesn't show excerpts easily without a second request per item.
                # For now, we use the title as the content context.
                content = f"Hacker News Story: {title}\nURL: {url}"

                items.append(NewsItem(
                    id=f"hn_{story_id}",
                    title=title,
                    url=url,
                    source=self.name,
                    content=content,
                    original_data={
                        "story_id": story_id,
                        "hn_score": hn_score,
                        "hn_comments": hn_comments,
                        "comment_count": hn_comments,
                    }
                ))
            except Exception as e:
                logger.warning(f"Failed to parse a Hacker News item: {e}")
                continue
                
        return items

    async def enrich_items(self, items: List[NewsItem]) -> List[NewsItem]:
        logger.info(
            "Fetching full content for Hacker News items.",
            extra={"event": "source.enrich.start", "source": self.name, "items_count": len(items)},
        )
        contents = await self._fetch_page_contents([item.url for item in items])
        for item, full_content in zip(items, contents):
            if full_content:
                item.content = full_content
        return items
