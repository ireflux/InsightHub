import os
import sys
import tempfile
import unittest

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_DIR = os.path.join(ROOT_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from insighthub.settings import AppSettings


class TestSettingsSecurity(unittest.TestCase):
    def test_env_secrets_override_and_config_secrets_are_ignored(self):
        config_content = """
llm_provider:
  name: zhipuai
  api_key: insecure_config_key
  model: glm-4.7-flash
sinks:
  - name: feishu_doc
    app_id: insecure_app_id
    app_secret: insecure_app_secret
    default_title: InsightHub {date}
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
            self.assertEqual(settings.llm_provider.api_key, "env_zhipu_key")
            self.assertEqual(settings.sinks[0].app_id, "env_app_id")
            self.assertEqual(settings.sinks[0].app_secret, "env_app_secret")
        finally:
            os.remove(tmp_path)
            for key, value in old_env.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value

    def test_unsupported_provider_raises(self):
        config_content = """
llm_provider:
  name: bad_provider
  model: x
sources:
  - name: github_trending
sinks:
  - name: markdown_file
    output_dir: output
"""
        with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False, encoding="utf-8") as tmp:
            tmp.write(config_content)
            tmp_path = tmp.name
        try:
            with self.assertRaises(Exception):
                AppSettings.load(tmp_path)
        finally:
            os.remove(tmp_path)


if __name__ == "__main__":
    unittest.main()
