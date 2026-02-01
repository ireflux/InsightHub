import os
import yaml
import logging
from typing import List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class LLMProviderConfig(BaseModel):
    name: str
    api_key: Optional[str] = None
    model: str = "glm-4-flash"

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

class AppSettings(BaseModel):
    llm_provider: LLMProviderConfig
    sources: List[SourceConfig] = Field(default_factory=list)
    sinks: List[SinkConfig] = Field(default_factory=list)

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
        
        # 2. Process Environment Variable Overrides
        
        # LLM API Keys
        if "llm_provider" not in config_data:
            config_data["llm_provider"] = {"name": "zhipuai", "model": "glm-4-flash"} # default
            
        provider_name = config_data["llm_provider"].get("name")
        env_api_key = None
        if provider_name == "openrouter":
            env_api_key = os.getenv("OPENROUTER_API_KEY")
        elif provider_name == "zhipuai":
            env_api_key = os.getenv("ZHIPUAI_API_KEY")
        
        if env_api_key:
            config_data["llm_provider"]["api_key"] = env_api_key

        # Feishu Credentials (scanning sinks)
        feishu_app_id = os.getenv("FEISHU_APP_ID")
        feishu_app_secret = os.getenv("FEISHU_APP_SECRET")
        feishu_space_id = os.getenv("FEISHU_SPACE_ID") # Optional override for space_id

        if "sinks" in config_data:
            for sink in config_data["sinks"]:
                if sink.get("name") == "feishu_doc":
                    if feishu_app_id:
                        sink["app_id"] = feishu_app_id
                    if feishu_app_secret:
                        sink["app_secret"] = feishu_app_secret
                    if feishu_space_id:
                        sink["space_id"] = feishu_space_id

        # 3. Validate and Return
        return cls(**config_data)

settings = AppSettings.load()
