import os
import sys
import unittest

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_DIR = os.path.join(ROOT_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from insighthub.prompting import PromptRenderer


class TestPromptRenderer(unittest.TestCase):
    def test_render_media_style_v3_prompt(self):
        renderer = PromptRenderer(
            prompts_dir="prompts",
            structure_name="professional_briefing_v3",
            style_name="professional_neutral_v3",
            variables={},
        )

        template = renderer.render_summarize_template()
        self.assertIn("## 今天发生了什么", template)
        self.assertIn("## 核心判断", template)
        self.assertIn("## 重点解读", template)
        self.assertIn("输出 4-6 个小节", template)
        self.assertIn("媒体化写作要求", template)
        self.assertIn("{content}", template)
        self.assertNotIn("{min_items}", template)


if __name__ == "__main__":
    unittest.main()

