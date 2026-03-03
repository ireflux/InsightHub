import datetime
import logging
import re
from typing import List
from zoneinfo import ZoneInfo

from insighthub.llm_providers import LLMFactory
from insighthub.llm_providers.base import BaseLLMProvider
from insighthub.llm_providers.failover import FailoverLLMProvider
from insighthub.publishing import TitlePolicy
from insighthub.settings import AppSettings, LLMEndpointConfig, SinkConfig, SourceConfig
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
    primary_cfg = app_settings.llm.primary
    primary_provider = _create_provider(primary_cfg, logger=logger, role="primary")
    if primary_provider is None:
        return None

    fallback_providers: List[BaseLLMProvider] = []
    labels = [f"primary:{primary_cfg.provider}"]
    for idx, fallback_cfg in enumerate(app_settings.llm.fallbacks):
        fallback_provider = _create_provider(fallback_cfg, logger=logger, role=f"fallback[{idx}]")
        if fallback_provider is not None:
            fallback_providers.append(fallback_provider)
            labels.append(f"fallback:{fallback_cfg.provider}")

    if fallback_providers:
        return FailoverLLMProvider([primary_provider, *fallback_providers], labels)
    return primary_provider


def _create_provider(
    endpoint_config: LLMEndpointConfig,
    *,
    logger: logging.Logger,
    role: str,
) -> BaseLLMProvider | None:
    provider_name = endpoint_config.provider
    try:
        return LLMFactory.create_provider(
            provider_name,
            api_key=endpoint_config.api_key,
            model=endpoint_config.model,
        )
    except (ValueError, ImportError) as e:
        logger.error(
            "Error initializing LLM provider.",
            extra={
                "event": "workflow.llm_init_failed",
                "provider": provider_name,
                "role": role,
                "error": str(e),
            },
        )
        return None


def build_sources(app_settings: AppSettings, logger: logging.Logger) -> List[BaseSource]:
    sources: List[BaseSource] = []

    for src_config in app_settings.sources.items:
        if not src_config.enabled:
            continue
        source = _build_single_source(src_config, app_settings=app_settings, logger=logger)
        if source is not None:
            sources.append(source)
    return sources


def _build_single_source(
    src_config: SourceConfig, *, app_settings: AppSettings, logger: logging.Logger
) -> BaseSource | None:
    source_type = src_config.type
    defaults = app_settings.sources.defaults
    max_items = src_config.max_items if src_config.max_items is not None else defaults.max_items
    discover_timeout = app_settings.runtime.timeouts.source_discover_timeout_seconds
    content_fetch_concurrency = (
        src_config.content_fetch_concurrency
        if src_config.content_fetch_concurrency is not None
        else defaults.content_fetch_concurrency
    )
    content_fetch_timeout = (
        src_config.content_fetch_timeout
        if src_config.content_fetch_timeout is not None
        else defaults.content_fetch_timeout
    )
    common_kwargs = {
        "max_items": max_items,
        "discover_timeout": discover_timeout,
        "content_fetch_concurrency": content_fetch_concurrency,
        "content_fetch_timeout": content_fetch_timeout,
    }

    if source_type == "github_trending":
        return GitHubTrendingSource(**common_kwargs)
    if source_type == "zhihu_hot":
        keyword_pattern = src_config.params.get("keyword_filter")
        pattern = None
        if keyword_pattern:
            try:
                pattern = re.compile(keyword_pattern)
            except re.error as e:
                logger.warning(
                    "Invalid zhihu keyword regex; source skipped.",
                    extra={
                        "event": "workflow.source_invalid_regex",
                        "source_id": src_config.id,
                        "error": str(e),
                    },
                )
                return None
        return ZhihuHotSource(keyword_filter=pattern, **common_kwargs)
    if source_type == "hacker_news":
        return HackerNewsSource(**common_kwargs)
    if source_type == "v2ex_hot":
        return V2EXHotSource(**common_kwargs)
    if source_type == "slashdot":
        return SlashdotSource(**common_kwargs)

    logger.warning(
        "Unknown source in config, skipping.",
        extra={"event": "workflow.unknown_source", "source_type": source_type, "source_id": src_config.id},
    )
    return None


def build_sinks(
    app_settings: AppSettings,
    logger: logging.Logger,
    now: datetime.datetime | None = None,
) -> List[BaseSink]:
    sinks: List[BaseSink] = []
    tz = ZoneInfo(app_settings.runtime.timezone)
    now = now or datetime.datetime.now(tz)
    title_policy = TitlePolicy(
        template=app_settings.publishing.title.template,
        date_format=app_settings.publishing.title.date_format,
        timezone_name=app_settings.publishing.title.timezone or app_settings.runtime.timezone,
        strip_leading_h1=app_settings.publishing.title.strip_leading_h1,
    )

    for sink_config in app_settings.sinks.items:
        enabled = app_settings.sinks.defaults.enabled if sink_config.enabled is None else sink_config.enabled
        if not enabled:
            continue
        sink = _build_single_sink(
            sink_config,
            logger=logger,
            now=now,
            timezone_name=app_settings.runtime.timezone,
            title_policy=title_policy,
        )
        if sink is not None:
            sinks.append(sink)
    return sinks


def _build_single_sink(
    sink_config: SinkConfig,
    *,
    logger: logging.Logger,
    now: datetime.datetime,
    timezone_name: str,
    title_policy: TitlePolicy,
) -> BaseSink | None:
    sink_type = sink_config.type
    sink_params = sink_config.params
    if sink_type == "markdown_file":
        output_dir = sink_params.get("output_dir") or "output"
        return MarkdownFileSink(output_dir=output_dir, timezone_name=timezone_name, title_policy=title_policy)

    if sink_type == "feishu_doc":
        app_id = sink_params.get("app_id")
        app_secret = sink_params.get("app_secret")
        space_id = sink_params.get("space_id")
        doc_id = sink_params.get("doc_id")
        if app_id and app_secret:
            try:
                return FeishuDocSink(
                    app_id=app_id,
                    app_secret=app_secret,
                    title_policy=title_policy,
                    space_id=space_id,
                    doc_id=doc_id,
                )
            except ValueError as e:
                logger.error(
                    "Error initializing FeishuDocSink.",
                    extra={
                        "event": "workflow.sink_init_failed",
                        "sink": "feishu_doc",
                        "sink_id": sink_config.id,
                        "error": str(e),
                    },
                )
                return None

        logger.warning(
            "feishu_doc sink enabled but credentials are missing. Skipping.",
            extra={"event": "workflow.sink_skipped", "sink": "feishu_doc", "sink_id": sink_config.id},
        )
        return None

    logger.warning(
        "Unknown sink in config, skipping.",
        extra={"event": "workflow.unknown_sink", "sink_type": sink_type, "sink_id": sink_config.id},
    )
    return None
