import datetime
import logging
import os
import sys
import unittest

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_DIR = os.path.join(ROOT_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from insighthub.settings import AppSettings
from insighthub.workflow_factory import build_llm_provider, build_sinks, build_sources


class TestWorkflowFactory(unittest.TestCase):
    def setUp(self):
        self.logger = logging.getLogger("test.workflow_factory")

    def test_build_sources_creates_expected_instances(self):
        settings = AppSettings(
            llm={"primary": {"provider": "zhipuai", "api_key": "k", "model": "glm-4.7-flash"}},
            runtime={"timeouts": {"source_discover_timeout_seconds": 15.0}},
            sources={
                "defaults": {"max_items": 5, "content_fetch_concurrency": 3, "content_fetch_timeout": 8.0},
                "items": [
                    {"id": "gh", "type": "github_trending", "enabled": True, "params": {}},
                    {"id": "hn", "type": "hacker_news", "enabled": True, "params": {}},
                ],
            },
            sinks={"defaults": {"enabled": True}, "items": []},
        )

        sources = build_sources(settings, logger=self.logger)

        self.assertEqual(len(sources), 2)
        self.assertEqual(sources[0].name, "GitHub Trending")
        self.assertEqual(sources[1].name, "Hacker News")
        self.assertEqual(sources[0].max_items, 5)
        self.assertEqual(sources[0].discover_timeout, 15.0)
        self.assertEqual(sources[0].content_fetch_concurrency, 3)
        self.assertEqual(sources[0].content_fetch_timeout, 8.0)

    def test_build_sinks_uses_global_publishing_title_policy(self):
        settings = AppSettings(
            llm={"primary": {"provider": "zhipuai", "api_key": "k", "model": "glm-4.7-flash"}},
            sources={"defaults": {"max_items": 5}, "items": []},
            publishing={"title": {"template": "每日技术趋势观察 {date}", "date_format": "%Y-%m-%d"}},
            sinks={
                "defaults": {"enabled": True},
                "items": [
                    {"id": "md", "type": "markdown_file", "params": {"output_dir": "output"}},
                    {
                        "id": "feishu",
                        "type": "feishu_doc",
                        "params": {
                            "app_id": "app",
                            "app_secret": "secret",
                            "doc_id": "doc-token",
                        },
                    },
                ],
            },
        )

        now = datetime.datetime(2026, 2, 21, 9, 0, 0)
        sinks = build_sinks(settings, logger=self.logger, now=now)

        self.assertEqual(len(sinks), 2)
        feishu_sink = sinks[1]
        self.assertEqual(feishu_sink.title_policy.render(now), "每日技术趋势观察 2026-02-21")
        self.assertEqual(feishu_sink.doc_id, "doc-token")

    def test_build_llm_provider_openrouter(self):
        settings = AppSettings(
            llm={"primary": {"provider": "openrouter", "api_key": "test-openrouter-key", "model": "xiaomi/mimo-v2-flash:free"}},
            sources={"defaults": {"max_items": 5}, "items": []},
            sinks={"defaults": {"enabled": True}, "items": []},
        )

        provider = build_llm_provider(settings, logger=self.logger)
        self.assertIsNotNone(provider)
        self.assertEqual(provider.__class__.__name__, "OpenRouterProvider")

    def test_build_llm_provider_with_fallbacks(self):
        settings = AppSettings(
            llm={
                "primary": {"provider": "zhipuai", "api_key": "primary_key", "model": "glm-4.7-flash"},
                "fallbacks": [{"provider": "openrouter", "api_key": "fallback_key", "model": "xiaomi/mimo-v2-flash:free"}],
            },
            sources={"defaults": {"max_items": 5}, "items": []},
            sinks={"defaults": {"enabled": True}, "items": []},
        )

        provider = build_llm_provider(settings, logger=self.logger)
        self.assertIsNotNone(provider)
        self.assertEqual(provider.__class__.__name__, "FailoverLLMProvider")


if __name__ == "__main__":
    unittest.main()
