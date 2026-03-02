import os
import sys
import tempfile
import unittest
from typing import List

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_DIR = os.path.join(ROOT_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from insighthub.core.engine import InsightEngine
from insighthub.llm_providers.base import BaseLLMProvider
from insighthub.models import NewsItem
from insighthub.sinks.base import BaseSink
from insighthub.sources.base import BaseSource
from insighthub.settings import RuntimeDedupConfig, ScoringConfig


class DummySource(BaseSource):
    def __init__(self, items: List[NewsItem]):
        super().__init__(name="dummy", max_items=20)
        self._items = items

    async def fetch(self) -> List[NewsItem]:
        return self._items


class DummyProvider(BaseLLMProvider):
    def __init__(self):
        self.last_content = ""

    async def summarize(self, content: str, prompt_template: str) -> str:
        self.last_content = content
        return "ok"

    async def classify(self, content: str, categories: List[str], prompt_template: str) -> str:
        return categories[0] if categories else "Uncategorized"


class DummySink(BaseSink):
    async def render(self, items: List[NewsItem], curated_content: str = None):
        return None


class TestEngineDedup(unittest.IsolatedAsyncioTestCase):
    async def test_fetch_deduplicates_tracking_urls(self):
        item1 = NewsItem(
            id="https://example.com/post?utm_source=hn&id=1",
            title="A",
            url="https://example.com/post?utm_source=hn&id=1",
            source="dummy",
            content="x",
        )
        item2 = NewsItem(
            id="https://example.com/post?id=1",
            title="A duplicate",
            url="https://example.com/post?id=1",
            source="dummy",
            content="y",
        )

        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as tmp_hist, tempfile.NamedTemporaryFile(
            "w", suffix=".json", delete=False, encoding="utf-8"
        ) as tmp_delivery:
            tmp_hist.write("[]")
            hist_path = tmp_hist.name
            tmp_delivery.write("{}")
            delivery_path = tmp_delivery.name

        engine = InsightEngine(
            sources=[DummySource([item1, item2])],
            llm_provider=DummyProvider(),
            sinks=[DummySink()],
            history_file=hist_path,
            delivery_state_file=delivery_path,
        )

        try:
            items = await engine.fetch(ignore_history=False)
            self.assertEqual(len(items), 1)
            self.assertEqual(items[0].url, "https://example.com/post?utm_source=hn&id=1")
        finally:
            os.remove(hist_path)
            os.remove(delivery_path)

    async def test_fetch_can_disable_url_normalization_dedup(self):
        item1 = NewsItem(
            id="https://example.com/post?utm_source=hn&id=1",
            title="A",
            url="https://example.com/post?utm_source=hn&id=1",
            source="dummy",
            content="x",
        )
        item2 = NewsItem(
            id="https://example.com/post?id=1",
            title="A duplicate",
            url="https://example.com/post?id=1",
            source="dummy",
            content="y",
        )

        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as tmp_hist, tempfile.NamedTemporaryFile(
            "w", suffix=".json", delete=False, encoding="utf-8"
        ) as tmp_delivery:
            tmp_hist.write("[]")
            hist_path = tmp_hist.name
            tmp_delivery.write("{}")
            delivery_path = tmp_delivery.name

        engine = InsightEngine(
            sources=[DummySource([item1, item2])],
            llm_provider=DummyProvider(),
            sinks=[DummySink()],
            history_file=hist_path,
            delivery_state_file=delivery_path,
            dedup_config=RuntimeDedupConfig(normalize_url=False, strip_query_params=["utm_source"]),
        )

        try:
            items = await engine.fetch(ignore_history=False)
            self.assertEqual(len(items), 2)
        finally:
            os.remove(hist_path)
            os.remove(delivery_path)

    async def test_history_not_updated_if_all_sinks_fail(self):
        class FailingSink(BaseSink):
            async def render(self, items: List[NewsItem], curated_content: str = None):
                raise RuntimeError("sink failure")

        item = NewsItem(
            id="https://example.com/article",
            title="A",
            url="https://example.com/article",
            source="dummy",
            content="x",
        )

        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as tmp_hist, tempfile.NamedTemporaryFile(
            "w", suffix=".json", delete=False, encoding="utf-8"
        ) as tmp_delivery:
            tmp_hist.write("[]")
            hist_path = tmp_hist.name
            tmp_delivery.write("{}")
            delivery_path = tmp_delivery.name

        engine = InsightEngine(
            sources=[DummySource([item])],
            llm_provider=DummyProvider(),
            sinks=[FailingSink()],
            history_file=hist_path,
            delivery_state_file=delivery_path,
        )

        try:
            await engine.distribute("summary", [item], update_history=True)
            with open(hist_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
            self.assertEqual(content, "[]")
        finally:
            os.remove(hist_path)
            os.remove(delivery_path)

    async def test_delivery_state_is_persisted_per_sink(self):
        item = NewsItem(
            id="https://example.com/article2",
            title="B",
            url="https://example.com/article2",
            source="dummy",
            content="x",
        )

        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as tmp_hist, tempfile.NamedTemporaryFile(
            "w", suffix=".json", delete=False, encoding="utf-8"
        ) as tmp_delivery:
            tmp_hist.write("[]")
            hist_path = tmp_hist.name
            tmp_delivery.write("{}")
            delivery_path = tmp_delivery.name

        engine = InsightEngine(
            sources=[DummySource([item])],
            llm_provider=DummyProvider(),
            sinks=[DummySink()],
            history_file=hist_path,
            delivery_state_file=delivery_path,
        )

        try:
            await engine.distribute("summary", [item], update_history=True)
            with open(delivery_path, "r", encoding="utf-8") as f:
                state = f.read()
            self.assertIn("DummySink", state)
            self.assertIn("success", state)
        finally:
            os.remove(hist_path)
            os.remove(delivery_path)

    async def test_delivery_state_prunes_old_items(self):
        item = NewsItem(
            id="https://example.com/new",
            title="new",
            url="https://example.com/new",
            source="dummy",
            content="x",
        )

        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as tmp_hist, tempfile.NamedTemporaryFile(
            "w", suffix=".json", delete=False, encoding="utf-8"
        ) as tmp_delivery:
            tmp_hist.write("[]")
            hist_path = tmp_hist.name
            tmp_delivery.write("{}")
            delivery_path = tmp_delivery.name

        engine = InsightEngine(
            sources=[DummySource([item])],
            llm_provider=DummyProvider(),
            sinks=[DummySink()],
            history_file=hist_path,
            delivery_state_file=delivery_path,
        )

        old_limit = engine.max_delivery_item_records
        engine.max_delivery_item_records = 2
        try:
            state = {
                "updated_at": None,
                "runs": [],
                "items": {
                    "a": {"sink": {"updated_at": "2026-02-20T00:00:00+00:00"}},
                    "b": {"sink": {"updated_at": "2026-02-21T00:00:00+00:00"}},
                    "c": {"sink": {"updated_at": "2026-02-22T00:00:00+00:00"}},
                },
            }
            engine._save_delivery_state(state)
            with open(delivery_path, "r", encoding="utf-8") as f:
                saved = f.read()
            self.assertIn('"b"', saved)
            self.assertIn('"c"', saved)
            self.assertNotIn('"a"', saved)
        finally:
            engine.max_delivery_item_records = old_limit
            os.remove(hist_path)
            os.remove(delivery_path)

    async def test_history_prunes_old_records(self):
        items = [
            NewsItem(
                id=f"https://example.com/{i}",
                title=f"t{i}",
                url=f"https://example.com/{i}",
                source="dummy",
                content="x",
            )
            for i in range(1, 5)
        ]

        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as tmp_hist, tempfile.NamedTemporaryFile(
            "w", suffix=".json", delete=False, encoding="utf-8"
        ) as tmp_delivery:
            tmp_hist.write("[]")
            hist_path = tmp_hist.name
            tmp_delivery.write("{}")
            delivery_path = tmp_delivery.name

        engine = InsightEngine(
            sources=[DummySource(items)],
            llm_provider=DummyProvider(),
            sinks=[DummySink()],
            history_file=hist_path,
            delivery_state_file=delivery_path,
            max_history_records=2,
        )

        try:
            await engine.distribute("summary", items, update_history=True)
            with open(hist_path, "r", encoding="utf-8") as f:
                data = f.read()
            self.assertIn("https://example.com/4", data)
            self.assertIn("https://example.com/3", data)
            self.assertNotIn("https://example.com/1", data)
            self.assertNotIn("https://example.com/2", data)
        finally:
            os.remove(hist_path)
            os.remove(delivery_path)

    async def test_run_uses_scored_subset_for_summary(self):
        low_item = NewsItem(
            id="https://example.com/low-priority",
            title="Small update",
            url="https://example.com/low-priority",
            source="Hacker News",
            content="Tiny update",
            original_data={"hn_score": 2, "hn_comments": 0},
        )
        high_item = NewsItem(
            id="https://example.com/high-priority",
            title="Major research release with benchmark",
            url="https://example.com/high-priority",
            source="Hacker News",
            content="Deep architecture analysis and benchmark results " * 40,
            original_data={"hn_score": 600, "hn_comments": 220},
        )

        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as tmp_hist, tempfile.NamedTemporaryFile(
            "w", suffix=".json", delete=False, encoding="utf-8"
        ) as tmp_delivery:
            tmp_hist.write("[]")
            hist_path = tmp_hist.name
            tmp_delivery.write("{}")
            delivery_path = tmp_delivery.name

        provider = DummyProvider()
        engine = InsightEngine(
            sources=[DummySource([low_item, high_item])],
            llm_provider=provider,
            sinks=[DummySink()],
            history_file=hist_path,
            delivery_state_file=delivery_path,
            scoring_config=ScoringConfig(enabled=True, use_llm=False, min_score_for_summary=5.0, keep_top_n=1),
        )

        try:
            await engine.run()
            self.assertIn("high-priority", provider.last_content)
            self.assertNotIn("low-priority", provider.last_content)
        finally:
            os.remove(hist_path)
            os.remove(delivery_path)


if __name__ == "__main__":
    unittest.main()
