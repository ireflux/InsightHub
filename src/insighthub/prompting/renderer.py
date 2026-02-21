import os
from typing import Any, Dict, Optional

from insighthub.errors import PromptRenderingError


class PromptRenderer:
    """
    Compose final summarize prompt from:
    - structure template
    - style template
    """

    def __init__(
        self,
        prompts_dir: str = "prompts",
        structure_name: str = "professional_briefing_v1",
        style_name: str = "professional_neutral_v1",
        variables: Optional[Dict[str, Any]] = None,
    ):
        self.prompts_dir = prompts_dir
        self.structure_name = structure_name
        self.style_name = style_name
        self.variables = variables or {}

    def render_summarize_template(self) -> str:
        structure_path = os.path.join(self.prompts_dir, "structure", f"{self.structure_name}.md")
        style_path = os.path.join(self.prompts_dir, "style", f"{self.style_name}.md")

        structure_template = self._read_file(structure_path)
        style_template = self._read_file(style_path)

        try:
            style_guidelines = self._safe_format(style_template, self.variables)
            # Keep "{content}" unresolved at this stage;
            # provider.summarize will inject runtime content.
            merged = structure_template.replace("{style_guidelines}", style_guidelines)
            return self._safe_format(merged, {"content": "{content}", **self.variables})
        except Exception as e:
            raise PromptRenderingError(f"Failed to render prompt template: {e}") from e

    @staticmethod
    def _safe_format(template: str, values: Dict[str, Any]) -> str:
        class SafeDict(dict):
            def __missing__(self, key):
                return "{" + key + "}"

        return template.format_map(SafeDict(values))

    @staticmethod
    def _read_file(path: str) -> str:
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError as e:
            raise PromptRenderingError(f"Template file not found: {path}") from e
