import json
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
from insighthub.observability import set_run_id
from insighthub.sinks.markdown import MarkdownFileSink
from insighthub.sources.base import BaseSource


class DummyProvider(BaseLLMProvider):
    async def summarize(self, content: str, prompt_template: str) -> str:
        return "ok"

    async def classify(self, content: str, categories: List[str], prompt_template: str) -> str:
        return categories[0] if categories else "Uncategorized"


class EmptySource(BaseSource):
    def __init__(self):
        super().__init__(name="empty", max_items=10)

    async def fetch(self) -> List[NewsItem]:
        return []


class TestMarkdownSink(unittest.IsolatedAsyncioTestCase):
    async def test_sink_uses_run_id_filename_and_manifest(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            set_run_id("run123")
            sink = MarkdownFileSink(output_dir=tmp_dir, timezone_name="Asia/Shanghai")
            items = [
                NewsItem(
                    id="https://example.com/a",
                    title="A",
                    url="https://example.com/a",
                    source="Hacker News",
                    content="x",
                )
            ]

            result = await sink.render(items, curated_content="# InsightHub 每日技术趋势观察\n\nSummary line.")
            self.assertEqual(result["status"], "success")
            self.assertIn("-run123.md", result["file_path"].replace("\\", "/"))

            with open(result["file_path"], "r", encoding="utf-8") as f:
                md_body = f.read()
            self.assertFalse(md_body.lstrip().startswith("# "))
            self.assertIn("Summary line.", md_body)

            with open(result["manifest_path"], "r", encoding="utf-8") as f:
                manifest = json.load(f)
            self.assertEqual(len(manifest["posts"]), 1)
            post = manifest["posts"][0]
            self.assertEqual(post["run_id"], "run123")
            self.assertEqual(post["title"], "每日技术趋势观察 " + post["date"])
            self.assertIn("hacker_news", post["tags"])
            self.assertFalse(post["is_empty_update"])

    async def test_sink_supports_empty_update_page(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            set_run_id("empty123")
            sink = MarkdownFileSink(output_dir=tmp_dir, timezone_name="Asia/Shanghai")
            result = await sink.render([], curated_content="# 每日技术趋势观察\n\n> 今日无更新。")
            self.assertEqual(result["status"], "success")
            self.assertTrue(result["is_empty_update"])

            with open(result["file_path"], "r", encoding="utf-8") as f:
                md_body = f.read()
            self.assertFalse(md_body.lstrip().startswith("# "))

            with open(result["manifest_path"], "r", encoding="utf-8") as f:
                manifest = json.load(f)
            self.assertTrue(manifest["posts"][0]["is_empty_update"])
            self.assertEqual(manifest["posts"][0]["item_count"], 0)
            self.assertEqual(
                manifest["posts"][0]["title"],
                "每日技术趋势观察 " + manifest["posts"][0]["date"],
            )

    async def test_engine_run_generates_no_update_post(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            hist_fd, hist_path = tempfile.mkstemp(suffix=".json")
            delivery_fd, delivery_path = tempfile.mkstemp(suffix=".json")
            os.close(hist_fd)
            os.close(delivery_fd)
            try:
                with open(hist_path, "w", encoding="utf-8") as f:
                    f.write("[]")
                with open(delivery_path, "w", encoding="utf-8") as f:
                    f.write("{}")
                set_run_id("norun123")

                sink = MarkdownFileSink(output_dir=tmp_dir, timezone_name="Asia/Shanghai")
                engine = InsightEngine(
                    sources=[EmptySource()],
                    llm_provider=DummyProvider(),
                    sinks=[sink],
                    history_file=hist_path,
                    delivery_state_file=delivery_path,
                    timezone_name="Asia/Shanghai",
                )
                await engine.run()

                manifest_path = os.path.join(tmp_dir, "manifest", "index.json")
                with open(manifest_path, "r", encoding="utf-8") as f:
                    manifest = json.load(f)
                self.assertEqual(len(manifest["posts"]), 1)
                self.assertTrue(manifest["posts"][0]["is_empty_update"])
                self.assertEqual(
                    manifest["posts"][0]["title"],
                    "每日技术趋势观察 " + manifest["posts"][0]["date"],
                )
            finally:
                os.remove(hist_path)
                os.remove(delivery_path)


if __name__ == "__main__":
    unittest.main()
