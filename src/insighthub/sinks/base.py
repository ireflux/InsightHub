from abc import ABC, abstractmethod
from typing import List, Optional
from insighthub.models import NewsItem

class BaseSink(ABC):
    """
    Abstract base class for all sinks (e.g., Markdown file, Feishu).
    
    A sink is responsible for taking the final processed data
    and rendering it to a specific output format or destination.
    """
    
    @abstractmethod
    async def render(self, items: List[NewsItem], curated_content: Optional[str] = None):
        """
        Renders the items or the pre-rendered curated content to the sink's target.
        
        Args:
            items: A list of NewsItem objects.
            curated_content: Optional pre-rendered Markdown content (e.g., from batch AI call).
        """
        pass
