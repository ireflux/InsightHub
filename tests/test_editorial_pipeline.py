import json
import os
import sys
import tempfile
from pathlib import Path
from typing import List

import pytest


ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_DIR = os.path.join(ROOT_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from insighthub.core.editorial import EditorialPipeline
from insighthub.core.engine import InsightEngine
from insighthub.llm_providers.base import BaseLLMProvider
from insighthub.models import NewsItem
from insighthub.settings import SummarizationConfig


class EditorialProvider(BaseLLMProvider):
    def __init__(self):
        self.calls: List[str] = []

    async def summarize(self, content: str, prompt_template: str) -> str:
        self.calls.append(content)
        if "结构化 brief" in content:
            include = "low" not in content
            return (
                "{"
                '"core_facts":["核心事实"],'
                '"context":["背景"],'
                '"discussion_signals":["讨论信号"],'
                '"uncertainties":["素材未提供更多细节"],'
                f'"editorial_score":{8 if include else 2},'
                f'"include":{str(include).lower()},'
                '"reason":"编辑取舍理由",'
                '"content_snippet":"核心内容片段",'
                '"top_comments":["评论1","评论2"]'
                "}"
            )
        if "值班主编" in content:
            return (
                "{"
                '"clusters":[{'
                '"title":"重要主题",'
                '"primary_item_id":"high",'
                '"item_ids":["high"],'
                '"angle":"主线角度",'
                '"include":true,'
                '"reason":"值得进入最终文章"'
                "}]"
                "}"
            )
        if "严苛的中文科技媒体审校" in content:
            return '{"passed":false,"issues":["标题需要链接"],"revision_instructions":"补上标题链接"}'
        if "请根据审校意见改稿" in content:
            return "## 今日概览\n\n修订稿\n\n## 新闻速递\n\n### [重要主题](https://example.com/high)\n\n正文\n\n## 编辑手记\n\n判断"
        return "## 今日概览\n\n初稿"

    async def score(self, content: str, prompt_template: str) -> str:
        return '{"quality_score": 7, "include": true, "reason": "test"}'


@pytest.mark.asyncio
async def test_editorial_pipeline_selects_items_and_revises_draft():
    high = NewsItem(id="high", title="High", url="https://example.com/high", source="Hacker News", content="important")
    low = NewsItem(id="low", title="Low", url="https://example.com/low", source="Hacker News", content="low")

    with tempfile.TemporaryDirectory() as tmp_dir:
        provider = EditorialProvider()
        engine = InsightEngine(
            sources=[],
            llm_provider=provider,
            sinks=[],
            history_file=str(Path(tmp_dir) / "history.json"),
            delivery_state_file=str(Path(tmp_dir) / "delivery.json"),
            stage_runs_dir=tmp_dir,
            summarization_config=SummarizationConfig(
                mode="editorial",
                brief_concurrency=2,
                max_briefs=5,
                min_final_items=1,
                max_final_items=3,
                review_enabled=True,
                revise_enabled=True,
            ),
        )

        article = await engine.summarize([low, high], run_id="run1")

        assert "修订稿" in article
        assert [item.id for item in engine.last_summarized_items] == ["high"]
        assert (Path(tmp_dir) / "run1" / "briefs.json").exists()
        assert (Path(tmp_dir) / "run1" / "clusters.json").exists()
        assert (Path(tmp_dir) / "run1" / "draft.md").exists()


@pytest.mark.asyncio
async def test_brief_includes_content_snippet():
    """Brief LLM response should populate content_snippet on ItemBrief."""
    provider = EditorialProvider()
    pipeline = EditorialPipeline(
        llm_provider=provider,
        final_prompt_template="template",
        brief_concurrency=1,
        max_briefs=5,
        min_final_items=1,
        max_final_items=3,
        review_enabled=False,
        revise_enabled=False,
    )

    item = NewsItem(
        id="test", title="Test", url="https://example.com/test",
        source="HN", content="Some content",
        original_data={"hn_score": 100, "hn_comments": 50},
    )
    result = await pipeline.run([item])

    briefs = result["briefs"]
    assert len(briefs) == 1
    assert briefs[0].content_snippet == "核心内容片段"


@pytest.mark.asyncio
async def test_brief_includes_top_comments():
    """Brief LLM response should populate top_comments on ItemBrief."""
    provider = EditorialProvider()
    pipeline = EditorialPipeline(
        llm_provider=provider,
        final_prompt_template="template",
        brief_concurrency=1,
        max_briefs=5,
        min_final_items=1,
        max_final_items=3,
        review_enabled=False,
        revise_enabled=False,
    )

    item = NewsItem(
        id="test", title="Test", url="https://example.com/test",
        source="HN", content="Some content",
        original_data={"hn_score": 100, "hn_comments": 50},
    )
    result = await pipeline.run([item])

    briefs = result["briefs"]
    assert len(briefs) == 1
    assert briefs[0].top_comments == ["评论1", "评论2"]


@pytest.mark.asyncio
async def test_review_defaults_failed_when_issues_no_passed_field():
    """When review returns issues but no explicit passed field, should default to False."""
    provider = EditorialProvider()

    # Override the review response to have issues but no passed field
    original_summarize = provider.summarize
    async def patched_summarize(content, prompt_template):
        if "严苛的中文科技媒体审校" in content:
            return '{"issues":["缺少编辑手记"],"revision_instructions":"加上手记"}'
        return await original_summarize(content, prompt_template)

    provider.summarize = patched_summarize

    pipeline = EditorialPipeline(
        llm_provider=provider,
        final_prompt_template="template",
        brief_concurrency=1,
        max_briefs=5,
        min_final_items=1,
        max_final_items=3,
        review_enabled=True,
        revise_enabled=True,
    )

    item = NewsItem(
        id="test", title="Test", url="https://example.com/test",
        source="HN", content="Some content",
        original_data={"hn_score": 100, "hn_comments": 50},
    )
    result = await pipeline.run([item])

    assert not result["review"].passed
    assert result["final_article"] == "## 今日概览\n\n修订稿\n\n## 新闻速递\n\n### [重要主题](https://example.com/high)\n\n正文\n\n## 编辑手记\n\n判断"


@pytest.mark.asyncio
async def test_article_input_has_enriched_briefs():
    """build_article_input should include content_snippet and top_comments in JSON."""
    provider = EditorialProvider()
    pipeline = EditorialPipeline(
        llm_provider=provider,
        final_prompt_template="template",
        brief_concurrency=1,
        max_briefs=5,
        min_final_items=1,
        max_final_items=3,
        review_enabled=False,
        revise_enabled=False,
    )

    item = NewsItem(
        id="test", title="Test", url="https://example.com/test",
        source="HN", content="Some content",
        original_data={"hn_score": 100, "hn_comments": 50},
    )
    result = await pipeline.run([item])

    article_input = result["article_input"]
    # The article input should contain the brief JSON with enriched fields
    for brief_json_line in article_input.split("\n"):
        if "{" in brief_json_line and "content_snippet" in brief_json_line:
            brief_data = json.loads(brief_json_line)
            assert "content_snippet" in brief_data
            assert "top_comments" in brief_data
            break
    else:
        # If no single line has both, check the full input
        assert "content_snippet" in article_input
        assert "top_comments" in article_input
