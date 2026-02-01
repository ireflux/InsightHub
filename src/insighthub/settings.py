import os
import yaml
import logging
from typing import List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

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
        
        # 2. Process Environment Variable Fallbacks (Config File > Environment Variables)
        
        # LLM Provider setup
        if "llm_provider" not in config_data:
            config_data["llm_provider"] = {"name": "zhipuai", "model": "glm-4.7-flash"} # default
            
        provider_config = config_data["llm_provider"]
        provider_name = provider_config.get("name")
        
        # LLM API Keys fallback
        if not provider_config.get("api_key"):
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

        # Feishu Credentials fallback (scanning sinks)
        if "sinks" in config_data:
            for sink in config_data["sinks"]:
                if sink.get("name") == "feishu_doc":
                    # Priority: config_data > environment variable
                    sink["app_id"] = sink.get("app_id") or os.getenv("FEISHU_APP_ID")
                    sink["app_secret"] = sink.get("app_secret") or os.getenv("FEISHU_APP_SECRET")
                    sink["space_id"] = sink.get("space_id") or os.getenv("FEISHU_SPACE_ID")

        # 3. Validate and Return
        return cls(**config_data)

settings = AppSettings.load()
