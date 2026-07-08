import httpx
import logging
from bs4 import BeautifulSoup
from typing import List
from insighthub.core.registry import registry
from insighthub.sources.base import BaseSource
from insighthub.models import NewsItem

logger = logging.getLogger(__name__)

@registry.register_source("github_trending")
class GitHubTrendingSource(BaseSource):
    """
    Source for fetching trending repositories from GitHub.
    """
    
    TRENDING_URL = "https://github.com/trending"
    
    def __init__(
        self,
        max_items: int = 8,
        discover_timeout: float = 20.0,
        content_fetch_concurrency: int = 4,
        content_fetch_timeout: float = 10.0,
    ):
        super().__init__(
            name="GitHub Trending",
            max_items=max_items,
            discover_timeout=discover_timeout,
            content_fetch_concurrency=content_fetch_concurrency,
            content_fetch_timeout=content_fetch_timeout,
        )

    async def discover_raw(self) -> str:
        # Set a sensible timeout and User-Agent to reduce chance of being blocked
        headers = {"User-Agent": "InsightHub/1.0 (+https://github.com/your/repo)"}
        async with httpx.AsyncClient(timeout=self.discover_timeout, headers=headers) as client:
            try:
                response = await client.get(self.TRENDING_URL, follow_redirects=True)
                response.raise_for_status()
                return response.text
            except httpx.ConnectTimeout:
                raise self.source_fetch_error("Connection to GitHub timed out. Check network/proxy or increase timeout.")
            except httpx.HTTPStatusError as e:
                raise self.source_fetch_error(f"GitHub HTTP error: {e}")
            except Exception as e:
                raise self.source_fetch_error(f"GitHub fetch failed: {e}")

    def normalize_raw(self, html: str) -> List[NewsItem]:
        """
        Parses the GitHub Trending HTML to extract repository information.
        Returns a list of NewsItem items.
        """
        soup = BeautifulSoup(html, "lxml")
        items = []
        for article in soup.select("article.Box-row")[:self.max_items]:
            h2 = article.select_one("h2.h3")
            if not h2 or not h2.a:
                continue
            
            repo_link = h2.a
            repo_name = repo_link.get_text(strip=True).replace(" / ", "/")
            repo_url = f"https://github.com{repo_link['href']}"
            
            description_tag = article.select_one("p.col-9")
            description = description_tag.get_text(strip=True) if description_tag else "No description provided."

            # Extract stars and language for scoring signals
            stars = 0
            star_tag = article.select_one("a[href$='/stargazers']")
            if star_tag:
                star_text = star_tag.get_text(strip=True).replace(",", "")
                digits = "".join(ch for ch in star_text if ch.isdigit())
                if digits:
                    stars = int(digits)

            language = ""
            lang_tag = article.select_one("span[itemprop='programmingLanguage']")
            if lang_tag:
                language = lang_tag.get_text(strip=True)

            # For simplicity, we use the description as the main 'content'
            # to be summarized by the LLM. Full README is fetched in enrich_items.
            content = f"Repository: {repo_name}\n\nDescription: {description}"

            items.append(NewsItem(
                id=repo_url,
                title=repo_name,
                url=repo_url,
                source=self.name,
                content=content,
                original_data={
                    "stars": stars,
                    "language": language,
                    "description": description,
                }
            ))
        return items

    async def enrich_items(self, items: List[NewsItem]) -> List[NewsItem]:
        """Fetch README content from each repository page for richer LLM context."""
        logger.info(
            "Fetching full content for GitHub items.",
            extra={"event": "source.enrich.start", "source": self.name, "items_count": len(items)},
        )
        contents = await self._fetch_page_contents([item.url for item in items])
        for item, full_content in zip(items, contents):
            if full_content:
                base = item.content or ""
                item.content = f"{base}\n\n--- README ---\n{full_content}".strip()
        return items
