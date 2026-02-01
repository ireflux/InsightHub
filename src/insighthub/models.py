from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

class NewsItem(BaseModel):
    """
    Standard data model for a news item/article across the InsightHub system.
    """
    id: str = Field(..., description="Unique identifier for the item (usually the URL)")
    title: str = Field(..., description="Title of the article or topic")
    url: str = Field(..., description="Source URL")
    source: str = Field(..., description="Source name (e.g., 'GitHub Trending', 'Zhihu Hot')")
    content: Optional[str] = Field(None, description="Full text or main content extracted")
    summary: Optional[str] = Field(None, description="AI generated summary")
    publish_date: Optional[datetime] = Field(None, description="Publication date if available")
    original_data: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Raw data from the source")

    class Config:
        from_attributes = True
