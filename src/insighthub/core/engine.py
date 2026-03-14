import asyncio
import json
import logging
import os
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from zoneinfo import ZoneInfo

from insighthub.core.retry import with_retry
from insighthub.errors import LLMProcessingError, PromptRenderingError, SinkDeliveryError, SourceFetchError
from insighthub.llm_providers.base import BaseLLMProvider
from insighthub.models import NewsItem
from insighthub.observability import get_run_id
from insighthub.prompting import PromptRenderer
from insighthub.publishing import TitlePolicy
from insighthub.scoring import ContentScorer
from insighthub.settings import RetryPolicyConfig, RuntimeDedupConfig, ScoringConfig
from insighthub.sinks.base import BaseSink
from insighthub.sources.base import BaseSource

logger = logging.getLogger(__name__)


class InsightEngine:
    """
    The core orchestrator of the InsightHub workflow.
    """

    def __init__(
        self,
        sources: List[BaseSource],
        llm_provider: BaseLLMProvider,
        sinks: List[BaseSink],
        prompts_dir: str = "prompts",
        history_file: str = "history.json",
        delivery_state_file: str = "delivery_state.json",
        prompt_structure: str = "structure_prompt_v1",
        prompt_style: str = "style_prompt_v1",
        prompt_variables: Optional[Dict[str, Any]] = None,
        max_history_records: int = 3000,
        max_delivery_item_records: int = 2000,
        max_delivery_runs: int = 100,
        scoring_config: Optional[ScoringConfig] = None,
        source_retry_policy: Optional[RetryPolicyConfig] = None,
        llm_retry_policy: Optional[RetryPolicyConfig] = None,
        sink_retry_policy: Optional[RetryPolicyConfig] = None,
        dedup_config: Optional[RuntimeDedupConfig] = None,
        timezone_name: str = "Asia/Shanghai",
        title_policy: Optional[TitlePolicy] = None,
        stage_runs_dir: str = "output/runs",
    ):
        self.sources = sources
        self.llm_provider = llm_provider
        self.sinks = sinks
        self.prompts_dir = prompts_dir
        self.history_file = history_file
        self.delivery_state_file = delivery_state_file
        self.max_history_records = max_history_records
        self.max_delivery_item_records = max_delivery_item_records
        self.max_delivery_runs = max_delivery_runs
        self.scoring_config = scoring_config or ScoringConfig()
        self.source_retry_policy = source_retry_policy or RetryPolicyConfig(max_attempts=3, base_delay_seconds=1.0)
        self.llm_retry_policy = llm_retry_policy or RetryPolicyConfig(max_attempts=3, base_delay_seconds=2.0)
        self.sink_retry_policy = sink_retry_policy or RetryPolicyConfig(max_attempts=2, base_delay_seconds=1.0)
        self.dedup_config = dedup_config or RuntimeDedupConfig()
        self.timezone_name = timezone_name
        self.stage_runs_dir = stage_runs_dir
        self.title_policy = title_policy
        self._strip_query_params = set(self.dedup_config.strip_query_params)
        self.scorer = ContentScorer(config=self.scoring_config)
        self.prompt_renderer = PromptRenderer(
            prompts_dir=prompts_dir,
            structure_name=prompt_structure,
            style_name=prompt_style,
            variables=prompt_variables or {},
        )
        self.summarize_prompt_template = self._load_summarize_prompt_template()

    def _load_history_entries(self) -> List[str]:
        if not os.path.exists(self.history_file):
            return []
        try:
            with open(self.history_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if not isinstance(data, list):
                    return []
                # Preserve order and remove duplicates.
                return list(dict.fromkeys(str(x) for x in data))
        except Exception as e:
            logger.warning("Failed to load history file.", extra={"event": "engine.history.load_failed", "error": str(e)})
            return []

    def _load_history(self) -> Set[str]:
        return set(self._load_history_entries())

    def _save_history_entries(self, entries: List[str]):
        pruned_entries = list(dict.fromkeys(entries))
        if len(pruned_entries) > self.max_history_records:
            pruned_entries = pruned_entries[-self.max_history_records :]
        try:
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(pruned_entries, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error("Failed to save history file.", extra={"event": "engine.history.save_failed", "error": str(e)})

    def _load_delivery_state(self) -> Dict[str, Any]:
        if not os.path.exists(self.delivery_state_file):
            return {"updated_at": None, "runs": [], "items": {}}
        try:
            with open(self.delivery_state_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    data.setdefault("updated_at", None)
                    data.setdefault("runs", [])
                    data.setdefault("items", {})
                    return data
        except Exception as e:
            logger.warning(
                "Failed to load delivery state file.",
                extra={"event": "engine.delivery_state.load_failed", "error": str(e)},
            )
        return {"updated_at": None, "runs": [], "items": {}}

    def _save_delivery_state(self, state: Dict[str, Any]) -> None:
        self._prune_delivery_state_items(state, max_item_records=self.max_delivery_item_records)
        if len(state.get("runs", [])) > self.max_delivery_runs:
            state["runs"] = state["runs"][-self.max_delivery_runs :]
        state["updated_at"] = self._utc_now_iso()
        try:
            with open(self.delivery_state_file, "w", encoding="utf-8") as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(
                "Failed to save delivery state file.",
                extra={"event": "engine.delivery_state.save_failed", "error": str(e)},
            )

    def _prune_delivery_state_items(self, state: Dict[str, Any], max_item_records: int) -> None:
        items = state.get("items")
        if not isinstance(items, dict):
            state["items"] = {}
            return
        if len(items) <= max_item_records:
            return

        def latest_updated_at(entry: Any) -> str:
            if not isinstance(entry, dict):
                return ""
            values = [v.get("updated_at", "") for v in entry.values() if isinstance(v, dict)]
            return max(values) if values else ""

        sorted_keys = sorted(items.keys(), key=lambda k: latest_updated_at(items[k]), reverse=True)
        keep = set(sorted_keys[:max_item_records])
        state["items"] = {k: v for k, v in items.items() if k in keep}

    @staticmethod
    def _utc_now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    async def run(self):
        run_id = self._resolve_run_id()
        new_items = await self.fetch()
        self._save_stage_items(run_id, "raw", new_items)
        if not new_items:
            logger.info("No new items to process.", extra={"event": "engine.run.no_new_items"})
            curated_markdown = self._build_no_update_markdown()
            self._save_stage_markdown(run_id, "summary", curated_markdown)
            self._save_run_meta(run_id, {"stages": {"raw": 0, "summary": 0}})
            await self.distribute(curated_markdown, [], update_history=False)
            return

        items_for_summary = new_items
        if self.scoring_config.enabled:
            items_for_summary = await self.score_items(new_items)
        self._save_stage_items(run_id, "scored", items_for_summary)

        curated_markdown = await self.summarize(items_for_summary)
        self._save_stage_markdown(run_id, "summary", curated_markdown)
        self._save_run_meta(
            run_id,
            {
                "stages": {
                    "raw": len(new_items),
                    "scored": len(items_for_summary) if self.scoring_config.enabled else None,
                    "summary": len(items_for_summary),
                }
            },
        )
        await self.distribute(curated_markdown, items_for_summary)

    async def _fetch_from_source(self, source: BaseSource) -> List[NewsItem]:
        source_name = getattr(source, "name", source.__class__.__name__)

        async def op() -> List[NewsItem]:
            try:
                return await source.fetch()
            except SourceFetchError:
                raise
            except Exception as e:
                raise SourceFetchError(f"Source '{source_name}' failed: {e}") from e

        return await with_retry(
            op,
            logger=logger,
            operation_name=f"source.fetch:{source_name}",
            max_attempts=self.source_retry_policy.max_attempts,
            base_delay_seconds=self.source_retry_policy.base_delay_seconds,
            backoff_multiplier=self.source_retry_policy.backoff_multiplier,
            max_delay_seconds=self.source_retry_policy.max_delay_seconds,
        )

    async def fetch(self, ignore_history: bool = False) -> List[NewsItem]:
        seen_ids = set() if ignore_history else self._load_history()
        if not ignore_history:
            logger.info(
                "Loaded history entries.",
                extra={"event": "engine.fetch.history_loaded", "seen_ids_count": len(seen_ids)},
            )

        fetch_tasks = [self._fetch_from_source(source) for source in self.sources]
        source_results = await asyncio.gather(*fetch_tasks, return_exceptions=True)

        all_items: List[NewsItem] = []
        for source, result in zip(self.sources, source_results):
            source_name = getattr(source, "name", source.__class__.__name__)
            if isinstance(result, Exception):
                logger.error(
                    "Source fetch failed.",
                    extra={"event": "engine.fetch.source_failed", "source": source_name, "error": str(result)},
                )
                continue
            logger.info(
                "Source fetch succeeded.",
                extra={"event": "engine.fetch.source_succeeded", "source": source_name, "items_count": len(result)},
            )
            all_items.extend(result)

        logger.info(
            "Fetched items from all sources.",
            extra={"event": "engine.fetch.completed", "items_total": len(all_items), "sources_total": len(self.sources)},
        )

        new_items: List[NewsItem] = []
        seen_in_batch: Set[str] = set()
        for item in all_items:
            primary_key = self._item_primary_key(item)
            if primary_key in seen_in_batch:
                continue
            seen_in_batch.add(primary_key)

            candidates = self._item_identity_candidates(item)
            if any(candidate in seen_ids for candidate in candidates):
                continue
            new_items.append(item)

        logger.info(
            "Deduplication completed.",
            extra={"event": "engine.fetch.deduplicated", "new_items_count": len(new_items)},
        )
        return new_items

    async def summarize(self, items: List[NewsItem]) -> str:
        if not items:
            return ""

        combined_input = self.build_summarize_input(items)

        logger.info(
            "Calling LLM summarization.",
            extra={"event": "engine.summarize.start", "items_count": len(items)},
        )

        async def op() -> str:
            try:
                return await self.llm_provider.summarize(combined_input, self.summarize_prompt_template)
            except LLMProcessingError:
                raise
            except Exception as e:
                raise LLMProcessingError(f"LLM summarization failed: {e}") from e

        try:
            curated_markdown = await with_retry(
                op,
                logger=logger,
                operation_name="llm.summarize",
                max_attempts=self.llm_retry_policy.max_attempts,
                base_delay_seconds=self.llm_retry_policy.base_delay_seconds,
                backoff_multiplier=self.llm_retry_policy.backoff_multiplier,
                max_delay_seconds=self.llm_retry_policy.max_delay_seconds,
            )
            logger.info("LLM summarization succeeded.", extra={"event": "engine.summarize.succeeded"})
            return curated_markdown
        except Exception as e:
            logger.error("LLM summarization failed; using fallback.", extra={"event": "engine.summarize.fallback", "error": str(e)})
            curated_markdown = "## 汇总内容 (AI 总结失败)\n"
            for item in items:
                curated_markdown += f"- [{item.title}]({item.url}): {self._fallback_summary(item.content or '')}\n"
            return curated_markdown

    async def score_items(self, items: List[NewsItem]) -> List[NewsItem]:
        if not items:
            return items
        logger.info("Starting content scoring.", extra={"event": "engine.score.start", "items_count": len(items)})
        scored_items = await self.scorer.score_items(items)
        selected = self.scorer.select_items_for_summary(scored_items)
        threshold = self.scoring_config.scoring_threshold
        filtered = selected
        if threshold is not None:
            filtered = [
                item
                for item in selected
                if item.discussion_signal is None or float(item.discussion_signal) >= threshold
            ]
            logger.info(
                "Applied scoring threshold.",
                extra={
                    "event": "engine.score.filtered",
                    "threshold": threshold,
                    "before_count": len(selected),
                    "after_count": len(filtered),
                },
            )
            if not filtered:
                logger.warning(
                    "All items filtered by score threshold.",
                    extra={"event": "engine.score.filtered_all", "threshold": threshold},
                )
        logger.info(
            "Content scoring completed.",
            extra={
                "event": "engine.score.completed",
                "items_count": len(scored_items),
                "selected_count": len(filtered),
            },
        )
        return filtered

    def build_summarize_input(self, items: List[NewsItem]) -> str:
        combined_input = ""
        for i, item in enumerate(items, start=1):
            combined_input += f"--- Item {i} ---\n"
            combined_input += f"Title: {item.title}\n"
            combined_input += f"URL: {item.url}\n"
            if item.discussion_signal is not None:
                combined_input += (
                    f"Discussion Signal: {item.discussion_signal} ({item.discussion_tier or 'Unrated'})\n"
                )
                if item.ranking_reason:
                    combined_input += f"Ranking Reason: {item.ranking_reason}\n"
            combined_input += f"Content: {item.content}\n\n"
        return combined_input

    async def _deliver_to_sink(self, sink: BaseSink, items: List[NewsItem], curated_content: str) -> Dict[str, Any]:
        sink_key = sink.sink_id()

        async def op() -> Dict[str, Any]:
            try:
                return await sink.render(items, curated_content=curated_content)
            except SinkDeliveryError:
                raise
            except Exception as e:
                raise SinkDeliveryError(f"Sink '{sink_key}' failed: {e}") from e

        result = await with_retry(
            op,
            logger=logger,
            operation_name=f"sink.render:{sink_key}",
            max_attempts=self.sink_retry_policy.max_attempts,
            base_delay_seconds=self.sink_retry_policy.base_delay_seconds,
            backoff_multiplier=self.sink_retry_policy.backoff_multiplier,
            max_delay_seconds=self.sink_retry_policy.max_delay_seconds,
        )
        return result or {"status": "success"}

    async def distribute(self, curated_content: str, items: List[NewsItem], update_history: bool = True):
        if not curated_content:
            logger.warning("No content to distribute.", extra={"event": "engine.distribute.empty_content"})
            return

        logger.info(
            "Sending curated content to sinks.",
            extra={"event": "engine.distribute.start", "sinks_count": len(self.sinks), "items_count": len(items)},
        )

        sink_tasks = [self._deliver_to_sink(sink, items, curated_content) for sink in self.sinks]
        results = await asyncio.gather(*sink_tasks, return_exceptions=True)

        state = self._load_delivery_state()
        run_record: Dict[str, Any] = {
            "timestamp": self._utc_now_iso(),
            "items_count": len(items),
            "sinks": {},
        }

        sink_successes = 0
        item_keys = [self._item_primary_key(item) for item in items]

        for sink, result in zip(self.sinks, results):
            sink_key = sink.sink_id()
            if isinstance(result, Exception):
                run_record["sinks"][sink_key] = {
                    "status": "failed",
                    "error": str(result),
                }
                logger.error(
                    "Sink delivery failed.",
                    extra={"event": "engine.distribute.sink_failed", "sink": sink_key, "error": str(result)},
                )
                status = "failed"
                error = str(result)
            else:
                run_record["sinks"][sink_key] = {
                    "status": "success",
                    "meta": result,
                }
                sink_successes += 1
                logger.info(
                    "Sink delivery succeeded.",
                    extra={"event": "engine.distribute.sink_succeeded", "sink": sink_key},
                )
                status = "success"
                error = None

            for key in item_keys:
                item_state = state["items"].setdefault(key, {})
                item_state[sink_key] = {
                    "status": status,
                    "updated_at": self._utc_now_iso(),
                    "error": error,
                }

        state["runs"].append(run_record)
        self._save_delivery_state(state)

        if update_history and items:
            if sink_successes == 0:
                logger.warning("No sinks succeeded; history not updated.", extra={"event": "engine.distribute.history_skipped"})
                return
            history_entries = self._load_history_entries()
            history_set = set(history_entries)
            new_entries = [key for key in item_keys if key not in history_set]
            history_entries.extend(new_entries)
            self._save_history_entries(history_entries)
            logger.info(
                "History updated after distribution.",
                extra={"event": "engine.distribute.history_updated", "updated_items_count": len(new_entries)},
            )

    def save_items(self, items: List[NewsItem], file_path: str):
        data = [item.model_dump() for item in items]
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load_items(self, file_path: str) -> List[NewsItem]:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return [NewsItem(**item) for item in data]

    def save_content(self, content: str, file_path: str):
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

    def load_content(self, file_path: str) -> str:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    def _fallback_summary(self, text: str) -> str:
        if not text:
            return "(No content to summarize)"
        import re

        s = text.strip()
        parts = re.split(r"(?<=[.!?])\s+", s)
        if parts and len(parts[0]) > 20:
            return parts[0][:360]
        return (s[:360] + "...") if len(s) > 360 else s

    def _load_prompt(self, filename: str) -> str:
        path = os.path.join(self.prompts_dir, filename)
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            logger.error("Prompt template not found.", extra={"event": "engine.prompt.not_found", "path": path})
            return "Summarize these items into a report:\n{content}"

    def _load_summarize_prompt_template(self) -> str:
        try:
            template = self.prompt_renderer.render_summarize_template()
            logger.info(
                "Loaded composed summarize prompt.",
                extra={
                    "event": "engine.prompt.loaded_composed",
                    "prompt_structure": self.prompt_renderer.structure_name,
                    "prompt_style": self.prompt_renderer.style_name,
                },
            )
            return template
        except PromptRenderingError as e:
            logger.warning(
                "Failed to load composed summarize prompt.",
                extra={"error": str(e)},
            )
            return None

    def _item_primary_key(self, item: NewsItem) -> str:
        normalized_id = self._normalize_possible_url(item.id)
        if normalized_id:
            return normalized_id
        normalized_url = self._normalize_possible_url(item.url)
        return normalized_url or item.id

    def _item_identity_candidates(self, item: NewsItem) -> Set[str]:
        candidates: Set[str] = {item.id}
        normalized_id = self._normalize_possible_url(item.id)
        if normalized_id:
            candidates.add(normalized_id)
        normalized_url = self._normalize_possible_url(item.url)
        if normalized_url:
            candidates.add(normalized_url)
        return candidates

    def _normalize_possible_url(self, value: Optional[str]) -> Optional[str]:
        if not self.dedup_config.normalize_url:
            return None
        if not value or not isinstance(value, str):
            return None
        if not (value.startswith("http://") or value.startswith("https://")):
            return None
        return self._normalize_url(value)

    def _normalize_url(self, url: str) -> str:
        parts = urlsplit(url)
        cleaned_query = urlencode(
            [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True) if k not in self._strip_query_params],
            doseq=True,
        )
        cleaned_path = parts.path.rstrip("/") if parts.path != "/" else parts.path
        return urlunsplit((
            parts.scheme.lower(),
            parts.netloc.lower(),
            cleaned_path,
            cleaned_query,
            "",
        ))

    def _resolve_run_id(self) -> str:
        run_id = (get_run_id() or "").strip()
        if run_id and run_id != "-":
            return run_id
        return datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")

    def _run_dir(self, run_id: str) -> Path:
        return Path(self.stage_runs_dir) / run_id

    def _save_stage_items(self, run_id: str, stage: str, items: List[NewsItem]) -> None:
        path = self._run_dir(run_id) / f"{stage}_items.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        data = [item.model_dump() for item in items]
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _save_stage_markdown(self, run_id: str, stage: str, content: str) -> None:
        path = self._run_dir(run_id) / f"{stage}.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

    def _save_run_meta(self, run_id: str, payload: Dict[str, Any]) -> None:
        path = self._run_dir(run_id) / "meta.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        existing: Dict[str, Any] = {}
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                if isinstance(loaded, dict):
                    existing = loaded
            except Exception:
                existing = {}
        existing.update(payload)
        existing["run_id"] = run_id
        existing["updated_at"] = self._utc_now_iso()
        with open(path, "w", encoding="utf-8") as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)

    def _build_no_update_markdown(self) -> str:
        now = datetime.now(ZoneInfo(self.timezone_name))
        title = self.title_policy.render(now)
        return (
            f"# {title}\n\n"
            "> 今日无更新。\n\n"
            "今天没有发现通过筛选的新内容，明日再见。"
        )
