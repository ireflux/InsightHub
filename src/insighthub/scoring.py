import json
import logging
import os
import re
from collections import defaultdict
from typing import Dict, List, Optional, Set, Tuple

from insighthub.llm_providers.base import BaseLLMProvider
from insighthub.models import NewsItem
from insighthub.settings import ScoringConfig

logger = logging.getLogger(__name__)

SCORE_TIERS: List[Tuple[float, str]] = [
    (9.0, "Groundbreaking"),
    (7.0, "High Value"),
    (5.0, "Interesting"),
    (3.0, "Low Priority"),
    (0.0, "Noise"),
]

TOPIC_LEXICON: Dict[str, Set[str]] = {
    "hardware": {"arm", "x86", "cpu", "gpu", "芯片", "处理器", "架构"},
    "ai_ml": {"ai", "llm", "ml", "neural", "model", "inference", "agent", "大模型", "推理", "训练"},
    "security": {"security", "privacy", "encryption", "安全", "隐私", "加密"},
    "performance": {"performance", "latency", "optimization", "性能", "延迟", "优化"},
    "systems": {"database", "distributed", "system", "数据库", "分布式", "系统"},
    "edge_mobile": {"edge", "mobile", "device", "边缘", "移动", "设备"},
}


def tier_from_score(score: float) -> str:
    for threshold, label in SCORE_TIERS:
        if score >= threshold:
            return label
    return "Noise"


