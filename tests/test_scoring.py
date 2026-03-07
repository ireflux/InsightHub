import os
import sys
import unittest
from typing import List

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_DIR = os.path.join(ROOT_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from insighthub.llm_providers.base import BaseLLMProvider
from insighthub.models import NewsItem
from insighthub.scoring import ContentScorer, tier_from_score
from insighthub.settings import ScoringConfig


class DummyBatchProvider(BaseLLMProvider):
    def __init__(self):
        self.calls = 0

    async def summarize(self, content: str, prompt_template: str) -> str:
        self.calls += 1
        return '{"items":[{"item_id":"item_0","reason":"Top discussion in this batch."}]}'

    async def classify(self, content: str, categories: List[str], prompt_template: str) -> str:
        return categories[0] if categories else "Uncategorized"


class TestScoring(unittest.IsolatedAsyncioTestCase):
    async def test_comment_priority_and_no_comment_order(self):
        low_comments = NewsItem(
            id="https://example.com/low",
            title="Low discussion",
            url="https://example.com/low",
            source="Hacker News",
            content="Small update",
            original_data={"hn_comments": 3},
        )
        high_comments = NewsItem(
            id="https://example.com/high",
            title="High discussion",
            url="https://example.com/high",
            source="Hacker News",
            content="Major release",
            original_data={"hn_comments": 120},
        )
        github_one = NewsItem(
            id="https://github.com/a",
            title="Repo A",
            url="https://github.com/a",
            source="GitHub Trending",
            content="A",
            original_data={},
        )
        github_two = NewsItem(
            id="https://github.com/b",
            title="Repo B",
            url="https://github.com/b",
            source="GitHub Trending",
            content="B",
            original_data={},
        )

        scorer = ContentScorer(
            config=ScoringConfig(
                enabled=True,
                use_llm=False,
            )
        )

        scored = await scorer.score_items([low_comments, github_one, high_comments, github_two])
        selected = scorer.select_items_for_summary(scored)

        self.assertEqual(scored[0].id, high_comments.id)
        self.assertEqual(scored[1].id, low_comments.id)
        self.assertEqual(scored[2].id, github_one.id)
        self.assertEqual(scored[3].id, github_two.id)

        self.assertEqual(len(selected), 4)
        self.assertEqual(selected[0].id, high_comments.id)
        self.assertEqual(selected[1].id, low_comments.id)
        self.assertEqual(selected[2].id, github_one.id)
        self.assertEqual(selected[3].id, github_two.id)

    def test_tier_mapping(self):
        self.assertEqual(tier_from_score(250), "Explosive")
        self.assertEqual(tier_from_score(100), "Hot")
        self.assertEqual(tier_from_score(30), "Active")
        self.assertEqual(tier_from_score(2), "Discussed")
        self.assertEqual(tier_from_score(0), "No Discussion")

    async def test_use_llm_adds_reason_without_changing_comment_priority(self):
        provider = DummyBatchProvider()
        scorer = ContentScorer(
            config=ScoringConfig(enabled=True, use_llm=True),
            llm_provider=provider,
        )

        items = [
            NewsItem(
                id="https://example.com/1",
                title="A",
                url="https://example.com/1",
                source="Hacker News",
                content="A",
                original_data={"hn_comments": 50},
            ),
            NewsItem(
                id="https://example.com/2",
                title="B",
                url="https://example.com/2",
                source="Hacker News",
                content="B",
                original_data={"hn_comments": 10},
            ),
        ]

        scored = await scorer.score_items(items)
        self.assertEqual(provider.calls, 1)
        self.assertEqual(scored[0].id, "https://example.com/1")
        self.assertIn("Top discussion", scored[0].score_reason or "")


if __name__ == "__main__":
    unittest.main()
