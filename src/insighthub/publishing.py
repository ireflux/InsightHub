from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo


@dataclass(frozen=True)
class TitlePolicy:
    template: str
    date_format: str
    timezone_name: str
    strip_leading_h1: bool = True

    def render(self, now: datetime, run_id: str | None = None) -> str:
        local_now = now.astimezone(ZoneInfo(self.timezone_name))
        date_text = local_now.strftime(self.date_format)
        values = {"date": date_text, "run_id": run_id or ""}
        try:
            return self.template.format(**values).strip()
        except Exception:
            return self.template.replace("{date}", date_text).replace("{run_id}", run_id or "").strip()

    def normalize_markdown(self, content: str) -> str:
        if not content:
            return content
        lines = content.splitlines()
        if self.strip_leading_h1:
            idx = 0
            while idx < len(lines) and not lines[idx].strip():
                idx += 1
            if idx < len(lines) and lines[idx].lstrip().startswith("# "):
                lines.pop(idx)
        while lines and not lines[0].strip():
            lines.pop(0)
        return "\n".join(lines).strip() + ("\n" if lines else "")

