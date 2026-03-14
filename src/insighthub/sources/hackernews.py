import httpx
import logging
import re
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
    API_BASE_URL = "https://hacker-news.firebaseio.com/v0"
    
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
        top_comments_per_item = await self._fetch_top_comments_batch(items)

        for item, full_content, top_comments in zip(items, contents, top_comments_per_item):
            if full_content:
                item.content = full_content
            if top_comments:
                item.original_data = item.original_data or {}
                item.original_data["top_comments"] = top_comments
                item.original_data["discussion_url"] = f"{self.BASE_URL}item?id={item.original_data.get('story_id', '')}"

                comments_block = "\n".join(
                    f"[{one.get('author', 'anon')}]: {one.get('text', '')}"
                    for one in top_comments
                    if one.get("text")
                )
                if comments_block:
                    base = item.content or f"Hacker News Story: {item.title}\nURL: {item.url}"
                    item.content = f"{base}\n\n--- Top Comments ---\n{comments_block}"
        return items

    async def _fetch_top_comments_batch(self, items: List[NewsItem]) -> List[List[dict]]:
        headers = {"User-Agent": self.USER_AGENT}
        timeout = httpx.Timeout(self.content_fetch_timeout)
        async with httpx.AsyncClient(timeout=timeout, headers=headers) as client:
            sem = asyncio.Semaphore(self.content_fetch_concurrency)

            async def one(item: NewsItem) -> List[dict]:
                async with sem:
                    story_id = str((item.original_data or {}).get("story_id") or "").strip()
                    if not story_id.isdigit():
                        return []
                    return await self._fetch_top_comments(client, int(story_id))

            return await asyncio.gather(*(one(item) for item in items))

    async def _fetch_top_comments(self, client: httpx.AsyncClient, story_id: int, limit: int = 5) -> List[dict]:
        try:
            story_resp = await client.get(f"{self.API_BASE_URL}/item/{story_id}.json")
            story_resp.raise_for_status()
            story = story_resp.json() or {}
            comment_ids = story.get("kids", [])[:limit]
        except Exception:
            return []

        async def fetch_comment(comment_id: int) -> dict:
            try:
                resp = await client.get(f"{self.API_BASE_URL}/item/{comment_id}.json")
                resp.raise_for_status()
                data = resp.json() or {}
                text = self._clean_comment_text(str(data.get("text", "") or ""))
                if not text:
                    return {}
                return {
                    "id": data.get("id"),
                    "author": data.get("by", "anon"),
                    "text": text[:500],
                }
            except Exception:
                return {}

        rows = await asyncio.gather(*(fetch_comment(cid) for cid in comment_ids))
        return [one for one in rows if isinstance(one, dict) and one.get("text")]

    @staticmethod
    def _clean_comment_text(raw: str) -> str:
        if not raw:
            return ""
        text = BeautifulSoup(raw, "lxml").get_text(" ", strip=True)
        text = re.sub(r"\s+", " ", text).strip()
        return text
