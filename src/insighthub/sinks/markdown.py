import os
import datetime
import logging
from typing import List, Optional
import aiofiles
from insighthub.sinks.base import BaseSink
from insighthub.models import NewsItem

logger = logging.getLogger(__name__)

class MarkdownFileSink(BaseSink):
    """
    A sink that writes content to a local Markdown file.
    """
    
    def __init__(self, output_dir: str = "output"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.name = "markdown_file"
        
    async def render(self, items: List[NewsItem], curated_content: Optional[str] = None):
        """
        Generates a Markdown file.
        """
        if not items and not curated_content:
            logger.info("MarkdownFileSink: Nothing to render.")
            return {"status": "skipped", "reason": "empty_input"}
            
        now = datetime.datetime.now()
        filename = f"InsightHub_{now.strftime('%Y-%m-%d_%H-%M')}.md"
        filepath = os.path.join(self.output_dir, filename)
        
        if curated_content:
            # Use curated content as-is to avoid forcing a title into article body.
            content = curated_content
        else:
            content = self._format_as_feishu_markdown(items, now)
        
        async with aiofiles.open(filepath, 'w', encoding='utf-8') as f:
            await f.write(content)
            
        logger.info(f"Successfully generated Markdown file: {filepath}")
        return {"status": "success", "file_path": filepath}

    def _format_as_feishu_markdown(self, items: List[NewsItem], timestamp: datetime.datetime) -> str:
        """
        Fallback formatter if curated_content is not provided.
        """
        header = f"# InsightHub {timestamp.strftime('%Y-%m-%d')}\n\n"
        header += "> 由 InsightHub 自动生成的今日技术精选。\n\n"
        
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
