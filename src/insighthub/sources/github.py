import httpx
import logging
from bs4 import BeautifulSoup
from typing import List
from insighthub.sources.base import BaseSource
from insighthub.models import NewsItem

logger = logging.getLogger(__name__)

class GitHubTrendingSource(BaseSource):
    """
    Source for fetching trending repositories from GitHub.
    """
    
    TRENDING_URL = "https://github.com/trending"
    
    def __init__(self, max_items: int = 8):
        super().__init__(name="GitHub Trending", max_items=max_items)
        
    async def fetch(self) -> List[NewsItem]:
        """
        Fetches trending repositories from GitHub, parses them,
        and returns them in the unified data format.
        """
        # Set a sensible timeout and User-Agent to reduce chance of being blocked
        headers = {"User-Agent": "InsightHub/1.0 (+https://github.com/your/repo)"}
        async with httpx.AsyncClient(timeout=20.0, headers=headers) as client:
            try:
                response = await client.get(self.TRENDING_URL, follow_redirects=True)
                response.raise_for_status()
                return self._parse_html(response.text)
            except httpx.ConnectTimeout:
                logger.warning("An error occurred: connection to GitHub timed out. Check your network/proxy or increase the timeout.")
                return []
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error occurred: {e}")
                return []
            except Exception as e:
                logger.error(f"An error occurred: {e}", exc_info=True)
                return []

    def _parse_html(self, html: str) -> List[NewsItem]:
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
            
            # For simplicity, we use the description as the main 'content'
            # to be summarized by the LLM.
            content = f"Repository: {repo_name}\n\nDescription: {description}"

            items.append(NewsItem(
                id=repo_url,
                title=repo_name,
                url=repo_url,
                source=self.name,
                content=content,
                original_data={}
            ))
        return items