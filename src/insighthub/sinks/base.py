from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from insighthub.models import NewsItem

class BaseSink(ABC):
    """
    Abstract base class for all sinks (e.g., Markdown file, Feishu).
    
    A sink is responsible for taking the final processed data
    and rendering it to a specific output format or destination.
    """
    
    def sink_id(self) -> str:
        return self.__class__.__name__

    @abstractmethod
    async def render(self, items: List[NewsItem], curated_content: Optional[str] = None) -> Dict[str, str]:
        """
        Renders the items or the pre-rendered curated content to the sink's target.
        
        Args:
            items: A list of NewsItem objects.
            curated_content: Optional pre-rendered Markdown content (e.g., from batch AI call).

        Returns:
            Optional metadata dictionary from sink execution.
        """
        pass
