import json
import logging
import os
import re
from typing import Dict, List, Optional, Set, Tuple
from collections import defaultdict

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


def tier_from_score(score: float) -> str:
    for threshold, label in SCORE_TIERS:
        if score >= threshold:
            return label
    return "Noise"


class ContentScorer:
    DEFAULT_SCORING_PROMPT_PATH = os.path.join("prompts", "scoring", "technical_content_scoring_v2_clustering.md")

    def __init__(self, config: ScoringConfig, llm_provider: Optional[BaseLLMProvider] = None):
        self.config = config
        self.llm_provider = llm_provider
        # 从 config 读取评分提示词名称，或使用默认值
        scoring_prompt_name = getattr(config, 'scoring_prompt_name', 'technical_content_scoring_v2_clustering')
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
        # Step 1: Score items using standard scoring
        scored_items = await self.score_items(items)
        
        # Step 2: Extract topics and analyze relationships
        topic_keywords = self._extract_topic_keywords(scored_items)
        
        # Step 3: Calculate topical relevance for each item
        for idx, item in enumerate(scored_items):
            related_ids = self._find_related_items(item, scored_items, topic_keywords)
            topical_relevance = self._calculate_topical_relevance(item, related_ids, len(scored_items))
            cross_domain_potential = self._calculate_cross_domain_potential(item, topic_keywords)
            narrative_conn = self._calculate_narrative_connectivity(item, scored_items, topic_keywords)
            is_hub = topical_relevance >= 8.0 and len(related_ids) >= 2
            
            item.topical_relevance_to_batch = round(topical_relevance, 2)
            item.cross_domain_insight_potential = round(cross_domain_potential, 2)
            item.narrative_connectivity = round(narrative_conn, 2)
            item.is_cluster_hub = is_hub
            item.related_item_ids = related_ids
        
        # Step 4: Identify topic clusters
        clusters = self._identify_topic_clusters(scored_items, topic_keywords)
        
        # Step 5: Assign suggested_topic_cluster for each item
        item_to_cluster = {}
        for cluster_name, cluster_items in clusters.items():
            for item_id in cluster_items:
                item_to_cluster[item_id] = cluster_name
        
        for item in scored_items:
            item.suggested_topic_cluster = item_to_cluster.get(item.id, "未分类")
        
        clustering_metadata = {
            "total_items": len(scored_items),
            "identified_topic_keywords": topic_keywords,
            "clusters": clusters,
            "cluster_hubs": [item.id for item in scored_items if item.is_cluster_hub],
        }
        
        return scored_items, clustering_metadata

    def _extract_topic_keywords(self, items: List[NewsItem]) -> Dict[str, int]:
        """
        Extract key topic indicators from all items.
        Returns a dict of keyword -> frequency map.
        """
        keywords: Dict[str, int] = defaultdict()
        
        common_keywords = {
            # Hardware/Architecture
            "arm": "hardware", "x86": "hardware", "cpu": "hardware", "gpu": "hardware", 
            "芯片": "hardware", "处理器": "hardware", "架构": "hardware",
            # AI/ML
            "ai": "ai_ml", "llm": "ai_ml", "ml": "ai_ml", "neural": "ai_ml",
            "model": "ai_ml", "inference": "ai_ml", "agent": "ai_ml",
            "大模型": "ai_ml", "推理": "ai_ml", "训练": "ai_ml",
            # Security/Privacy
            "security": "security", "privacy": "security", "encryption": "security",
            "安全": "security", "隐私": "security", "加密": "security",
            # Performance/Optimization
            "performance": "performance", "latency": "performance", "optimization": "performance",
            "性能": "performance", "延迟": "performance", "优化": "performance",
            # Data/Systems
            "database": "systems", "distributed": "systems", "system": "systems",
            "数据库": "systems", "分布式": "systems", "系统": "systems",
            # Edge/Mobile
            "edge": "edge_mobile", "mobile": "edge_mobile", "device": "edge_mobile",
            "边缘": "edge_mobile", "移动": "edge_mobile", "设备": "edge_mobile",
        }
        
        topic_groups: Dict[str, Set[str]] = defaultdict(set)
        
        for item in items:
            text = f"{item.title or ''} {item.content or ''}".lower()
            for keyword, group in common_keywords.items():
                if keyword in text:
                    topic_groups[group].add(item.id)
        
        return topic_groups

    def _find_related_items(self, item: NewsItem, all_items: List[NewsItem], 
                           topic_keywords: Dict[str, Set[str]]) -> List[str]:
        """
        Find IDs of items related to the given item.
        """
        related = []
        item_text = f"{item.title or ''} {item.content or ''}".lower()
        
        # Keyword-based relevance
        for other in all_items:
            if other.id == item.id:
                continue
            other_text = f"{other.title or ''} {other.content or ''}".lower()
            
            # Simple shared keyword detection
            shared_keywords = 0
            for group, item_ids in topic_keywords.items():
                if item.id in item_ids and other.id in item_ids:
                    shared_keywords += 1
            
            if shared_keywords >= 1:
                related.append(other.id)
        
        return related[:5]  # Limit to 5 most related items

    @staticmethod
    def _calculate_topical_relevance(item: NewsItem, related_ids: List[str], total_items: int) -> float:
        """
        Calculate topical relevance score based on how many related items exist.
        """
        if total_items <= 1:
            return 5.0
        
        relation_ratio = len(related_ids) / (total_items - 1)
        
        if len(related_ids) >= 3:
            score = 8.0 + relation_ratio * 2.0
        elif len(related_ids) == 2:
            score = 6.5 + relation_ratio * 1.5
        elif len(related_ids) == 1:
            score = 4.0 + relation_ratio * 1.0
        else:
            score = 2.0
        
        return min(10.0, score)

    @staticmethod
    def _calculate_cross_domain_potential(item: NewsItem, topic_keywords: Dict[str, Set[str]]) -> float:
        """
        Estimate cross-domain insight potential based on topic diversity coverage.
        """
        item_groups = []
        for group, item_ids in topic_keywords.items():
            if item.id in item_ids:
                item_groups.append(group)
        
        # More diverse topics = higher cross-domain potential
        diversity_score = min(10.0, 2.0 + len(item_groups) * 2.5)
        return diversity_score

    @staticmethod
    def _calculate_narrative_connectivity(item: NewsItem, all_items: List[NewsItem],
                                        topic_keywords: Dict[str, Set[str]]) -> float:
        """
        Estimate how easily this item can be integrated into a narrative.
        """
        # Items with good evidence quality and clarity are more narrative-friendly
        base_score = 5.0
        
        if item.content and len(item.content) > 300:
            base_score += 2.0
        
        if item.score_breakdown.get("writing_quality", 0) >= 6.0:
            base_score += 2.0
        
        return min(10.0, base_score)

    def _identify_topic_clusters(self, items: List[NewsItem], 
                                topic_keywords: Dict[str, Set[str]]) -> Dict[str, List[str]]:
        """
        Identify main topic clusters from items.
        """
        clusters = {}
        
        for group_name, item_ids in topic_keywords.items():
            if len(item_ids) >= 2:  # Only clusters with 2+ items
                sorted_by_score = sorted(
                    [i for i in items if i.id in item_ids],
                    key=lambda x: x.ai_score or 0.0,
                    reverse=True
                )
                cluster_name = self._generate_cluster_name(group_name, list(item_ids))
                clusters[cluster_name] = list(item_ids)
        
        return clusters

    @staticmethod
    def _generate_cluster_name(group: str, item_ids: List[str]) -> str:
        """
        Generate a human-readable cluster name from the group identifier.
        """
        group_names = {
            "hardware": "硬件架构演进",
            "ai_ml": "AI/ML 技术进展",
            "security": "安全与隐私",
            "performance": "性能优化",
            "systems": "系统与基础设施",
            "edge_mobile": "边缘与移动计算",
        }
        return group_names.get(group, f"主题-{group}")

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

        technical_depth = min(10.0, 3.0 + keyword_hits * 0.7 + min(content_len / 1200.0, 2.5))
        potential_impact = min(10.0, 2.5 + keyword_hits * 0.5 + engagement * 0.4)
        writing_quality = min(10.0, 2.0 + min(content_len / 700.0, 4.0))
        community_discussion = discussion
        engagement_signals = engagement

        breakdown = {
            "technical_depth_and_novelty": round(technical_depth, 2),
            "potential_impact": round(potential_impact, 2),
            "writing_quality": round(writing_quality, 2),
            "community_discussion": round(community_discussion, 2),
            "engagement_signals": round(engagement_signals, 2),
        }
        score = self._weighted_score(breakdown)
        return breakdown, score

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
                    "potential_impact": self._clamp_score(one.get("potential_impact", 0)),
                    "writing_quality": self._clamp_score(one.get("writing_quality", 0)),
                    "community_discussion": self._clamp_score(one.get("community_discussion", 0)),
                    "engagement_signals": self._clamp_score(one.get("engagement_signals", 0)),
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
                "你是技术内容评分器。请按五个维度给每个条目打分，并只输出 JSON："
                "technical_depth_and_novelty, potential_impact, writing_quality, community_discussion, "
                "engagement_signals, score, tier, reason, confidence。"
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
