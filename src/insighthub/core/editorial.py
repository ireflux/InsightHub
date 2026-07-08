import asyncio
import json
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from insighthub.core.retry import with_retry
from insighthub.core.json_utils import parse_json_object
from insighthub.errors import LLMProcessingError
from insighthub.llm_providers.base import BaseLLMProvider
from insighthub.models import NewsItem
from insighthub.settings import RetryPolicyConfig

logger = logging.getLogger(__name__)


@dataclass
class ItemBrief:
    item_id: str
    title: str
    url: str
    source: str
    core_facts: List[str] = field(default_factory=list)
    context: List[str] = field(default_factory=list)
    discussion_signals: List[str] = field(default_factory=list)
    uncertainties: List[str] = field(default_factory=list)
    editorial_score: float = 0.0
    include: bool = True
    reason: str = ""
    content_snippet: str = ""
    top_comments: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "item_id": self.item_id,
            "title": self.title,
            "url": self.url,
            "source": self.source,
            "core_facts": self.core_facts,
            "context": self.context,
            "discussion_signals": self.discussion_signals,
            "uncertainties": self.uncertainties,
            "editorial_score": self.editorial_score,
            "include": self.include,
            "reason": self.reason,
            "content_snippet": self.content_snippet,
            "top_comments": self.top_comments,
        }


@dataclass
class StoryCluster:
    title: str
    primary_item_id: str
    item_ids: List[str]
    angle: str
    include: bool = True
    reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "primary_item_id": self.primary_item_id,
            "item_ids": self.item_ids,
            "angle": self.angle,
            "include": self.include,
            "reason": self.reason,
        }


@dataclass
class ReviewResult:
    passed: bool
    issues: List[str] = field(default_factory=list)
    revision_instructions: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "passed": self.passed,
            "issues": self.issues,
            "revision_instructions": self.revision_instructions,
        }


