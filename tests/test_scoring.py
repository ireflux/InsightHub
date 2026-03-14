import os
import sys

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
