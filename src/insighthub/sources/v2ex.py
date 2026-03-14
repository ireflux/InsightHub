import httpx
import logging
import asyncio
from typing import List
from insighthub.sources.base import BaseSource
from insighthub.models import NewsItem

logger = logging.getLogger(__name__)

class V2EXHotSource(BaseSource):
    """
    Source for fetching hot topics from V2EX.
    """
    
    API_URL = "https://www.v2ex.com/api/topics/hot.json"
    REPLIES_API_URL = "https://www.v2ex.com/api/replies/show.json"
    
    def __init__(
        self,
        max_items: int = 8,
        discover_timeout: float = 20.0,
        content_fetch_concurrency: int = 4,
        content_fetch_timeout: float = 10.0,
    ):
        """
        Initializes the V2EXHotSource.
        
        Args:
            max_items: Maximum number of items to fetch.
        """
        super().__init__(
            name="V2EX Hot",
            max_items=max_items,
            discover_timeout=discover_timeout,
            content_fetch_concurrency=content_fetch_concurrency,
            content_fetch_timeout=content_fetch_timeout,
        )

    async def discover_raw(self) -> List[dict]:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        async with httpx.AsyncClient(headers=headers, timeout=self.discover_timeout) as client:
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
                original_data={**item, "comment_count": int(item.get("replies", 0) or 0)}
            ))
        return items

    async def enrich_items(self, items: List[NewsItem]) -> List[NewsItem]:
        logger.info(
            "Fetching full content for V2EX items.",
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
                item.original_data["discussion_url"] = item.url

                comments_block = "\n".join(
                    f"[{one.get('author', 'anon')}]: {one.get('text', '')}"
                    for one in top_comments
                    if one.get("text")
                )
                if comments_block:
                    base = item.content or ""
                    item.content = f"{base}\n\n--- Top Comments ---\n{comments_block}".strip()
        return items

    async def _fetch_top_comments_batch(self, items: List[NewsItem]) -> List[List[dict]]:
        headers = {"User-Agent": self.USER_AGENT}
        timeout = httpx.Timeout(self.content_fetch_timeout)
        async with httpx.AsyncClient(headers=headers, timeout=timeout) as client:
            sem = asyncio.Semaphore(self.content_fetch_concurrency)

            async def one(item: NewsItem) -> List[dict]:
                async with sem:
                    topic_id = self._topic_id(item)
                    if topic_id <= 0:
                        return []
                    return await self._fetch_topic_comments(client, topic_id=topic_id)

            return await asyncio.gather(*(one(item) for item in items))

    async def _fetch_topic_comments(self, client: httpx.AsyncClient, topic_id: int, limit: int = 5) -> List[dict]:
        try:
            resp = await client.get(self.REPLIES_API_URL, params={"topic_id": topic_id})
            resp.raise_for_status()
            rows = resp.json() or []
        except Exception:
            return []
        if not isinstance(rows, list):
            return []

        comments: List[dict] = []
        for row in rows[:limit]:
            if not isinstance(row, dict):
                continue
            content = str(row.get("content", "")).strip()
            if not content:
                continue
            comments.append(
                {
                    "id": row.get("id"),
                    "author": str((row.get("member") or {}).get("username", "")).strip() or "anon",
                    "text": content[:500],
                }
            )
        return comments

    @staticmethod
    def _topic_id(item: NewsItem) -> int:
        data = item.original_data or {}
        raw = data.get("id")
        try:
            return int(raw)
        except Exception:
            return 0
