import logging
import re
from typing import Dict, List, Tuple

from insighthub.models import NewsItem
from insighthub.settings import ScoringConfig

logger = logging.getLogger(__name__)

COMMENT_TIERS: List[Tuple[int, str]] = [
    (200, "Explosive"),
    (80, "Hot"),
    (20, "Active"),
    (1, "Discussed"),
    (0, "No Discussion"),
]


def tier_from_score(score: float) -> str:
    comments = max(0, int(score))
    for threshold, label in COMMENT_TIERS:
        if comments >= threshold:
            return label
    return "No Discussion"


class ContentScorer:
    def __init__(self, config: ScoringConfig):
        self.config = config

    async def score_items(self, items: List[NewsItem]) -> List[NewsItem]:
        if not items:
            return items

        entries: List[Dict[str, object]] = []
        for index, item in enumerate(items):
            comment_count = self._comment_count(item)
            engagement_count = self._engagement_count(item)
            discussion_signal = self._discussion_signal(comment_count=comment_count, engagement_count=engagement_count)
            entries.append(
                {
                    "index": index,
                    "item": item,
                    "comment_count": comment_count,
                    "engagement_count": engagement_count,
                    "discussion_signal": discussion_signal,
                    "has_comments": comment_count > 0,
                }
            )

        ranked_entries = sorted(
            entries,
            key=lambda x: (
                -float(x["discussion_signal"]),
                0 if bool(x["has_comments"]) else 1,
                -int(x["engagement_count"]),
                int(x["index"]),
            ),
        )

        ranked_items: List[NewsItem] = []
        for entry in ranked_entries:
            index = int(entry["index"])
            item = entry["item"]
            comment_count = int(entry["comment_count"])
            engagement_count = int(entry["engagement_count"])
            discussion_signal = float(entry["discussion_signal"])
            base_reason = (
                "Ordered by discussion signal (comments + engagement)."
                if discussion_signal > 0
                else "Low discussion and engagement; kept lower priority."
            )
            item.discussion_signal = discussion_signal
            item.discussion_tier = tier_from_score(comment_count)
            item.discussion_breakdown = {
                "comment_count": float(comment_count),
                "engagement_count": float(engagement_count),
                "discussion_signal": float(discussion_signal),
            }
            item.ranking_reason = base_reason
            ranked_items.append(item)

        return ranked_items

    def select_items_for_summary(self, items: List[NewsItem]) -> List[NewsItem]:
        ranked = sorted(
            items,
            key=lambda x: (
                -self._discussion_signal(
                    comment_count=self._comment_count(x),
                    engagement_count=self._engagement_count(x),
                ),
                0 if self._comment_count(x) > 0 else 1,
            ),
        )
        return ranked

    @staticmethod
    def _comment_count(item: NewsItem) -> int:
        data = item.original_data or {}
        value = ContentScorer._extract_number(
            data,
            "comment_count",
            "hn_comments",
            "comments",
            "comments_count",
            "replies",
            "reply_count",
        )
        return max(0, int(value))

    @staticmethod
    def _engagement_count(item: NewsItem) -> int:
        data = item.original_data or {}
        value = ContentScorer._extract_number(
            data,
            "hn_score",
            "score",
            "points",
            "favorite_count",
            "likes",
            "upvotes",
            "views",
            "bookmarks",
        )
        return max(0, int(value))

    @staticmethod
    def _discussion_signal(*, comment_count: int, engagement_count: int) -> float:
        # Keep comments dominant while letting strong engagement slightly lift tie-breaks.
        signal = float(comment_count) + min(float(engagement_count), 500.0) * 0.08
        return round(signal, 2)

    @staticmethod
    def _extract_number(data: Dict[str, object], *keys: str) -> float:
        for key in keys:
            value = data.get(key)
            if isinstance(value, (int, float)):
                return float(value)
            if isinstance(value, str):
                match = re.search(r"[-+]?\d+(\.\d+)?", value.replace(",", ""))
                if match:
                    try:
                        return float(match.group())
                    except ValueError:
                        continue
        return 0.0
