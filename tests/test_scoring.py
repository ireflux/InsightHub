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
        return (
            '{"items":['
            '{"item_id":"item_0","technical_depth_and_novelty":9,"potential_impact":8,'
            '"writing_quality":7,"community_discussion":6,"engagement_signals":8,"score":8.2,'
            '"reason":"具备较高技术价值"},'
            '{"item_id":"item_1","technical_depth_and_novelty":4,"potential_impact":4,'
            '"writing_quality":5,"community_discussion":3,"engagement_signals":3,"score":3.9,'
            '"reason":"增量更新"}'
            "]}",
        )[0]

    async def classify(self, content: str, categories: List[str], prompt_template: str) -> str:
        return categories[0] if categories else "Uncategorized"


class TestScoring(unittest.IsolatedAsyncioTestCase):
    async def test_rule_scoring_and_ranking(self):
        high_item = NewsItem(
            id="https://example.com/high",
            title="Research release about distributed inference benchmark",
            url="https://example.com/high",
            source="Hacker News",
            content="A deep technical write-up with architecture details and benchmark data." * 20,
            original_data={"hn_score": 420, "hn_comments": 180},
        )
        low_item = NewsItem(
            id="https://example.com/low",
            title="Minor product update",
            url="https://example.com/low",
            source="Hacker News",
            content="Small update.",
            original_data={"hn_score": 12, "hn_comments": 1},
        )

        scorer = ContentScorer(
            config=ScoringConfig(
                enabled=True,
                use_llm=False,
                min_score_for_summary=5.0,
                keep_top_n=1,
            )
        )
        scored = await scorer.score_items([low_item, high_item])
        selected = scorer.select_items_for_summary(scored)

        self.assertIsNotNone(high_item.ai_score)
        self.assertIsNotNone(low_item.ai_score)
        self.assertGreater(high_item.ai_score, low_item.ai_score)
        self.assertEqual(len(selected), 1)
        self.assertEqual(selected[0].id, high_item.id)
        self.assertIn(high_item.score_tier, {"Interesting", "High Value", "Groundbreaking"})

    def test_tier_mapping(self):
        self.assertEqual(tier_from_score(9.2), "Groundbreaking")
        self.assertEqual(tier_from_score(7.1), "High Value")
        self.assertEqual(tier_from_score(5.5), "Interesting")
        self.assertEqual(tier_from_score(3.3), "Low Priority")
        self.assertEqual(tier_from_score(1.0), "Noise")

    async def test_batch_llm_scoring_calls_once(self):
        provider = DummyBatchProvider()
        scorer = ContentScorer(
            config=ScoringConfig(enabled=True, use_llm=True, llm_blend_alpha=0.5, max_items_for_llm_scoring=10),
            llm_provider=provider,
        )

        items = [
            NewsItem(
                id="https://example.com/1",
                title="Research benchmark",
                url="https://example.com/1",
                source="Hacker News",
                content="Deep analysis " * 50,
                original_data={"hn_score": 300, "hn_comments": 120},
            ),
            NewsItem(
                id="https://example.com/2",
                title="Small update",
                url="https://example.com/2",
                source="Hacker News",
                content="Minor update",
                original_data={"hn_score": 10, "hn_comments": 1},
            ),
        ]

        scored = await scorer.score_items(items)
        self.assertEqual(provider.calls, 1)
        self.assertTrue(all(item.ai_score is not None for item in scored))
        self.assertGreater(scored[0].ai_score, scored[1].ai_score)


if __name__ == "__main__":
    unittest.main()
