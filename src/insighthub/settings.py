import os
import yaml
import logging
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from insighthub.errors import ConfigValidationError

logger = logging.getLogger(__name__)

SUPPORTED_LLM_PROVIDERS = {"openrouter", "zhipuai"}
SUPPORTED_SOURCES = {"github_trending", "zhihu_hot", "hacker_news", "v2ex_hot", "slashdot"}
SUPPORTED_SINKS = {"markdown_file", "feishu_doc"}


class LLMProviderConfig(BaseModel):
    name: str
    api_key: Optional[str] = None
    model: str = "glm-4.7-flash"

class SourceConfig(BaseModel):
    name: str
    keyword_filter: Optional[str] = None

class SinkConfig(BaseModel):
    name: str
    output_dir: Optional[str] = "output"
    app_id: Optional[str] = None
    app_secret: Optional[str] = None
    default_title: Optional[str] = "InsightHub Summary"
    space_id: Optional[str] = None
    doc_id: Optional[str] = None


class PromptConfig(BaseModel):
    structure: str = "professional_briefing_v1"
    style: str = "professional_neutral_v1"
    variables: Dict[str, Any] = Field(default_factory=dict)


class AppSettings(BaseModel):
    llm_provider: LLMProviderConfig
    max_items: int = 8
    sources: List[SourceConfig] = Field(default_factory=list)
    sinks: List[SinkConfig] = Field(default_factory=list)
    prompt: PromptConfig = Field(default_factory=PromptConfig)

    class Config:
        extra = "forbid"

    def validate_schema_rules(self) -> None:
        provider = self.llm_provider.name.lower()
        if provider not in SUPPORTED_LLM_PROVIDERS:
            raise ConfigValidationError(
                f"Unsupported llm_provider.name '{self.llm_provider.name}'. "
                f"Supported: {sorted(SUPPORTED_LLM_PROVIDERS)}"
            )

        source_names = [source.name for source in self.sources]
        unsupported_sources = sorted({name for name in source_names if name not in SUPPORTED_SOURCES})
        if unsupported_sources:
            raise ConfigValidationError(
                f"Unsupported source names: {unsupported_sources}. "
                f"Supported: {sorted(SUPPORTED_SOURCES)}"
            )
        if len(source_names) != len(set(source_names)):
            raise ConfigValidationError("Duplicate source names found in config.")

        sink_names = [sink.name for sink in self.sinks]
        unsupported_sinks = sorted({name for name in sink_names if name not in SUPPORTED_SINKS})
        if unsupported_sinks:
            raise ConfigValidationError(
                f"Unsupported sink names: {unsupported_sinks}. "
                f"Supported: {sorted(SUPPORTED_SINKS)}"
            )
        if len(sink_names) != len(set(sink_names)):
            raise ConfigValidationError("Duplicate sink names found in config.")

        for sink in self.sinks:
            if sink.name == "markdown_file" and not sink.output_dir:
                raise ConfigValidationError("Sink 'markdown_file' requires output_dir.")
            if sink.name == "feishu_doc" and sink.doc_id and sink.space_id:
                logger.warning("Both feishu_doc.doc_id and space_id are set; doc_id will take precedence.")

    def validate_runtime_requirements(self) -> None:
        provider = self.llm_provider.name.lower()
        if provider == "openrouter" and not self.llm_provider.api_key:
            raise ConfigValidationError("Missing OPENROUTER_API_KEY for provider 'openrouter'.")
        if provider == "zhipuai" and not self.llm_provider.api_key:
            raise ConfigValidationError("Missing ZHIPUAI_API_KEY for provider 'zhipuai'.")

        for sink in self.sinks:
            if sink.name == "feishu_doc":
                if not sink.app_id or not sink.app_secret:
                    raise ConfigValidationError(
                        "Sink 'feishu_doc' requires FEISHU_APP_ID and FEISHU_APP_SECRET."
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
        
        # LLM Provider setup
        if "llm_provider" not in config_data:
            config_data["llm_provider"] = {"name": "zhipuai", "model": "glm-4.7-flash"} # default
            
        provider_config = config_data["llm_provider"]
        provider_name = provider_config.get("name")

        # Security hardening: always read sensitive values from env.
        if provider_config.get("api_key"):
            logger.warning("`llm_provider.api_key` in config is ignored for security; use environment variables instead.")
        provider_config["api_key"] = None

        env_api_key = None
        if provider_name == "openrouter":
            env_api_key = os.getenv("OPENROUTER_API_KEY")
        elif provider_name == "zhipuai":
            env_api_key = os.getenv("ZHIPUAI_API_KEY")
        if env_api_key:
            provider_config["api_key"] = env_api_key
        
        # LLM Model fallback
        if not provider_config.get("model"):
            env_model = os.getenv("LLM_MODEL")
            if env_model:
                provider_config["model"] = env_model

        # Feishu credentials fallback (env-preferred for secrets)
        if "sinks" in config_data:
            for sink in config_data["sinks"]:
                if sink.get("name") == "feishu_doc":
                    if sink.get("app_id") or sink.get("app_secret"):
                        logger.warning("`feishu_doc.app_id/app_secret` in config are ignored for security; use env vars.")
                    sink["app_id"] = os.getenv("FEISHU_APP_ID")
                    sink["app_secret"] = os.getenv("FEISHU_APP_SECRET")
                    sink["space_id"] = sink.get("space_id") or os.getenv("FEISHU_SPACE_ID")
                    sink["doc_id"] = sink.get("doc_id") or os.getenv("FEISHU_DOC_ID")

        settings_obj = cls(**config_data)
        settings_obj.validate_schema_rules()
        return settings_obj

settings = AppSettings.load()
