import httpx
import logging
from abc import ABC, abstractmethod
from typing import List, Optional
from bs4 import BeautifulSoup
from insighthub.models import NewsItem

logger = logging.getLogger(__name__)

class BaseSource(ABC):
    """
    Abstract base class for all data sources (e.g., GitHub, Zhihu, RSS).
    
    Each source is responsible for fetching its raw data and parsing it
    into the `NewsItem` model.
    """
    
    def __init__(self, name: str, max_items: int = 8):
        self.name = name
        self.max_items = max_items

    @abstractmethod
    async def fetch(self) -> List[NewsItem]:
        """
        The main public method for a source.
        
        It should orchestrate the process of fetching raw data, parsing it,
        and returning a list of NewsItem objects.
        
        Returns:
            A list of NewsItem objects.
        """
        pass

    async def _fetch_page_content(self, url: str) -> str:
        """
        Helper to fetch and extract text content from a URL for Reading Mode.
        """
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        async with httpx.AsyncClient(timeout=10.0, headers=headers) as client:
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
                logger.warning(f"Failed to fetch content from {url}: {e}")
                return ""