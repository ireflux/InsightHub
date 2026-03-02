import os
import yaml
import logging
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from pydantic import BaseModel, Field

from insighthub.errors import ConfigValidationError

logger = logging.getLogger(__name__)

SUPPORTED_LLM_PROVIDERS = {"openrouter", "zhipuai"}
SUPPORTED_SOURCES = {"github_trending", "zhihu_hot", "hacker_news", "v2ex_hot", "slashdot"}
SUPPORTED_SINKS = {"markdown_file", "feishu_doc"}


class LLMEndpointConfig(BaseModel):
    provider: str
    api_key: Optional[str] = None
    model: Optional[str] = None


class LLMConfig(BaseModel):
    primary: LLMEndpointConfig = Field(
        default_factory=lambda: LLMEndpointConfig(provider="zhipuai", model="glm-4.7-flash")
    )
    fallbacks: List[LLMEndpointConfig] = Field(default_factory=list)


class SourceDefaultsConfig(BaseModel):
    max_items: int = 8
    content_fetch_concurrency: int = 4
    content_fetch_timeout: float = 10.0


class SourceConfig(BaseModel):
    id: str
    type: str
    enabled: bool = True
    max_items: Optional[int] = None
    content_fetch_concurrency: Optional[int] = None
    content_fetch_timeout: Optional[float] = None
    params: Dict[str, Any] = Field(default_factory=dict)


class SourcesConfig(BaseModel):
    defaults: SourceDefaultsConfig = Field(default_factory=SourceDefaultsConfig)
    items: List[SourceConfig] = Field(default_factory=list)


class SinkDefaultsConfig(BaseModel):
    enabled: bool = True


class SinkConfig(BaseModel):
    id: str
    type: str
    enabled: Optional[bool] = None
    params: Dict[str, Any] = Field(default_factory=dict)


class SinksConfig(BaseModel):
    defaults: SinkDefaultsConfig = Field(default_factory=SinkDefaultsConfig)
    items: List[SinkConfig] = Field(default_factory=list)


class PromptConfig(BaseModel):
    structure: str = "professional_briefing_v1"
    style: str = "professional_neutral_v1"
    variables: Dict[str, Any] = Field(default_factory=dict)


class StateConfig(BaseModel):
    max_history_records: int = 3000
    max_delivery_item_records: int = 2000
    max_delivery_runs: int = 100


class ScoringWeights(BaseModel):
    technical_depth_and_novelty: float = 0.30
    potential_impact: float = 0.25
    writing_quality: float = 0.15
    community_discussion: float = 0.15
    engagement_signals: float = 0.15


class ScoringConfig(BaseModel):
    enabled: bool = False
    use_llm: bool = False
    llm_blend_alpha: float = 0.7
    min_score_for_summary: float = 0.0
    keep_top_n: Optional[int] = None
    max_items_for_llm_scoring: int = 20
    weights: ScoringWeights = Field(default_factory=ScoringWeights)


class RetryPolicyConfig(BaseModel):
    max_attempts: int = 3
    base_delay_seconds: float = 1.0
    backoff_multiplier: float = 2.0
    max_delay_seconds: float = 30.0


class RuntimeRetryConfig(BaseModel):
    source_fetch: RetryPolicyConfig = Field(default_factory=lambda: RetryPolicyConfig(max_attempts=3, base_delay_seconds=1.0))
    llm_summarize: RetryPolicyConfig = Field(default_factory=lambda: RetryPolicyConfig(max_attempts=3, base_delay_seconds=2.0))
    sink_render: RetryPolicyConfig = Field(default_factory=lambda: RetryPolicyConfig(max_attempts=2, base_delay_seconds=1.0))


class RuntimeTimeoutsConfig(BaseModel):
    source_discover_timeout_seconds: float = 20.0


class RuntimeDedupConfig(BaseModel):
    normalize_url: bool = True
    strip_query_params: List[str] = Field(
        default_factory=lambda: [
            "utm_source",
            "utm_medium",
            "utm_campaign",
            "utm_term",
            "utm_content",
            "ref",
            "source",
        ]
    )


