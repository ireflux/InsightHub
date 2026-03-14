import os
import datetime
import logging
import json
import re
import uuid
from typing import List, Optional
from zoneinfo import ZoneInfo
import aiofiles
from insighthub.publishing import TitlePolicy
from insighthub.sinks.base import BaseSink
from insighthub.models import NewsItem
from insighthub.observability import get_run_id

logger = logging.getLogger(__name__)

class MarkdownFileSink(BaseSink):
    """
    A sink that writes content to a local Markdown file.
    """
    
    def __init__(
        self,
        output_dir: str = "output",
        timezone_name: str = "Asia/Shanghai",
        title_policy: Optional[TitlePolicy] = None,
    ):
        self.output_dir = output_dir
        self.timezone_name = timezone_name
        self.title_policy = title_policy
        self.posts_dir = os.path.join(self.output_dir, "posts")
        self.manifest_dir = os.path.join(self.output_dir, "manifest")
        self.manifest_path = os.path.join(self.manifest_dir, "index.json")
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.posts_dir, exist_ok=True)
        os.makedirs(self.manifest_dir, exist_ok=True)
        self.name = "markdown_file"
        
    async def render(self, items: List[NewsItem], curated_content: Optional[str] = None):
        """
        Generates a Markdown file.
        """
        if not items and not curated_content:
            logger.info("MarkdownFileSink: Nothing to render.")
            return {"status": "skipped", "reason": "empty_input"}

        now = self._now_local()
        run_id = self._safe_run_id()
        date_str = now.strftime("%Y-%m-%d")
        slug = f"{date_str}-{run_id}"
        filename = f"{slug}.md"
        filepath = os.path.join(self.posts_dir, filename)
        
        if curated_content:
            content = curated_content
        else:
            content = self._format_as_feishu_markdown(items, now)
        content = self.title_policy.normalize_markdown(content)

        async with aiofiles.open(filepath, 'w', encoding='utf-8') as f:
            await f.write(content)

        self._update_manifest(
            items=items,
            content=content,
            now=now,
            run_id=run_id,
            slug=slug,
            markdown_rel_path=f"posts/{filename}",
        )

        logger.info(f"Successfully generated Markdown file: {filepath}")
        return {
            "status": "success",
            "file_path": filepath,
            "slug": slug,
            "manifest_path": self.manifest_path,
            "is_empty_update": len(items) == 0,
        }

    def _format_as_feishu_markdown(self, items: List[NewsItem], timestamp: datetime.datetime) -> str:
        """
        Fallback formatter if curated_content is not provided.
        """
        header = f"# InsightHub {timestamp.strftime('%Y-%m-%d')}\n\n"
        header += "> 闂?InsightHub 闂佺厧顨庢禍婊勬叏閳哄懏鍋ㄩ柣鏃傤焾閻忓洭鏌ｉ妸銉ヮ仹缂侇喗鐗犲顕€濡烽敃鈧灇闂佸搫鐗滈崹宕囪姳閸ф鐒诲璺虹墐閸嬫挻绌遍幖濉"
        
        body = []
        for i, item in enumerate(items):
            title = item.title
            url = item.url
            summary = item.summary or 'No summary available.'
            
            item_str = f"## {i+1}. **[{title}]({url})**\n\n"
            formatted_summary = summary.replace('\n', '\n> ')
            house_blockquote = f"> {formatted_summary}\n"
            body.append(item_str + house_blockquote)
            
        return header + "\n---\n\n".join(body)

    def _now_local(self) -> datetime.datetime:
        return datetime.datetime.now(ZoneInfo(self.timezone_name))

    def _safe_run_id(self) -> str:
        run_id = (get_run_id() or "").strip()
        if not run_id or run_id == "-":
            run_id = uuid.uuid4().hex[:12]
        return re.sub(r"[^a-zA-Z0-9_-]", "", run_id)

    def _update_manifest(
        self,
        *,
        items: List[NewsItem],
        content: str,
        now: datetime.datetime,
        run_id: str,
        slug: str,
        markdown_rel_path: str,
    ) -> None:
        manifest = self._load_manifest()
        post = {
            "id": slug,
            "run_id": run_id,
            "date": now.strftime("%Y-%m-%d"),
            "title": self.title_policy.render(now, run_id=run_id),
            "slug": slug,
            "markdown_path": markdown_rel_path,
            "summary": self._extract_summary(content),
            "tags": self._extract_tags(items),
            "sources": sorted({item.source for item in items if item.source}),
            "item_count": len(items),
            "is_empty_update": len(items) == 0,
            "created_at": now.isoformat(),
        }

        posts = [p for p in manifest.get("posts", []) if p.get("slug") != slug]
        posts.append(post)
        posts.sort(key=lambda p: p.get("created_at", ""), reverse=True)

        manifest["site_timezone"] = self.timezone_name
        manifest["generated_at"] = now.isoformat()
        manifest["posts"] = posts

        with open(self.manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)

    def _load_manifest(self) -> dict:
        if not os.path.exists(self.manifest_path):
            return {"site_timezone": self.timezone_name, "generated_at": None, "posts": []}
        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                data.setdefault("site_timezone", self.timezone_name)
                data.setdefault("generated_at", None)
                data.setdefault("posts", [])
                return data
        except Exception:
            logger.warning("MarkdownFileSink: Failed to load manifest, rebuilding from scratch.")
        return {"site_timezone": self.timezone_name, "generated_at": None, "posts": []}

    def _extract_title(self, content: str, now: datetime.datetime) -> str:
        for line in content.splitlines():
            stripped = line.strip()
            if stripped.startswith("#"):
                return stripped.lstrip("#").strip()
        return self.title_policy.render(now)

    def _extract_summary(self, content: str) -> str:
        for line in content.splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith("#") and not stripped.startswith(">"):
                return stripped[:200]
        return ""

    def _extract_tags(self, items: List[NewsItem]) -> List[str]:
        tags = set()
        for item in items:
            if not item.source:
                continue
            slug = re.sub(r"[^a-z0-9]+", "_", item.source.lower()).strip("_")
            if slug:
                tags.add(slug)
        return sorted(tags)
