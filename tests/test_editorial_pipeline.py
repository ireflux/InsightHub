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
                '"reason":"编辑取舍理由"'
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

    async def classify(self, content: str, categories: List[str], prompt_template: str) -> str:
        return categories[0]


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