class EditorialPipeline:
    def __init__(
        self,
        llm_provider: BaseLLMProvider,
        final_prompt_template: str,
        *,
        brief_prompt_template: str = "{content}",
        cluster_prompt_template: str = "{content}",
        review_prompt_template: str = "{content}",
        revision_prompt_template: str = "{content}",
        brief_concurrency: int = 4,
        max_briefs: int = 12,
        min_final_items: int = 3,
        max_final_items: int = 8,
        review_enabled: bool = True,
        revise_enabled: bool = True,
        retry_policy: Optional[RetryPolicyConfig] = None,
    ):
        self.llm_provider = llm_provider
        self.final_prompt_template = final_prompt_template
        self.brief_prompt_template = brief_prompt_template
        self.cluster_prompt_template = cluster_prompt_template
        self.review_prompt_template = review_prompt_template
        self.revision_prompt_template = revision_prompt_template
        self.brief_concurrency = max(1, brief_concurrency)
        self.max_briefs = max(1, max_briefs)
        self.min_final_items = max(1, min_final_items)
        self.max_final_items = max(self.min_final_items, max_final_items)
        self.review_enabled = review_enabled
        self.revise_enabled = revise_enabled
        self.retry_policy = retry_policy or RetryPolicyConfig(
            max_attempts=3, base_delay_seconds=2.0
        )

    async def run(self, items: List[NewsItem]) -> Dict[str, Any]:
        candidate_items = items[: self.max_briefs]
        briefs = await self.build_briefs(candidate_items)
        clusters = await self.plan_clusters(briefs)
        selected_items = self.selected_items(items, clusters)
        article_input = self.build_article_input(briefs, clusters, selected_items)
        draft = await self._summarize(article_input, self.final_prompt_template, operation_name="summarize")
        review = ReviewResult(passed=True)
        final_article = draft
        if self.review_enabled:
            review = await self.review_article(final_article, article_input)
            if self.revise_enabled and not review.passed:
                final_article = await self.revise_article(final_article, article_input, review)
        return {
            "briefs": briefs,
            "clusters": clusters,
            "selected_items": selected_items,
            "article_input": article_input,
            "draft": draft,
            "review": review,
            "final_article": final_article,
        }

    async def _summarize(self, content: str, prompt_template: str, *, operation_name: str) -> str:
        """Run a single editorial LLM call with its own retry budget.

        Retry is scoped per step so a transient failure on (say) the review call
        does not force the whole pipeline (briefs + clustering + drafting) to
        restart from scratch.
        """

        async def op() -> str:
            try:
                return await self.llm_provider.summarize(content, prompt_template)
            except LLMProcessingError:
                raise
            except Exception as e:
                raise LLMProcessingError(f"Editorial {operation_name} failed: {e}") from e

        return await with_retry(
            op,
            logger=logger,
            operation_name=f"editorial.{operation_name}",
            max_attempts=self.retry_policy.max_attempts,
            base_delay_seconds=self.retry_policy.base_delay_seconds,
            backoff_multiplier=self.retry_policy.backoff_multiplier,
            max_delay_seconds=self.retry_policy.max_delay_seconds,
        )

    async def build_briefs(self, items: List[NewsItem]) -> List[ItemBrief]:
        semaphore = asyncio.Semaphore(self.brief_concurrency)

        async def one(item: NewsItem) -> ItemBrief:
            async with semaphore:
                return await self._build_brief(item)

        return await asyncio.gather(*(one(item) for item in items))

    async def _build_brief(self, item: NewsItem) -> ItemBrief:
        payload = self._brief_payload(item)
        raw = await self._summarize(payload, self.brief_prompt_template, operation_name=f"brief:{item.id}")
        data = parse_json_object(raw, source_label="editorial brief")
        return ItemBrief(
            item_id=item.id,
            title=item.title,
            url=item.url,
            source=item.source,
            core_facts=_string_list(data.get("core_facts")),
            context=_string_list(data.get("context")),
            discussion_signals=_string_list(data.get("discussion_signals")),
            uncertainties=_string_list(data.get("uncertainties")),
            editorial_score=_float_in_range(data.get("editorial_score"), 0.0, 10.0),
            include=bool(data.get("include", True)),
            reason=str(data.get("reason", "")).strip(),
            content_snippet=str(data.get("content_snippet", "")).strip(),
            top_comments=_string_list(data.get("top_comments")),
        )

    async def plan_clusters(self, briefs: List[ItemBrief]) -> List[StoryCluster]:
        if not briefs:
            return []
        raw = await self._summarize(self._cluster_payload(briefs), self.cluster_prompt_template, operation_name="plan_clusters")
        data = parse_json_object(raw, source_label="editorial cluster")
        clusters_data = data.get("clusters")
        clusters: List[StoryCluster] = []
        if isinstance(clusters_data, list):
            valid_ids = {brief.item_id for brief in briefs}
            for entry in clusters_data:
                if not isinstance(entry, dict):
                    continue
                item_ids = [x for x in _string_list(entry.get("item_ids")) if x in valid_ids]
                if not item_ids:
                    continue
                primary_item_id = str(entry.get("primary_item_id") or item_ids[0])
                if primary_item_id not in item_ids:
                    primary_item_id = item_ids[0]
                clusters.append(
                    StoryCluster(
                        title=str(entry.get("title") or "未命名主题").strip(),
                        primary_item_id=primary_item_id,
                        item_ids=item_ids,
                        angle=str(entry.get("angle") or "").strip(),
                        include=bool(entry.get("include", True)),
                        reason=str(entry.get("reason") or "").strip(),
                    )
                )
        if clusters:
            return clusters[: self.max_final_items]
        return self._fallback_clusters(briefs)

    def selected_items(self, original_items: List[NewsItem], clusters: List[StoryCluster]) -> List[NewsItem]:
        id_to_item = {item.id: item for item in original_items}
        selected_ids: List[str] = []
        for cluster in clusters:
            if not cluster.include:
                continue
            for item_id in cluster.item_ids:
                if item_id not in selected_ids and item_id in id_to_item:
                    selected_ids.append(item_id)
        return [id_to_item[item_id] for item_id in selected_ids]

    def build_article_input(
        self,
        briefs: List[ItemBrief],
        clusters: List[StoryCluster],
        selected_items: List[NewsItem],
    ) -> str:
        brief_map = {brief.item_id: brief for brief in briefs}
        item_map = {item.id: item for item in selected_items}
        sections = [
            "以下是经过单条理解、编辑取舍和主题合并后的素材。请严格基于这些素材写作。",
            "允许最终文章根据材料质量动态决定条目数量；不要硬凑。",
            "每条新闻标题必须链接到对应 primary URL。",
            "每条素材包含核心内容片段(content_snippet)和精选社区评论(top_comments)，可作为写作参考。",
            "",
        ]
        for index, cluster in enumerate([c for c in clusters if c.include], start=1):
            primary_item = item_map.get(cluster.primary_item_id)
            primary_url = primary_item.url if primary_item else ""
            sections.append(f"--- Story {index} ---")
            sections.append(f"Suggested Title: {cluster.title}")
            sections.append(f"Primary URL: {primary_url}")
            sections.append(f"Editorial Angle: {cluster.angle}")
            sections.append(f"Selection Reason: {cluster.reason}")
            sections.append("Briefs:")
            for item_id in cluster.item_ids:
                brief = brief_map.get(item_id)
                if not brief:
                    continue
                sections.append(json.dumps(brief.to_dict(), ensure_ascii=False))
            sections.append("")
        return "\n".join(sections).strip()

    async def review_article(self, article: str, article_input: str) -> ReviewResult:
        raw = await self._summarize(
            self._review_payload(article, article_input), self.review_prompt_template, operation_name="review"
        )
        data = parse_json_object(raw, source_label="editorial review")
        issues = _string_list(data.get("issues"))
        if "passed" in data:
            passed = bool(data["passed"])
        elif issues:
            passed = False
        else:
            passed = True
        return ReviewResult(
            passed=passed,
            issues=issues,
            revision_instructions=str(data.get("revision_instructions") or "").strip(),
        )

    async def revise_article(self, article: str, article_input: str, review: ReviewResult) -> str:
        payload = self._revision_payload(article, article_input, review)
        return await self._summarize(payload, self.revision_prompt_template, operation_name="revise")

    def _fallback_clusters(self, briefs: List[ItemBrief]) -> List[StoryCluster]:
        included = [brief for brief in briefs if brief.include]
        if len(included) < self.min_final_items:
            included = sorted(briefs, key=lambda x: x.editorial_score, reverse=True)
        clusters = []
        for brief in included[: self.max_final_items]:
            clusters.append(
                StoryCluster(
                    title=brief.title,
                    primary_item_id=brief.item_id,
                    item_ids=[brief.item_id],
                    angle=brief.reason,
                    include=True,
                    reason=brief.reason,
                )
            )
        return clusters

    @staticmethod
    def _brief_payload(item: NewsItem) -> str:
        """Build the dynamic JSON payload for the brief prompt.

        The full content is sent so the LLM can independently decide which
        parts are most important to extract into ``content_snippet``.
        """
        content = item.content or ""
        top_comments = []
        comments_data = (item.original_data or {}).get("top_comments") or []
        for c in comments_data:
            if isinstance(c, dict):
                text = c.get("text", "")
            else:
                text = str(c)
            if text:
                top_comments.append(text[:500])
        payload = {
            "id": item.id,
            "title": item.title,
            "url": item.url,
            "source": item.source,
            "content": content,
            "top_comments": top_comments,
            "discussion_signal": item.discussion_signal,
            "discussion_tier": item.discussion_tier,
            "ranking_reason": item.ranking_reason,
            "original_data": item.original_data or {},
        }
        return json.dumps(payload, ensure_ascii=False)

    def _cluster_payload(self, briefs: List[ItemBrief]) -> str:
        """Build the dynamic JSON payload for the cluster prompt."""
        payload = {
            "target_range": f"{self.min_final_items}-{self.max_final_items}",
            "briefs": [brief.to_dict() for brief in briefs],
        }
        return json.dumps(payload, ensure_ascii=False)

    @staticmethod
    def _review_payload(article: str, article_input: str) -> str:
        """Build the dynamic JSON payload for the review prompt."""
        payload = {"article_input": article_input, "draft_article": article}
        return json.dumps(payload, ensure_ascii=False)

    @staticmethod
    def _revision_payload(article: str, article_input: str, review: ReviewResult) -> str:
        """Build the dynamic JSON payload for the revision prompt."""
        payload = {
            "article_input": article_input,
            "draft_article": article,
            "review": review.to_dict(),
        }
        return json.dumps(payload, ensure_ascii=False)

def _string_list(value: Any) -> List[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _float_in_range(value: Any, low: float, high: float) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return low
    return max(low, min(high, number))
