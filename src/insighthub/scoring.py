import json
import logging
import re
import asyncio
from typing import Any, Dict, List, Optional, Tuple

from insighthub.models import NewsItem
from insighthub.settings import ScoringConfig, RetryPolicyConfig
from insighthub.core.retry import with_retry
from insighthub.core.json_utils import parse_json_object
from insighthub.errors import LLMProcessingError

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
    def __init__(
        self,
        config: ScoringConfig,
        llm_provider=None,
        retry_policy: Optional[RetryPolicyConfig] = None,
    ):
        self.config = config
        self.llm_provider = llm_provider
        self.retry_policy = retry_policy or RetryPolicyConfig(
            max_attempts=3, base_delay_seconds=2.0
        )

    async def score_items(self, items: List[NewsItem]) -> List[NewsItem]:
        if not items:
            return items

        if self.config.use_llm_scoring and self.llm_provider is not None:
            return await self._llm_score_items(items)
        return await self._heuristic_score_items(items)

    # ---- Heuristic scoring (legacy path, unchanged) ----

    async def _heuristic_score_items(self, items: List[NewsItem]) -> List[NewsItem]:
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

    # ---- LLM scoring ----

    async def _llm_score_items(self, items: List[NewsItem]) -> List[NewsItem]:
        """Score items using LLM evaluation with concurrent processing."""
        logger.info(
            "Starting LLM-based scoring.",
            extra={"event": "engine.score.llm_start", "items_count": len(items)},
        )
        concurrency = self.config.llm_scoring_concurrency
        semaphore = asyncio.Semaphore(concurrency)

        async def score_one(item: NewsItem) -> NewsItem:
            async with semaphore:
                try:
                    return await self._llm_score_single(item)
                except Exception as e:
                    logger.warning(
                        "LLM scoring failed for item, assigning score 0.",
                        extra={"event": "engine.score.llm_failed", "item_id": item.id, "error": str(e)},
                    )
                    item.llm_quality_score = 0.0
                    item.ranking_reason = "LLM scoring failed"
                    return item

        scored_items = await asyncio.gather(*(score_one(item) for item in items))

        # Sort by LLM quality score descending
        scored_items.sort(key=lambda x: (x.llm_quality_score or 0), reverse=True)

        # Apply threshold filter
        threshold = self.config.llm_scoring_threshold
        filtered = [item for item in scored_items if (item.llm_quality_score or 0) >= threshold]

        logger.info(
            "LLM scoring completed.",
            extra={
                "event": "engine.score.llm_completed",
                "before_count": len(scored_items),
                "after_count": len(filtered),
                "threshold": threshold,
                "avg_score": round(
                    sum(item.llm_quality_score or 0 for item in scored_items) / max(len(scored_items), 1),
                    2,
                ),
            },
        )
        return filtered

    async def _llm_score_single(self, item: NewsItem) -> NewsItem:
        """Run a single LLM scoring call with retry."""
        prompt = self._llm_score_prompt(item)

        async def op() -> str:
            try:
                return await self.llm_provider.score(prompt, "{content}")
            except LLMProcessingError:
                raise
            except Exception as e:
                raise LLMProcessingError(f"LLM scoring failed: {e}") from e

        raw = await with_retry(
            op,
            logger=logger,
            operation_name=f"scoring.llm:{item.id}",
            max_attempts=self.retry_policy.max_attempts,
            base_delay_seconds=self.retry_policy.base_delay_seconds,
            backoff_multiplier=self.retry_policy.backoff_multiplier,
            max_delay_seconds=self.retry_policy.max_delay_seconds,
        )

        try:
            data = parse_json_object(raw, source_label="scoring")
            quality_score = float(data.get("quality_score", 0))
            include = bool(data.get("include", False))
            reason = str(data.get("reason", "")).strip()
        except (LLMProcessingError, ValueError, TypeError):
            quality_score = 0.0
            include = False
            reason = "Failed to parse LLM scoring response"

        item.llm_quality_score = quality_score
        item.ranking_reason = reason
        return item

    @staticmethod
    def _llm_score_prompt(item: NewsItem) -> str:
        """Build the scoring prompt for a single news item."""
        payload = {
            "id": item.id,
            "title": item.title,
            "url": item.url,
            "source": item.source,
            "content": item.content or "",
            "original_data": item.original_data or {},
            "heuristic_signal": item.discussion_signal,
            "heuristic_tier": item.discussion_tier,
        }
        return (
            "你是资深科技媒体编辑。请评估以下新闻素材的质量，决定是否值得纳入今日科技日报。\n"
            "评估维度：\n"
            "1. 内容丰富度：是否有实质性信息、数据、背景？\n"
            "2. 新闻价值：是否是重要事件、发布、突破？\n"
            "3. 独特性：是否提供了其他素材中没有的信息角度？\n"
            "4. 编辑故事潜力：是否能成为一篇好报道的核心素材？\n"
            "只输出 JSON，不要 Markdown，不要解释。\n"
            "JSON schema: {\n"
            '  "quality_score": 0-10 整数,\n'
            '  "include": true/false,\n'
            '  "reason": "一句话说明评分理由"\n'
            "}\n\n"
            f"素材：\n{json.dumps(payload, ensure_ascii=False)}"
        )

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