class RuntimePathsConfig(BaseModel):
    prompts_dir: str = "prompts"
    history_file: str = "history.json"
    delivery_state_file: str = "delivery_state.json"
    logs_dir: str = "logs"


class ObservabilityConfig(BaseModel):
    level: str = "INFO"
    format: str = "json"
    console_enabled: bool = True
    file_enabled: bool = True
    file_name_prefix: str = "insighthub"


class RuntimeConfig(BaseModel):
    timezone: str = "Asia/Shanghai"
    paths: RuntimePathsConfig = Field(default_factory=RuntimePathsConfig)
    retry: RuntimeRetryConfig = Field(default_factory=RuntimeRetryConfig)
    timeouts: RuntimeTimeoutsConfig = Field(default_factory=RuntimeTimeoutsConfig)
    dedup: RuntimeDedupConfig = Field(default_factory=RuntimeDedupConfig)
    observability: ObservabilityConfig = Field(default_factory=ObservabilityConfig)


class AppSettings(BaseModel):
    llm: LLMConfig = Field(default_factory=LLMConfig)
    sources: SourcesConfig = Field(default_factory=SourcesConfig)
    sinks: SinksConfig = Field(default_factory=SinksConfig)
    prompt: PromptConfig = Field(default_factory=PromptConfig)
    state: StateConfig = Field(default_factory=StateConfig)
    scoring: ScoringConfig = Field(default_factory=ScoringConfig)
    runtime: RuntimeConfig = Field(default_factory=RuntimeConfig)

    class Config:
        extra = "forbid"

    def validate_schema_rules(self) -> None:
        endpoints = [self.llm.primary, *self.llm.fallbacks]
        unsupported_providers = sorted(
            {ep.provider for ep in endpoints if ep.provider.lower() not in SUPPORTED_LLM_PROVIDERS}
        )
        if unsupported_providers:
            raise ConfigValidationError(
                f"Unsupported llm providers: {unsupported_providers}. "
                f"Supported: {sorted(SUPPORTED_LLM_PROVIDERS)}"
            )

        source_ids = [source.id for source in self.sources.items]
        if len(source_ids) != len(set(source_ids)):
            raise ConfigValidationError("Duplicate source ids found in config.")

        source_types = [source.type for source in self.sources.items]
        unsupported_sources = sorted({name for name in source_types if name not in SUPPORTED_SOURCES})
        if unsupported_sources:
            raise ConfigValidationError(
                f"Unsupported source types: {unsupported_sources}. "
                f"Supported: {sorted(SUPPORTED_SOURCES)}"
            )

        sink_ids = [sink.id for sink in self.sinks.items]
        if len(sink_ids) != len(set(sink_ids)):
            raise ConfigValidationError("Duplicate sink ids found in config.")

        sink_types = [sink.type for sink in self.sinks.items]
        unsupported_sinks = sorted({name for name in sink_types if name not in SUPPORTED_SINKS})
        if unsupported_sinks:
            raise ConfigValidationError(
                f"Unsupported sink types: {unsupported_sinks}. "
                f"Supported: {sorted(SUPPORTED_SINKS)}"
            )

        if self.sources.defaults.max_items <= 0:
            raise ConfigValidationError("sources.defaults.max_items must be > 0.")
        if self.sources.defaults.content_fetch_concurrency <= 0:
            raise ConfigValidationError("sources.defaults.content_fetch_concurrency must be > 0.")
        if self.sources.defaults.content_fetch_timeout <= 0:
            raise ConfigValidationError("sources.defaults.content_fetch_timeout must be > 0.")

        for source in self.sources.items:
            if not source.id.strip():
                raise ConfigValidationError("sources.items[].id must not be empty.")
            if source.max_items is not None and source.max_items <= 0:
                raise ConfigValidationError(f"sources.items[{source.id}].max_items must be > 0 when provided.")
            if source.content_fetch_concurrency is not None and source.content_fetch_concurrency <= 0:
                raise ConfigValidationError(
                    f"sources.items[{source.id}].content_fetch_concurrency must be > 0 when provided."
                )
            if source.content_fetch_timeout is not None and source.content_fetch_timeout <= 0:
                raise ConfigValidationError(
                    f"sources.items[{source.id}].content_fetch_timeout must be > 0 when provided."
                )

        for sink in self.sinks.items:
            if not sink.id.strip():
                raise ConfigValidationError("sinks.items[].id must not be empty.")
            enabled = self.sinks.defaults.enabled if sink.enabled is None else sink.enabled
            if not enabled:
                continue
            if sink.type == "markdown_file":
                output_dir = sink.params.get("output_dir")
                if output_dir is not None and not str(output_dir).strip():
                    raise ConfigValidationError(f"sinks.items[{sink.id}] markdown_file.output_dir cannot be empty.")
            if sink.type == "feishu_doc":
                doc_id = sink.params.get("doc_id")
                space_id = sink.params.get("space_id")
                if doc_id and space_id:
                    logger.warning("Both feishu_doc.params.doc_id and space_id are set; doc_id will take precedence.")

        if self.state.max_history_records <= 0:
            raise ConfigValidationError("state.max_history_records must be > 0.")
        if self.state.max_delivery_item_records <= 0:
            raise ConfigValidationError("state.max_delivery_item_records must be > 0.")
        if self.state.max_delivery_runs <= 0:
            raise ConfigValidationError("state.max_delivery_runs must be > 0.")

        self._validate_retry_policy("runtime.retry.source_fetch", self.runtime.retry.source_fetch)
        self._validate_retry_policy("runtime.retry.llm_summarize", self.runtime.retry.llm_summarize)
        self._validate_retry_policy("runtime.retry.sink_render", self.runtime.retry.sink_render)

        if self.runtime.timeouts.source_discover_timeout_seconds <= 0:
            raise ConfigValidationError("runtime.timeouts.source_discover_timeout_seconds must be > 0.")
        if not self.runtime.paths.prompts_dir.strip():
            raise ConfigValidationError("runtime.paths.prompts_dir must not be empty.")
        if not self.runtime.paths.history_file.strip():
            raise ConfigValidationError("runtime.paths.history_file must not be empty.")
        if not self.runtime.paths.delivery_state_file.strip():
            raise ConfigValidationError("runtime.paths.delivery_state_file must not be empty.")
        if not self.runtime.paths.logs_dir.strip():
            raise ConfigValidationError("runtime.paths.logs_dir must not be empty.")
        try:
            ZoneInfo(self.runtime.timezone)
        except ZoneInfoNotFoundError as e:
            raise ConfigValidationError(f"runtime.timezone is invalid: {self.runtime.timezone}") from e

        observability_level = self.runtime.observability.level.upper()
        if observability_level not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
            raise ConfigValidationError(
                "runtime.observability.level must be one of DEBUG, INFO, WARNING, ERROR, CRITICAL."
            )
        if self.runtime.observability.format not in {"json", "text"}:
            raise ConfigValidationError("runtime.observability.format must be 'json' or 'text'.")
        if not self.runtime.observability.file_name_prefix.strip():
            raise ConfigValidationError("runtime.observability.file_name_prefix must not be empty.")

        if not (0.0 <= self.scoring.min_score_for_summary <= 10.0):
            raise ConfigValidationError("scoring.min_score_for_summary must be within [0, 10].")
        if not (0.0 <= self.scoring.llm_blend_alpha <= 1.0):
            raise ConfigValidationError("scoring.llm_blend_alpha must be within [0, 1].")
        if self.scoring.max_items_for_llm_scoring <= 0:
            raise ConfigValidationError("scoring.max_items_for_llm_scoring must be > 0.")
        if self.scoring.keep_top_n is not None and self.scoring.keep_top_n <= 0:
            raise ConfigValidationError("scoring.keep_top_n must be > 0 when provided.")

        weight_values = self.scoring.weights.model_dump().values()
        if any(v < 0 for v in weight_values):
            raise ConfigValidationError("scoring.weights values must be >= 0.")
        if sum(weight_values) <= 0:
            raise ConfigValidationError("scoring.weights must have a positive total.")

    def validate_runtime_requirements(self) -> None:
        endpoints = [("llm.primary", self.llm.primary)] + [
            (f"llm.fallbacks[{i}]", ep) for i, ep in enumerate(self.llm.fallbacks)
        ]
        for location, endpoint in endpoints:
            if endpoint.provider.lower() == "openrouter" and not endpoint.api_key:
                raise ConfigValidationError(f"Missing OPENROUTER_API_KEY for {location} provider 'openrouter'.")
            if endpoint.provider.lower() == "zhipuai" and not endpoint.api_key:
                raise ConfigValidationError(f"Missing ZHIPUAI_API_KEY for {location} provider 'zhipuai'.")

        for sink in self.sinks.items:
            enabled = self.sinks.defaults.enabled if sink.enabled is None else sink.enabled
            if sink.type == "feishu_doc" and enabled:
                app_id = sink.params.get("app_id")
                app_secret = sink.params.get("app_secret")
                if not app_id or not app_secret:
                    raise ConfigValidationError(
                        f"Sink '{sink.id}' (feishu_doc) requires FEISHU_APP_ID and FEISHU_APP_SECRET."
                    )

    @classmethod
    def load(cls, config_path: str = "configs/config.yaml") -> "AppSettings":
        # 1. Load from YAML
        config_data = {}
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    config_data = yaml.safe_load(f) or {}
            except Exception as e:
                logger.warning(f"Failed to load config file {config_path}: {e}")
        
        # 2. Process environment variable fallbacks
        if "llm" not in config_data:
            config_data["llm"] = {"primary": {"provider": "zhipuai", "model": "glm-4.7-flash"}, "fallbacks": []}

        llm_config = config_data["llm"]
        primary_cfg = llm_config.get("primary") or {}
        if primary_cfg.get("api_key"):
            logger.warning("`llm.primary.api_key` in config is ignored for security; use environment variables instead.")
        primary_cfg["api_key"] = cls._api_key_from_env(primary_cfg.get("provider"))
        llm_config["primary"] = primary_cfg

        fallback_cfgs = llm_config.get("fallbacks") or []
        for endpoint in fallback_cfgs:
            if endpoint.get("api_key"):
                logger.warning("`llm.fallbacks[].api_key` in config is ignored for security; use environment variables instead.")
            endpoint["api_key"] = cls._api_key_from_env(endpoint.get("provider"))
        llm_config["fallbacks"] = fallback_cfgs

        sinks_cfg = config_data.get("sinks") or {}
        sink_items = sinks_cfg.get("items") or []
        for sink in sink_items:
            if sink.get("type") == "feishu_doc":
                params = sink.get("params") or {}
                if params.get("app_id") or params.get("app_secret"):
                    logger.warning("`feishu_doc.params.app_id/app_secret` in config are ignored for security; use env vars.")
                params["app_id"] = os.getenv("FEISHU_APP_ID")
                params["app_secret"] = os.getenv("FEISHU_APP_SECRET")
                params["space_id"] = params.get("space_id") or os.getenv("FEISHU_SPACE_ID")
                params["doc_id"] = params.get("doc_id") or os.getenv("FEISHU_DOC_ID")
                sink["params"] = params
        sinks_cfg["items"] = sink_items
        config_data["sinks"] = sinks_cfg

        settings_obj = cls(**config_data)
        settings_obj.validate_schema_rules()
        return settings_obj

    @staticmethod
    def _validate_retry_policy(location: str, policy: RetryPolicyConfig) -> None:
        if policy.max_attempts <= 0:
            raise ConfigValidationError(f"{location}.max_attempts must be > 0.")
        if policy.base_delay_seconds <= 0:
            raise ConfigValidationError(f"{location}.base_delay_seconds must be > 0.")
        if policy.backoff_multiplier < 1:
            raise ConfigValidationError(f"{location}.backoff_multiplier must be >= 1.")
        if policy.max_delay_seconds <= 0:
            raise ConfigValidationError(f"{location}.max_delay_seconds must be > 0.")

    @staticmethod
    def _api_key_from_env(provider_name: Optional[str]) -> Optional[str]:
        if not provider_name:
            return None
        provider = provider_name.lower()
        if provider == "openrouter":
            return os.getenv("OPENROUTER_API_KEY")
        if provider == "zhipuai":
            return os.getenv("ZHIPUAI_API_KEY")
        return None

settings = AppSettings.load()
