import json
import logging
import os
import re
from typing import Dict, List, Optional, Tuple

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
    DEFAULT_SCORING_PROMPT_PATH = os.path.join("prompts", "scoring", "technical_content_scoring_v1.md")

    def __init__(self, config: ScoringConfig, llm_provider: Optional[BaseLLMProvider] = None):
        self.config = config
        self.llm_provider = llm_provider
        self.scoring_prompt_template = self._load_scoring_prompt_template()

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
    def _load_scoring_prompt_template(cls) -> str:
        try:
            with open(cls.DEFAULT_SCORING_PROMPT_PATH, "r", encoding="utf-8") as f:
                return f.read().strip()
        except Exception as e:
            logger.warning(
                "Failed to load scoring prompt template; using fallback.",
                extra={"event": "scoring.prompt.fallback", "path": cls.DEFAULT_SCORING_PROMPT_PATH, "error": str(e)},
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
