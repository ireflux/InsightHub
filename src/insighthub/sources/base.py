import logging
import asyncio
import httpx
from abc import ABC
from typing import Any, List, Optional
from bs4 import BeautifulSoup

from insighthub.errors import SourceFetchError
from insighthub.models import NewsItem

logger = logging.getLogger(__name__)

class BaseSource(ABC):
    """
    Abstract base class for all data sources (e.g., GitHub, V2EX, RSS).
    
    Each source is responsible for fetching its raw data and parsing it
    into the `NewsItem` model.
    """
    
    USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    def __init__(
        self,
        name: str,
        max_items: int = 8,
        discover_timeout: float = 20.0,
        content_fetch_concurrency: int = 4,
        content_fetch_timeout: float = 10.0,
    ):
        self.name = name
        self.max_items = max_items
        self.discover_timeout = max(discover_timeout, 1.0)
        self.content_fetch_concurrency = max(content_fetch_concurrency, 1)
        self.content_fetch_timeout = max(content_fetch_timeout, 1.0)

    async def fetch(self) -> List[NewsItem]:
        """
        Standard source pipeline:
        1) discover raw payload
        2) normalize into NewsItem list
        3) enrich items (optional)
        """
        logger.info("Source pipeline started.", extra={"event": "source.fetch.start", "source": self.name})
        raw_data = await self.discover_raw()
        items = self.normalize_raw(raw_data)
        if len(items) > self.max_items:
            items = items[:self.max_items]
        items = await self.enrich_items(items)
        logger.info(
            "Source pipeline completed.",
            extra={"event": "source.fetch.completed", "source": self.name, "items_count": len(items)},
        )
        return items

    async def discover_raw(self) -> Any:
        raise NotImplementedError(f"{self.__class__.__name__}.discover_raw is not implemented")

    def normalize_raw(self, raw_data: Any) -> List[NewsItem]:
        raise NotImplementedError(f"{self.__class__.__name__}.normalize_raw is not implemented")

    async def enrich_items(self, items: List[NewsItem]) -> List[NewsItem]:
        return items

    async def _fetch_page_content(self, url: str, client: Optional[httpx.AsyncClient] = None) -> str:
        """
        Helper to fetch and extract text content from a URL for Reading Mode.
        """
        if client is None:
            headers = {"User-Agent": self.USER_AGENT}
            timeout = httpx.Timeout(self.content_fetch_timeout)
            async with httpx.AsyncClient(timeout=timeout, headers=headers) as local_client:
                return await self._fetch_page_content(url, client=local_client)

        try:
            response = await client.get(url, follow_redirects=True)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "lxml")

            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()

            # Get text
            text = soup.get_text(separator=' ', strip=True)

            # Limit text length to avoid token issues (approx 3000 chars)
            return text[:3000]
        except Exception as e:
            logger.warning("Failed to fetch content from URL.", extra={"event": "source.content_fetch_failed", "source": self.name, "url": url, "error": str(e)})
            return ""

    async def _fetch_page_contents(self, urls: List[str]) -> List[str]:
        """
        Fetch many article pages with bounded concurrency.
        """
        if not urls:
            return []

        semaphore = asyncio.Semaphore(self.content_fetch_concurrency)
        headers = {"User-Agent": self.USER_AGENT}
        timeout = httpx.Timeout(self.content_fetch_timeout)

        async with httpx.AsyncClient(timeout=timeout, headers=headers) as client:
            async def fetch_one(url: str) -> str:
                async with semaphore:
                    return await self._fetch_page_content(url, client=client)

            return await asyncio.gather(*(fetch_one(url) for url in urls))

    @staticmethod
    def source_fetch_error(message: str) -> SourceFetchError:
        return SourceFetchError(message)
