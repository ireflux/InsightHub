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


class DummySource(BaseSource):
    def __init__(self, items: List[NewsItem]):
        super().__init__(name="dummy", max_items=20)
        self._items = items

    async def fetch(self) -> List[NewsItem]:
        return self._items


class DummyProvider(BaseLLMProvider):
    async def summarize(self, content: str, prompt_template: str) -> str:
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


if __name__ == "__main__":
    unittest.main()
