import os
import sys
import tempfile

import pytest

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_DIR = os.path.join(ROOT_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from insighthub.settings import AppSettings


def test_env_secrets_override_and_config_secrets_are_ignored():
    config_content = """
llm:
  primary:
    provider: zhipuai
    api_key: insecure_config_key
    model: glm-4.7-flash
sinks:
  defaults:
    enabled: true
  items:
    - id: feishu
      type: feishu_doc
      params:
        app_id: insecure_app_id
        app_secret: insecure_app_secret
"""
    with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False, encoding="utf-8") as tmp:
        tmp.write(config_content)
        tmp_path = tmp.name

    old_env = {
        "ZHIPUAI_API_KEY": os.getenv("ZHIPUAI_API_KEY"),
        "FEISHU_APP_ID": os.getenv("FEISHU_APP_ID"),
        "FEISHU_APP_SECRET": os.getenv("FEISHU_APP_SECRET"),
    }
    os.environ["ZHIPUAI_API_KEY"] = "env_zhipu_key"
    os.environ["FEISHU_APP_ID"] = "env_app_id"
    os.environ["FEISHU_APP_SECRET"] = "env_app_secret"

    try:
        settings = AppSettings.load(tmp_path)
        assert settings.llm.primary.api_key == "env_zhipu_key"
        assert settings.sinks.items[0].params.get("app_id") == "env_app_id"
        assert settings.sinks.items[0].params.get("app_secret") == "env_app_secret"
    finally:
        os.remove(tmp_path)
        for key, value in old_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def test_unsupported_provider_raises():
    config_content = """
llm:
  primary:
    provider: bad_provider
    model: x
sources:
  items:
    - id: github
      type: github_trending
sinks:
  items:
    - id: markdown
      type: markdown_file
      params:
        output_dir: output
"""
    with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False, encoding="utf-8") as tmp:
        tmp.write(config_content)
        tmp_path = tmp.name
    try:
        with pytest.raises(Exception):
            AppSettings.load(tmp_path)
    finally:
        os.remove(tmp_path)


def test_legacy_scoring_threshold_is_ignored():
    config_content = """
llm:
  primary:
    provider: zhipuai
    model: glm-4.7-flash
sources:
  items:
    - id: github
      type: github_trending
sinks:
  items:
    - id: markdown
      type: markdown_file
      params:
        output_dir: output
scoring:
  min_comments_for_summary: -1
"""
    with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False, encoding="utf-8") as tmp:
        tmp.write(config_content)
        tmp_path = tmp.name
    try:
        settings = AppSettings.load(tmp_path)
        assert settings.scoring is not None
    finally:
        os.remove(tmp_path)


def test_invalid_retry_policy_raises():
    config_content = """
llm:
  primary:
    provider: zhipuai
    model: glm-4.7-flash
runtime:
  retry:
    source_fetch:
      max_attempts: 0
sources:
  items:
    - id: github
      type: github_trending
sinks:
  items:
    - id: markdown
      type: markdown_file
      params:
        output_dir: output
"""
    with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False, encoding="utf-8") as tmp:
        tmp.write(config_content)
        tmp_path = tmp.name
    try:
        with pytest.raises(Exception):
            AppSettings.load(tmp_path)
    finally:
        os.remove(tmp_path)


def test_invalid_observability_format_raises():
    config_content = """
llm:
  primary:
    provider: zhipuai
    model: glm-4.7-flash
runtime:
  observability:
    format: xml
sources:
  items:
    - id: github
      type: github_trending
sinks:
  items:
    - id: markdown
      type: markdown_file
      params:
        output_dir: output
"""
    with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False, encoding="utf-8") as tmp:
        tmp.write(config_content)
        tmp_path = tmp.name
    try:
        with pytest.raises(Exception):
            AppSettings.load(tmp_path)
    finally:
        os.remove(tmp_path)


def test_env_values_take_priority_over_config_for_model_and_feishu_ids():
    config_content = """
llm:
  primary:
    provider: zhipuai
    model: config-model
sinks:
  defaults:
    enabled: true
  items:
    - id: feishu
      type: feishu_doc
      params:
        app_id: insecure_app_id
        app_secret: insecure_app_secret
        space_id: config_space_id
        doc_id: config_doc_id
"""
    with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False, encoding="utf-8") as tmp:
        tmp.write(config_content)
        tmp_path = tmp.name

    old_env = {
        "LLM_MODEL": os.getenv("LLM_MODEL"),
        "FEISHU_APP_ID": os.getenv("FEISHU_APP_ID"),
        "FEISHU_APP_SECRET": os.getenv("FEISHU_APP_SECRET"),
        "FEISHU_SPACE_ID": os.getenv("FEISHU_SPACE_ID"),
        "FEISHU_DOC_ID": os.getenv("FEISHU_DOC_ID"),
    }
    os.environ["LLM_MODEL"] = "env-model"
    os.environ["FEISHU_APP_ID"] = "env_app_id"
    os.environ["FEISHU_APP_SECRET"] = "env_app_secret"
    os.environ["FEISHU_SPACE_ID"] = "env_space_id"
    os.environ["FEISHU_DOC_ID"] = "env_doc_id"

    try:
        settings = AppSettings.load(tmp_path)
        assert settings.llm.primary.model == "env-model"
        assert settings.sinks.items[0].params.get("space_id") == "env_space_id"
        assert settings.sinks.items[0].params.get("doc_id") == "env_doc_id"
    finally:
        os.remove(tmp_path)
        for key, value in old_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def test_env_base_url_takes_priority_over_config_for_custom_openai():
    config_content = """
llm:
  primary:
    provider: custom_openai
    model: config-model
    base_url: https://config.example.com/v1
"""
    with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False, encoding="utf-8") as tmp:
        tmp.write(config_content)
        tmp_path = tmp.name

    old_env = {
        "CUSTOM_OPENAI_API_KEY": os.getenv("CUSTOM_OPENAI_API_KEY"),
        "CUSTOM_OPENAI_BASE_URL": os.getenv("CUSTOM_OPENAI_BASE_URL"),
    }
    os.environ["CUSTOM_OPENAI_API_KEY"] = "env_custom_openai_key"
    os.environ["CUSTOM_OPENAI_BASE_URL"] = "https://env.example.com/v1"

    try:
        settings = AppSettings.load(tmp_path)
        assert settings.llm.primary.base_url == "https://env.example.com/v1"
    finally:
        os.remove(tmp_path)
        for key, value in old_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
