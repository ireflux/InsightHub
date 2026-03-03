import os
import sys
import unittest

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_DIR = os.path.join(ROOT_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from insighthub.prompting import PromptRenderer


class TestPromptRenderer(unittest.TestCase):
    def test_render_professional_prompt_contains_paper_like_sections(self):
        renderer = PromptRenderer(
            prompts_dir="prompts",
            structure_name="professional_briefing_v1",
            style_name="professional_neutral_v1",
            variables={"min_items": 12},
        )

        template = renderer.render_summarize_template()

        self.assertIn("## 摘要（Abstract）", template)
        self.assertIn("## 方法与样本（Methodology）", template)
        self.assertIn("## 主要发现（Key Findings）", template)
        self.assertIn("## 深度分析（Analysis）", template)
        self.assertIn("至少输出 12 个分析小节", template)
        self.assertIn("不编造来源", template)
        self.assertIn("{content}", template)


if __name__ == "__main__":
    unittest.main()

