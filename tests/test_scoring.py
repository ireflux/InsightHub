import os
import sys
from typing import List, Optional

import pytest

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_DIR = os.path.join(ROOT_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from insighthub.models import NewsItem
from insighthub.scoring import ContentScorer, tier_from_score
from insighthub.settings import ScoringConfig


@pytest.mark.asyncio
async def test_comment_priority_and_no_comment_order():
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

    scorer = ContentScorer(config=ScoringConfig(enabled=True))

    scored = await scorer.score_items([low_comments, github_one, high_comments, github_two])
    selected = scorer.select_items_for_summary(scored)

    assert scored[0].id == high_comments.id
    assert scored[1].id == low_comments.id
    assert scored[2].id == github_one.id
    assert scored[3].id == github_two.id

    assert len(selected) == 4
    assert selected[0].id == high_comments.id
    assert selected[1].id == low_comments.id
    assert selected[2].id == github_one.id
    assert selected[3].id == github_two.id


def test_tier_mapping():
    assert tier_from_score(250) == "Explosive"
    assert tier_from_score(100) == "Hot"
    assert tier_from_score(30) == "Active"
    assert tier_from_score(2) == "Discussed"
    assert tier_from_score(0) == "No Discussion"


@pytest.mark.asyncio
async def test_ranking_reason_is_assigned():
    scorer = ContentScorer(config=ScoringConfig(enabled=True))
    items = [
        NewsItem(
            id="https://example.com/1",
            title="A",
            url="https://example.com/1",
            source="Hacker News",
            content="A",
            original_data={"hn_comments": 50},
        )
    ]
    scored = await scorer.score_items(items)
    assert scored[0].ranking_reason


# ---- LLM scoring tests ----

class MockScoreProvider:
    """Mock LLM provider that returns controlled scoring results."""

    def __init__(self, responses: Optional[List[str]] = None):
        self.responses = responses or ['{"quality_score": 7, "include": true, "reason": "good"}']
        self.call_count = 0

    async def score(self, content: str, prompt_template: str) -> str:
        resp = self.responses[self.call_count % len(self.responses)]
        self.call_count += 1
        return resp


@pytest.mark.asyncio
async def test_llm_scoring_scores_by_quality():
    high_resp = '{"quality_score": 9, "include": true, "reason": "excellent"}'
    low_resp = '{"quality_score": 2, "include": false, "reason": "weak"}'
    provider = MockScoreProvider([high_resp, low_resp])
    config = ScoringConfig(use_llm_scoring=True, llm_scoring_threshold=0.0)
    scorer = ContentScorer(config=config, llm_provider=provider)

    items = [
        NewsItem(id="high", title="High", url="https://example.com/high", source="HN", content="important"),
        NewsItem(id="low", title="Low", url="https://example.com/low", source="HN", content="low"),
    ]
    scored = await scorer.score_items(items)

    assert scored[0].id == "high"
    assert scored[0].llm_quality_score == 9.0
    assert scored[1].id == "low"
    assert scored[1].llm_quality_score == 2.0


@pytest.mark.asyncio
async def test_llm_scoring_filters_below_threshold():
    provider = MockScoreProvider([
        '{"quality_score": 7, "include": true, "reason": "good"}',
        '{"quality_score": 3, "include": false, "reason": "weak"}',
    ])
    config = ScoringConfig(use_llm_scoring=True, llm_scoring_threshold=4.0)
    scorer = ContentScorer(config=config, llm_provider=provider)

    items = [
        NewsItem(id="good", title="Good", url="https://example.com/good", source="HN", content="good content"),
        NewsItem(id="bad", title="Bad", url="https://example.com/bad", source="HN", content="bad content"),
    ]
    scored = await scorer.score_items(items)

    assert len(scored) == 1
    assert scored[0].id == "good"


@pytest.mark.asyncio
async def test_llm_scoring_partial_failure():
    """When one item's LLM scoring fails, others should still succeed."""
    call_counter = [0]
    responses = [
        '{"quality_score": 7, "include": true, "reason": "good"}',
        '{"quality_score": 5, "include": true, "reason": "ok"}',
    ]

    class PartialFailureProvider:
        async def score(self, content: str, prompt_template: str) -> str:
            call_counter[0] += 1
            if call_counter[0] == 2:
                raise RuntimeError("API error")
            return responses[call_counter[0] - 1]

    provider = PartialFailureProvider()
    config = ScoringConfig(use_llm_scoring=True, llm_scoring_threshold=0.0)
    scorer = ContentScorer(config=config, llm_provider=provider)

    items = [
        NewsItem(id="ok", title="Ok", url="https://example.com/ok", source="HN", content="ok"),
        NewsItem(id="fail", title="Fail", url="https://example.com/fail", source="HN", content="fail"),
    ]
    scored = await scorer.score_items(items)
    assert len(scored) == 2
    assert scored[0].llm_quality_score == 7.0
    assert scored[1].llm_quality_score == 0.0  # failed item


@pytest.mark.asyncio
async def test_llm_scoring_disabled_uses_heuristic():
    provider = MockScoreProvider()
    config = ScoringConfig(use_llm_scoring=False)
    scorer = ContentScorer(config=config, llm_provider=provider)

    items = [
        NewsItem(id="a", title="A", url="https://example.com/a", source="HN", content="A",
                 original_data={"hn_score": 100, "hn_comments": 50}),
    ]
    scored = await scorer.score_items(items)

    assert len(scored) == 1
    assert scored[0].discussion_signal is not None
    # Provider should not have been called
    assert provider.call_count == 0
