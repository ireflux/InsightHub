from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field

class NewsItem(BaseModel):
    """
    Standard data model for a news item/article across the InsightHub system.
    """
    id: str = Field(..., description="Unique identifier for the item (usually the URL)")
    title: str = Field(..., description="Title of the article or topic")
    url: str = Field(..., description="Source URL")
    source: str = Field(..., description="Source name (e.g., 'GitHub Trending', 'V2EX Hot')")
    content: Optional[str] = Field(None, description="Full text or main content extracted")
    summary: Optional[str] = Field(None, description="AI generated summary")
    discussion_signal: Optional[float] = Field(None, description="Discussion heat/engagement signal")
    discussion_tier: Optional[str] = Field(None, description="Discussion tier label")
    discussion_breakdown: Dict[str, float] = Field(
        default_factory=dict,
        description="Per-dimension discussion breakdown",
    )
    ranking_reason: Optional[str] = Field(None, description="Short reason for the ranking")
    publish_date: Optional[datetime] = Field(None, description="Publication date if available")
    original_data: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Raw data from the source")
    
    # Clustering & thematic organization (v4 briefing support)
    topical_relevance_to_batch: Optional[float] = Field(
        None, description="Relevance score (0-10) to other items in batch for clustering"
    )
    cross_domain_insight_potential: Optional[float] = Field(
        None, description="Score (0-10) for cross-domain connection potential"
    )
    narrative_connectivity: Optional[float] = Field(
        None, description="Score (0-10) for narrative integration potential"
    )
    is_cluster_hub: bool = Field(
        False, description="Whether this item is a cluster hub connecting multiple topics"
    )
    suggested_topic_cluster: Optional[str] = Field(
        None, description="Suggested topic/theme clustering label"
    )
    related_item_ids: List[str] = Field(
        default_factory=list, description="List of related item IDs in the same cluster"
    )

    class Config:
        from_attributes = True
