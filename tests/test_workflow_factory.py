import datetime
import logging
import os
import sys
import unittest

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_DIR = os.path.join(ROOT_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from insighthub.settings import AppSettings, LLMProviderConfig, SinkConfig, SourceConfig
from insighthub.workflow_factory import build_llm_provider, build_sinks, build_sources


class TestWorkflowFactory(unittest.TestCase):
    def setUp(self):
        self.logger = logging.getLogger("test.workflow_factory")

    def test_build_sources_creates_expected_instances(self):
        settings = AppSettings(
            llm_provider=LLMProviderConfig(name="zhipuai", api_key="k", model="glm-4.7-flash"),
            max_items=5,
            sources=[SourceConfig(name="github_trending"), SourceConfig(name="hacker_news")],
            sinks=[],
        )

        sources = build_sources(settings, logger=self.logger)

        self.assertEqual(len(sources), 2)
        self.assertEqual(sources[0].name, "GitHub Trending")
        self.assertEqual(sources[1].name, "Hacker News")
        self.assertEqual(sources[0].max_items, 5)

    def test_build_sinks_formats_feishu_title(self):
        settings = AppSettings(
            llm_provider=LLMProviderConfig(name="zhipuai", api_key="k", model="glm-4.7-flash"),
            max_items=5,
            sources=[],
            sinks=[
                SinkConfig(name="markdown_file", output_dir="output"),
                SinkConfig(
                    name="feishu_doc",
                    app_id="app",
                    app_secret="secret",
                    default_title="InsightHub {date}",
                    doc_id="doc-token",
                ),
            ],
        )

        now = datetime.datetime(2026, 2, 21, 9, 0, 0)
        sinks = build_sinks(settings, logger=self.logger, now=now)

        self.assertEqual(len(sinks), 2)
        feishu_sink = sinks[1]
        self.assertEqual(feishu_sink.default_title, "InsightHub 20260221")
        self.assertEqual(feishu_sink.doc_id, "doc-token")

    def test_build_llm_provider_openrouter(self):
        settings = AppSettings(
            llm_provider=LLMProviderConfig(
                name="openrouter",
                api_key="test-openrouter-key",
                model="xiaomi/mimo-v2-flash:free",
            ),
            max_items=5,
            sources=[],
            sinks=[],
        )

        provider = build_llm_provider(settings, logger=self.logger)
        self.assertIsNotNone(provider)
        self.assertEqual(provider.__class__.__name__, "OpenRouterProvider")


if __name__ == "__main__":
    unittest.main()
