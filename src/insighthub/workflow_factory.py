import datetime
import logging
import re
from typing import List

from insighthub.llm_providers import LLMFactory
from insighthub.llm_providers.base import BaseLLMProvider
from insighthub.settings import AppSettings, SinkConfig, SourceConfig
from insighthub.sinks import BaseSink, FeishuDocSink, MarkdownFileSink
from insighthub.sources import (
    GitHubTrendingSource,
    HackerNewsSource,
    SlashdotSource,
    V2EXHotSource,
    ZhihuHotSource,
)
from insighthub.sources.base import BaseSource


def build_llm_provider(app_settings: AppSettings, logger: logging.Logger) -> BaseLLMProvider | None:
    provider_name = app_settings.llm_provider.name
    provider_api_key = app_settings.llm_provider.api_key
    provider_model = app_settings.llm_provider.model
    try:
        return LLMFactory.create_provider(
            provider_name,
            api_key=provider_api_key,
            model=provider_model,
        )
    except (ValueError, ImportError) as e:
        logger.error(
            "Error initializing LLM provider.",
            extra={
                "event": "workflow.llm_init_failed",
                "provider": provider_name,
                "error": str(e),
            },
        )
        return None


def build_sources(app_settings: AppSettings, logger: logging.Logger) -> List[BaseSource]:
    sources: List[BaseSource] = []
    max_items = app_settings.max_items

    for src_config in app_settings.sources:
        source = _build_single_source(src_config, max_items=max_items, logger=logger)
        if source is not None:
            sources.append(source)
    return sources


def _build_single_source(
    src_config: SourceConfig, *, max_items: int, logger: logging.Logger
) -> BaseSource | None:
    source_name = src_config.name
    if source_name == "github_trending":
        return GitHubTrendingSource(max_items=max_items)
    if source_name == "zhihu_hot":
        keyword_pattern = src_config.keyword_filter
        pattern = None
        if keyword_pattern:
            try:
                pattern = re.compile(keyword_pattern)
            except re.error as e:
                logger.warning(
                    "Invalid zhihu keyword regex; source skipped.",
                    extra={
                        "event": "workflow.source_invalid_regex",
                        "source_name": source_name,
                        "error": str(e),
                    },
                )
                return None
        return ZhihuHotSource(keyword_filter=pattern, max_items=max_items)
    if source_name == "hacker_news":
        return HackerNewsSource(max_items=max_items)
    if source_name == "v2ex_hot":
        return V2EXHotSource(max_items=max_items)
    if source_name == "slashdot":
        return SlashdotSource(max_items=max_items)

    logger.warning(
        "Unknown source in config, skipping.",
        extra={"event": "workflow.unknown_source", "source_name": source_name},
    )
    return None


def build_sinks(
    app_settings: AppSettings,
    logger: logging.Logger,
    now: datetime.datetime | None = None,
) -> List[BaseSink]:
    sinks: List[BaseSink] = []
    now = now or datetime.datetime.now()

    for sink_config in app_settings.sinks:
        sink = _build_single_sink(sink_config, logger=logger, now=now)
        if sink is not None:
            sinks.append(sink)
    return sinks


def _build_single_sink(
    sink_config: SinkConfig,
    *,
    logger: logging.Logger,
    now: datetime.datetime,
) -> BaseSink | None:
    sink_name = sink_config.name
    if sink_name == "markdown_file":
        output_dir = sink_config.output_dir or "output"
        return MarkdownFileSink(output_dir=output_dir)

    if sink_name == "feishu_doc":
        app_id = sink_config.app_id
        app_secret = sink_config.app_secret
        space_id = sink_config.space_id
        doc_id = sink_config.doc_id
        default_title = sink_config.default_title or "InsightHub"
        formatted_title = _format_title(default_title, now)

        if app_id and app_secret:
            try:
                return FeishuDocSink(
                    app_id=app_id,
                    app_secret=app_secret,
                    default_title=formatted_title,
                    space_id=space_id,
                    doc_id=doc_id,
                )
            except ValueError as e:
                logger.error(
                    "Error initializing FeishuDocSink.",
                    extra={
                        "event": "workflow.sink_init_failed",
                        "sink": "feishu_doc",
                        "error": str(e),
                    },
                )
                return None

        logger.warning(
            "feishu_doc sink enabled but credentials are missing. Skipping.",
            extra={"event": "workflow.sink_skipped", "sink": "feishu_doc"},
        )
        return None

    logger.warning(
        "Unknown sink in config, skipping.",
        extra={"event": "workflow.unknown_sink", "sink_name": sink_name},
    )
    return None


def _format_title(template: str, now: datetime.datetime) -> str:
    date_str = now.strftime("%Y%m%d")
    try:
        return template.format(date=date_str)
    except Exception:
        return template.replace("{date}", date_str)
