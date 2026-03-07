import json
import logging
import os
import re
from typing import Dict, List, Optional, Tuple

from insighthub.llm_providers.base import BaseLLMProvider
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
    DEFAULT_SCORING_PROMPT_PATH = os.path.join("prompts", "scoring", "comment_priority_reasoning_v1.md")

    def __init__(self, config: ScoringConfig, llm_provider: Optional[BaseLLMProvider] = None):
        self.config = config
        self.llm_provider = llm_provider
        scoring_prompt_name = getattr(config, "scoring_prompt_name", "comment_priority_reasoning_v1")
        prompt_path = os.path.join("prompts", "scoring", f"{scoring_prompt_name}.md")
        self.scoring_prompt_template = self._load_scoring_prompt_template(prompt_path)

    async def score_items(self, items: List[NewsItem]) -> List[NewsItem]:
        if not items:
            return items

        entries: List[Dict[str, object]] = []
        for index, item in enumerate(items):
            comment_count = self._comment_count(item)
            entries.append(
                {
                    "index": index,
                    "item": item,
                    "comment_count": comment_count,
                    "has_comments": comment_count > 0,
                }
            )

        llm_reasons: Dict[int, str] = {}
        if self.config.use_llm and self.llm_provider is not None:
            llm_reasons = await self._llm_reason_batch(entries)

        ranked_entries = sorted(
            entries,
            key=lambda x: (
                0 if bool(x["has_comments"]) else 1,
                -int(x["comment_count"]),
                int(x["index"]),
            ),
        )

        ranked_items: List[NewsItem] = []
        for entry in ranked_entries:
            index = int(entry["index"])
            item = entry["item"]
            comment_count = int(entry["comment_count"])
            base_reason = (
                "Ordered by comment count (higher first)."
                if comment_count > 0
                else "No comments; kept original source order."
            )
            llm_reason = llm_reasons.get(index)
            item.ai_score = float(comment_count)
            item.score_tier = tier_from_score(comment_count)
            item.score_breakdown = {"comment_count": float(comment_count)}
            item.score_reason = f"{base_reason} {llm_reason}".strip() if llm_reason else base_reason
            ranked_items.append(item)

        return ranked_items

    def select_items_for_summary(self, items: List[NewsItem]) -> List[NewsItem]:
        ranked = sorted(
            items,
            key=lambda x: (
                0 if self._comment_count(x) > 0 else 1,
                -self._comment_count(x),
            ),
        )
        return ranked

    async def _llm_reason_batch(self, entries: List[Dict[str, object]]) -> Dict[int, str]:
        payload: List[Dict[str, object]] = []
        for entry in entries:
            index = int(entry["index"])
            item = entry["item"]
            payload.append(
                {
                    "item_id": f"item_{index}",
                    "title": item.title,
                    "source": item.source,
                    "url": item.url,
                    "comment_count": int(entry["comment_count"]),
                    "content": (item.content or "")[:800],
                }
            )

        if not payload:
            return {}

        prompt = (
            f"{self.scoring_prompt_template}\n\n"
            "Generate short ranking reasons in JSON format: "
            "{'items':[{'item_id':'item_0','reason':'...'}]}\n"
            f"Input JSON:\n{json.dumps(payload, ensure_ascii=False)}"
        )
        try:
            raw = await self.llm_provider.summarize(prompt, "{content}")
            parsed_items = self._parse_llm_reason_json(raw)
            reason_map: Dict[int, str] = {}
            for one in parsed_items:
                item_id = str(one.get("item_id", "")).strip()
                reason = str(one.get("reason", "")).strip()
                if not item_id.startswith("item_") or not reason:
                    continue
                try:
                    idx = int(item_id.split("_", 1)[1])
                except ValueError:
                    continue
                reason_map[idx] = reason
            return reason_map
        except Exception as e:
            logger.warning(
                "LLM reason generation failed; keeping rule-only ordering.",
                extra={"event": "scoring.llm_reason.failed", "error": str(e)},
            )
            return {}

    @staticmethod
    def _parse_llm_reason_json(raw: str) -> List[Dict[str, object]]:
        text = raw.strip()
        fenced_match = re.search(r"```(?:json)?\s*(\{.*?\}|\[.*?\])\s*```", text, flags=re.S)
        if fenced_match:
            text = fenced_match.group(1).strip()

        if not text.startswith("[") and "{" in text and "}" in text:
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1 and end >= start:
                text = text[start : end + 1]

        data = json.loads(text)
        if isinstance(data, dict) and isinstance(data.get("items"), list):
            return [x for x in data["items"] if isinstance(x, dict)]
        if isinstance(data, list):
            return [x for x in data if isinstance(x, dict)]
        raise ValueError("Invalid LLM reason payload format")

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
            return "You rank news items for daily briefings. Keep reasons concise."

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
