import asyncio
import os
import json
import logging
from typing import List, Set, Optional
from insighthub.sources.base import BaseSource
from insighthub.llm_providers.base import BaseLLMProvider
from insighthub.sinks.base import BaseSink
from insighthub.models import NewsItem

logger = logging.getLogger(__name__)

class InsightEngine:
    """
    The core orchestrator of the InsightHub workflow.
    Refactored for batch processing: collects all items and calls AI once.
    """
    
    def __init__(
        self,
        sources: List[BaseSource],
        llm_provider: BaseLLMProvider,
        sinks: List[BaseSink],
        prompts_dir: str = "prompts",
        history_file: str = "history.json",
    ):
        self.sources = sources
        self.llm_provider = llm_provider
        self.sinks = sinks
        self.prompts_dir = prompts_dir
        self.history_file = history_file
        # Updated to use .md template
        self.summarize_prompt_template = self._load_prompt("summarize_template.md")

    def _load_history(self) -> Set[str]:
        """Loads processed item IDs from the history file."""
        if not os.path.exists(self.history_file):
            return set()
        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return set(data) if isinstance(data, list) else set()
        except Exception as e:
            logger.warning(f"Failed to load history from {self.history_file}: {e}")
            return set()

    def _save_history(self, seen_ids: Set[str]):
        """Saves processed item IDs to the history file."""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(list(seen_ids), f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save history to {self.history_file}: {e}")

    async def run(self):
        """
        Runs the full workflow:
        1. Loads processed history.
        2. Fetches data from all sources.
        3. Deduplicates.
        4. Batch summarizes ALL new items in one AI call.
        5. Sends the curated content to all sinks.
        6. Updates history.
        """
        # 1. Load History
        seen_ids = self._load_history()
        logger.info(f"Loaded {len(seen_ids)} seen items from history.")

        # 2. Fetch from all sources
        fetch_tasks = [source.fetch() for source in self.sources]
        all_items_nested = await asyncio.gather(*fetch_tasks)
        all_items: List[NewsItem] = [item for sublist in all_items_nested for item in sublist]
        logger.info(f"Fetched {len(all_items)} total items from {len(self.sources)} sources.")

        # 3. Deduplicate
        new_items = [item for item in all_items if item.id not in seen_ids]
        logger.info(f"Found {len(new_items)} new items after deduplication.")
        
        if not new_items:
            logger.info("No new items to process. Exiting.")
            return

        # 4. Batch Summarize
        # Prepare the combined content for the AI
        combined_input = ""
        for i, item in enumerate(new_items, start=1):
            combined_input += f"--- Item {i} ---\n"
            combined_input += f"Title: {item.title}\n"
            combined_input += f"URL: {item.url}\n"
            combined_input += f"Content: {item.content}\n\n"

        logger.info(f"Calling AI once to summarize {len(new_items)} items...")
        try:
            curated_markdown = await self.llm_provider.summarize(combined_input, self.summarize_prompt_template)
            logger.info("AI batch summarization successful.")
        except Exception as e:
            logger.error(f"Failed to perform batch summarization: {e}", exc_info=True)
            # Fallback: simple list if AI fails completely
            curated_markdown = "## 汇总内容 (AI总结失败)\n"
            for item in new_items:
                curated_markdown += f"- [{item.title}]({item.url}): {self._fallback_summary(item.content or '')}\n"

        # 5. Send to sinks
        # We pass both the items (for metadata/tracking) and the pre-rendered content
        logger.info(f"Sending curated content to {len(self.sinks)} sinks...")
        sink_tasks = [sink.render(new_items, curated_content=curated_markdown) for sink in self.sinks]
        await asyncio.gather(*sink_tasks)
        
        # 6. Update history
        # We mark all input items as seen if the process reached here
        new_seen_ids = {item.id for item in new_items}
        seen_ids.update(new_seen_ids)
        self._save_history(seen_ids)
        logger.info("History updated.")
            
    def _fallback_summary(self, text: str) -> str:
        """Simple heuristic to truncate content if LLM fails."""
        if not text:
            return "(No content to summarize)"
        import re
        s = text.strip()
        parts = re.split(r"(?<=[.!?])\s+", s)
        if parts and len(parts[0]) > 20:
            return parts[0][:360]
        return (s[:360] + "...") if len(s) > 360 else s

    def _load_prompt(self, filename: str) -> str:
        """Loads a prompt template from the prompts directory."""
        path = os.path.join(self.prompts_dir, filename)
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            logger.error(f"Prompt template not found at '{path}'.")
            return "Summarize these items into a report:\n{content}"