class ContentScorer:
    DEFAULT_SCORING_PROMPT_PATH = os.path.join("prompts", "scoring", "technical_content_scoring_v2.md")

    def __init__(self, config: ScoringConfig, llm_provider: Optional[BaseLLMProvider] = None):
        self.config = config
        self.llm_provider = llm_provider
        # 从 config 读取评分提示词名称，或使用默认值
        scoring_prompt_name = getattr(config, "scoring_prompt_name", "technical_content_scoring_v2")
        prompt_path = os.path.join("prompts", "scoring", f"{scoring_prompt_name}.md")
        self.scoring_prompt_template = self._load_scoring_prompt_template(prompt_path)

    async def score_items(self, items: List[NewsItem]) -> List[NewsItem]:
        if not items:
            return items

        rule_data: List[Dict[str, object]] = []
        for index, item in enumerate(items):
            rule_breakdown, rule_score = self._rule_score(item)
            rule_data.append(
                {
                    "index": index,
                    "item": item,
                    "rule_breakdown": rule_breakdown,
                    "rule_score": rule_score,
                }
            )

        llm_results: Dict[int, Dict[str, object]] = {}
        if self.config.use_llm and self.llm_provider is not None:
            llm_results = await self._llm_score_batch(rule_data)

        for entry in rule_data:
            index = int(entry["index"])
            item = entry["item"]
            rule_breakdown = entry["rule_breakdown"]
            rule_score = float(entry["rule_score"])

            final_score = rule_score
            final_breakdown = rule_breakdown
            reason = "规则评分。"

            llm_data = llm_results.get(index)
            if llm_data:
                llm_breakdown = llm_data.get("breakdown", {})
                llm_score = float(llm_data.get("score", rule_score))
                alpha = self.config.llm_blend_alpha
                final_breakdown = {
                    k: round(alpha * rule_breakdown.get(k, 0.0) + (1 - alpha) * llm_breakdown.get(k, 0.0), 2)
                    for k in rule_breakdown.keys()
                }
                final_score = round(alpha * rule_score + (1 - alpha) * llm_score, 2)
                reason = str(llm_data.get("reason", "")).strip() or reason

            item.ai_score = self._clamp_score(final_score)
            item.score_tier = tier_from_score(item.ai_score)
            item.score_breakdown = final_breakdown
            item.score_reason = reason
        return items

    def select_items_for_summary(self, items: List[NewsItem]) -> List[NewsItem]:
        ranked = sorted(items, key=lambda x: (x.ai_score or 0.0), reverse=True)
        filtered = [item for item in ranked if (item.ai_score or 0.0) >= self.config.min_score_for_summary]
        if self.config.keep_top_n is not None:
            filtered = filtered[: self.config.keep_top_n]
        return filtered

    async def score_items_with_clustering(self, items: List[NewsItem]) -> Tuple[List[NewsItem], Dict[str, object]]:
        """
        Enhanced scoring with topic clustering analysis for v4 briefing.
        Returns both scored items and clustering metadata.
        """
        scored_items = await self.score_items(items)

        topic_groups = self._extract_topic_keywords(scored_items)
        total_items = len(scored_items)
        small_batch_mode = total_items <= 3

        for item in scored_items:
            related_ids = self._find_related_items(item, scored_items, topic_groups)
            topical_relevance = self._calculate_topical_relevance(related_ids, total_items, small_batch_mode)
            cross_domain_potential = self._calculate_cross_domain_potential(item, topic_groups)
            narrative_conn = self._calculate_narrative_connectivity(item, topic_groups, small_batch_mode)

            hub_threshold = 2 if small_batch_mode else 3
            is_hub = topical_relevance >= 8.0 and len(related_ids) >= hub_threshold

            item.topical_relevance_to_batch = round(topical_relevance, 2)
            item.cross_domain_insight_potential = round(cross_domain_potential, 2)
            item.narrative_connectivity = round(narrative_conn, 2)
            item.is_cluster_hub = is_hub
            item.related_item_ids = related_ids
            # Rebuild six-dimension breakdown to keep one scoring schema end-to-end.
            item.score_breakdown = {
                **(item.score_breakdown or {}),
                "topical_relevance_to_batch": item.topical_relevance_to_batch,
                "cross_domain_insight_potential": item.cross_domain_insight_potential,
                "narrative_connectivity": item.narrative_connectivity,
            }
            item.ai_score = self._weighted_score(item.score_breakdown)
            item.score_tier = tier_from_score(item.ai_score)

        clusters = self._identify_topic_clusters(scored_items, topic_groups)
        item_to_cluster: Dict[str, str] = {}
        for cluster_name, cluster_items in clusters.items():
            for item_id in cluster_items:
                item_to_cluster[item_id] = cluster_name

        for item in scored_items:
            item.suggested_topic_cluster = item_to_cluster.get(item.id, "未分类")

        clustering_metadata = {
            "total_items": total_items,
            "small_batch_mode": small_batch_mode,
            "identified_topics": sorted(topic_groups.keys()),
            "clusters": clusters,
            "cluster_hubs": [item.id for item in scored_items if item.is_cluster_hub],
        }

        return scored_items, clustering_metadata

    def _extract_topic_keywords(self, items: List[NewsItem]) -> Dict[str, Set[str]]:
        """
        Return topic -> set(item_id) map using a lightweight lexicon.
        """
        topic_groups: Dict[str, Set[str]] = defaultdict(set)
        for item in items:
            text = f"{item.title or ''} {item.content or ''}".lower()
            for topic, keywords in TOPIC_LEXICON.items():
                if any(kw in text for kw in keywords):
                    topic_groups[topic].add(item.id)

        return topic_groups

    def _find_related_items(
        self, item: NewsItem, all_items: List[NewsItem], topic_groups: Dict[str, Set[str]]
    ) -> List[str]:
        """
        Find related item IDs based on shared topic groups and rank by overlap.
        """
        item_topics = {topic for topic, item_ids in topic_groups.items() if item.id in item_ids}
        scored_related: List[Tuple[str, int, float]] = []

        for other in all_items:
            if other.id == item.id or not other.id:
                continue
            other_topics = {topic for topic, item_ids in topic_groups.items() if other.id in item_ids}
            overlap = len(item_topics & other_topics)
            if overlap > 0:
                scored_related.append((other.id, overlap, other.ai_score or 0.0))

        scored_related.sort(key=lambda x: (x[1], x[2]), reverse=True)
        return [item_id for item_id, _, _ in scored_related[:5]]

    @staticmethod
    def _calculate_topical_relevance(related_ids: List[str], total_items: int, small_batch_mode: bool) -> float:
        """
        Convert related-item count to 0-10 score aligned with v4.2 bands.
        """
        if total_items <= 1:
            return 3.0

        related_count = len(related_ids)
        relation_ratio = related_count / max(1, total_items - 1)

        if related_count >= 3:
            score = 8.0 + relation_ratio * 2.0
        elif related_count == 2:
            score = 6.0 + relation_ratio * 1.5
        elif related_count == 1:
            score = 4.0 + relation_ratio
        else:
            score = 2.0

        if small_batch_mode:
            score = score * 0.9
        return min(10.0, score)

    @staticmethod
    def _calculate_cross_domain_potential(item: NewsItem, topic_groups: Dict[str, Set[str]]) -> float:
        """
        More topic coverage implies higher cross-domain insight potential.
        """
        topic_count = sum(1 for _, item_ids in topic_groups.items() if item.id in item_ids)
        if topic_count >= 4:
            return 9.0
        if topic_count == 3:
            return 7.5
        if topic_count == 2:
            return 6.0
        if topic_count == 1:
            return 4.5
        return 3.0

    @staticmethod
    def _calculate_narrative_connectivity(
        item: NewsItem, topic_groups: Dict[str, Set[str]], small_batch_mode: bool
    ) -> float:
        """
        Estimate narrative fitness using content richness + topic overlap.
        """
        base_score = 4.5
        topic_count = sum(1 for _, item_ids in topic_groups.items() if item.id in item_ids)
        base_score += min(2.0, topic_count * 0.7)

        if item.content and len(item.content) > 300:
            base_score += 1.2
        if item.content and len(item.content) > 900:
            base_score += 0.8

        if item.score_breakdown.get("technical_depth_and_novelty", 0.0) >= 6.0:
            base_score += 1.0

        if small_batch_mode:
            base_score -= 0.6
        return min(10.0, base_score)

    def _identify_topic_clusters(
        self, items: List[NewsItem], topic_groups: Dict[str, Set[str]]
    ) -> Dict[str, List[str]]:
        """
        Build topic clusters with at least two items.
        """
        by_id = {item.id: item for item in items}
        clusters: Dict[str, List[str]] = {}

        for topic, item_ids in topic_groups.items():
            if len(item_ids) < 2:
                continue
            sorted_ids = sorted(item_ids, key=lambda item_id: by_id[item_id].ai_score or 0.0, reverse=True)
            cluster_name = self._generate_cluster_name(topic)
            clusters[cluster_name] = sorted_ids

        return clusters

    @staticmethod
    def _generate_cluster_name(topic: str) -> str:
        """
        Generate a stable display name for topic cluster.
        """
        topic_names = {
            "hardware": "硬件架构演进",
            "ai_ml": "AI/ML 技术进展",
            "security": "安全与隐私",
            "performance": "性能优化",
            "systems": "系统与基础设施",
            "edge_mobile": "边缘与移动计算",
        }
        return topic_names.get(topic, f"主题-{topic}")

    def _rule_score(self, item: NewsItem) -> Tuple[Dict[str, float], float]:
        text = f"{item.title or ''}\n{item.content or ''}".lower()
        engagement = self._engagement_score(item)
        discussion = self._discussion_score(item)

        novelty_keywords = (
            "research",
            "paper",
            "release",
            "benchmark",
            "architecture",
            "distributed",
            "compiler",
            "security",
            "database",
            "kernel",
            "llm",
            "agent",
            "inference",
            "rust",
            "go",
            "python",
        )
        keyword_hits = sum(1 for kw in novelty_keywords if kw in text)
        content_len = len(item.content or "")
        matched_topics = self._topic_count_for_text(text)
        digit_hits = len(re.findall(r"\d+(\.\d+)?", item.content or ""))
        link_hits = len(re.findall(r"https?://", item.content or ""))

        technical_depth = min(10.0, 3.0 + keyword_hits * 0.7 + min(content_len / 1200.0, 2.5))
        practical_impact = min(10.0, 2.4 + keyword_hits * 0.45 + engagement * 0.35 + discussion * 0.15)
        evidence_quality = min(10.0, 2.0 + min(content_len / 900.0, 3.0) + min(digit_hits * 0.35 + link_hits * 0.8, 5.0))
        # Batch-level topical relevance is re-estimated in score_items_with_clustering.
        topical_relevance = min(10.0, 3.0 + matched_topics * 1.0)
        cross_domain = min(10.0, 2.5 + matched_topics * 1.8)
        narrative_connectivity = min(10.0, 3.0 + min(content_len / 700.0, 3.5) + min(matched_topics * 0.8, 2.5))

        breakdown = {
            "technical_depth_and_novelty": round(technical_depth, 2),
            "practical_impact": round(practical_impact, 2),
            "evidence_quality": round(evidence_quality, 2),
            "topical_relevance_to_batch": round(topical_relevance, 2),
            "cross_domain_insight_potential": round(cross_domain, 2),
            "narrative_connectivity": round(narrative_connectivity, 2),
        }
        score = self._weighted_score(breakdown)
        return breakdown, score

    @staticmethod
    def _topic_count_for_text(text: str) -> int:
        return sum(1 for _, keywords in TOPIC_LEXICON.items() if any(kw in text for kw in keywords))

    def _weighted_score(self, breakdown: Dict[str, float]) -> float:
        weights = self.config.weights.model_dump()
        total_weight = sum(weights.values()) or 1.0
        score = sum(breakdown.get(k, 0.0) * weights.get(k, 0.0) for k in breakdown.keys()) / total_weight
        return self._clamp_score(score)

    @staticmethod
    def _clamp_score(value: float) -> float:
        return round(max(0.0, min(10.0, float(value))), 2)

    def _discussion_score(self, item: NewsItem) -> float:
        data = item.original_data or {}
        comments = self._extract_number(data, "hn_comments", "comments", "comments_count", "replies", "reply_count")
        if comments <= 0:
            return 1.5
        # Saturating curve for stability across sources.
        return self._clamp_score(1.5 + min(8.5, (comments ** 0.5) * 0.9))

    def _engagement_score(self, item: NewsItem) -> float:
        data = item.original_data or {}
        source = (item.source or "").lower()

        if "hacker news" in source:
            score = self._extract_number(data, "hn_score", "score")
            return self._clamp_score(min(10.0, 2.0 + (score ** 0.5) * 0.45))

        if "reddit" in source:
            ratio = self._extract_number(data, "upvote_ratio")
            comments = self._extract_number(data, "comments", "comments_count")
            ratio_score = max(0.0, min(1.0, ratio)) * 6.0
            comment_score = min(4.0, (comments ** 0.5) * 0.35)
            return self._clamp_score(ratio_score + comment_score)

        generic = self._extract_number(data, "score", "likes", "votes", "hot")
        if generic <= 0:
            return 2.0
        return self._clamp_score(2.0 + min(8.0, (generic ** 0.5) * 0.4))

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

    async def _llm_score_batch(self, rule_data: List[Dict[str, object]]) -> Dict[int, Dict[str, object]]:
        # Prioritize high rule-score items for LLM scoring budget.
        top_entries = sorted(rule_data, key=lambda x: float(x["rule_score"]), reverse=True)[: self.config.max_items_for_llm_scoring]
        if not top_entries:
            return {}

        items_json = self._build_batch_llm_prompt(top_entries)
        prompt = f"{self.scoring_prompt_template}\n\n输入条目JSON：\n{items_json}"
        try:
            raw = await self.llm_provider.summarize(prompt, "{content}")
            parsed_items = self._parse_llm_batch_json(raw)

            parsed_map: Dict[str, Dict[str, object]] = {}
            for one in parsed_items:
                item_id = str(one.get("item_id", "")).strip()
                if item_id:
                    parsed_map[item_id] = one

            results: Dict[int, Dict[str, object]] = {}
            for entry in top_entries:
                entry_id = f"item_{entry['index']}"
                one = parsed_map.get(entry_id)
                if not one:
                    continue

                breakdown = {
                    "technical_depth_and_novelty": self._clamp_score(one.get("technical_depth_and_novelty", 0)),
                    "practical_impact": self._clamp_score(one.get("practical_impact", 0)),
                    "evidence_quality": self._clamp_score(one.get("evidence_quality", 0)),
                    "topical_relevance_to_batch": self._clamp_score(one.get("topical_relevance_to_batch", 0)),
                    "cross_domain_insight_potential": self._clamp_score(one.get("cross_domain_insight_potential", 0)),
                    "narrative_connectivity": self._clamp_score(one.get("narrative_connectivity", 0)),
                }
                score = self._clamp_score(one.get("score", self._weighted_score(breakdown)))
                reason = str(one.get("reason", "")).strip() or "LLM批量评分。"
                results[int(entry["index"])] = {"breakdown": breakdown, "score": score, "reason": reason}
            return results
        except Exception as e:
            logger.warning("LLM batch scoring failed; fallback to rule score.", extra={"event": "scoring.llm_batch.failed", "error": str(e)})
            return {}

    @staticmethod
    def _build_batch_llm_prompt(entries: List[Dict[str, object]]) -> str:
        payload: List[Dict[str, object]] = []
        for entry in entries:
            index = entry["index"]
            item = entry["item"]
            compact_content = (item.content or "")[:1400]
            payload.append(
                {
                    "item_id": f"item_{index}",
                    "title": item.title,
                    "source": item.source,
                    "url": item.url,
                    "content": compact_content,
                    "engagement_metadata": item.original_data or {},
                    "rule_score_reference": {
                        "breakdown": entry["rule_breakdown"],
                        "score": entry["rule_score"],
                    },
                }
            )

        return json.dumps(payload, ensure_ascii=False)

    @classmethod
    def _load_scoring_prompt_template(cls, path: Optional[str] = None) -> str:
        if path is None:
            path = cls.DEFAULT_SCORING_PROMPT_PATH
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read().strip()
        except Exception as e:
            logger.warning(
                "Failed to load scoring prompt template; using fallback.",
                extra={"event": "scoring.prompt.fallback", "path": path, "error": str(e)},
            )
            return (
                "你是技术内容评分器。请只输出 JSON，字段包括："
                "technical_depth_and_novelty, practical_impact, evidence_quality, "
                "topical_relevance_to_batch, cross_domain_insight_potential, narrative_connectivity, "
                "score, tier, reason, confidence。"
            )

    @staticmethod
    def _parse_llm_batch_json(raw: str) -> List[Dict[str, object]]:
        text = raw.strip()
        fenced_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, flags=re.S)
        if fenced_match:
            text = fenced_match.group(1).strip()
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end >= start:
            text = text[start : end + 1]
        data = json.loads(text)

        if isinstance(data, dict) and isinstance(data.get("items"), list):
            return [x for x in data["items"] if isinstance(x, dict)]
        if isinstance(data, list):
            return [x for x in data if isinstance(x, dict)]
        raise ValueError("Invalid LLM batch scoring payload format")
