from abc import ABC, abstractmethod
from typing import List
from insighthub.models import NewsItem

class BaseSource(ABC):
    """
    Abstract base class for all data sources (e.g., GitHub, Zhihu, RSS).
    
    Each source is responsible for fetching its raw data and parsing it
    into the `NewsItem` model.
    """
    
    def __init__(self, name: str):
        self.name = name

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