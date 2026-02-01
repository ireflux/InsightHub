import httpx
import logging
import re
from datetime import datetime
from typing import List, Dict, Optional, Any
from insighthub.sinks.base import BaseSink
from insighthub.models import NewsItem

logger = logging.getLogger(__name__)

class FeishuDocSink(BaseSink):
    """
    Sink that creates or updates a Feishu Cloud Document.
    Optimized to parse curated Markdown content into Doc blocks.
    """

    AUTH_URL = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    DOC_CREATE_URL = "https://open.feishu.cn/open-apis/docx/v1/documents"
    WIKI_NODE_CREATE_URL_TEMPLATE = "https://open.feishu.cn/open-apis/wiki/v2/spaces/{space_id}/nodes"
    BLOCK_CHILDREN_CREATE_URL_TEMPLATE = "https://open.feishu.cn/open-apis/docx/v1/documents/{document_id}/blocks/{block_id}/children"

    def __init__(self, app_id: str, app_secret: str, default_title: Optional[str] = None, space_id: Optional[str] = None):
        if not app_id or not app_secret:
            raise ValueError("Feishu app_id and app_secret are required for FeishuDocSink")
        self.app_id = app_id
        self.app_secret = app_secret
        self.default_title = default_title or "InsightHub Summary"
        self.space_id = space_id

    async def _get_tenant_access_token(self) -> str:
        async with httpx.AsyncClient() as client:
            resp = await client.post(self.AUTH_URL, json={"app_id": self.app_id, "app_secret": self.app_secret})
            resp.raise_for_status()
            data = resp.json()
            token = data.get("tenant_access_token") or data.get("data", {}).get("tenant_access_token")
            if not token:
                raise RuntimeError(f"Failed to obtain tenant_access_token: {data}")
            return token

    def _make_text_block(self, content: str, elements: Optional[List[Dict]] = None) -> Dict:
        """Helper to create a Text Block structure."""
        if elements:
            return {"block_type": 2, "text": {"elements": elements}}
        
        return {
            "block_type": 2,
            "text": {
                "elements": [{"text_run": {"content": content}}]
            }
        }

    def _make_heading_block(self, content: str, level: int) -> Dict:
        """Helper to create a Heading Block (level 1-9)."""
        block_type = 2 + level
        key = f"heading{level}"
        return {
            "block_type": block_type,
            key: {
                "elements": [{"text_run": {"content": content}}]
            }
        }

    def _parse_markdown_to_blocks(self, markdown: str) -> List[Dict]:
        """
        Simple parser to convert Markdown lines into Feishu blocks.
        Supports:
        - ## Headings (converted to Heading 2)
        - [Title](URL): Summary (converted to Text block with link)
        - Plain text
        """
        blocks = []
        lines = markdown.split("\n")
        
        for line in lines:
            line = line.strip()
            if not line:
                # Add empty block for spacing if needed, but usually skip
                continue
            
            # Match ## Heading
            if line.startswith("##"):
                content = line.replace("##", "").strip()
                blocks.append(self._make_heading_block(content, 2))
                continue
            
            # Match [Title](URL): Summary
            # Regex: \[([^\]]+)\]\(([^)]+)\):?\s*(.*)
            link_match = re.match(r"\[([^\]]+)\]\(([^)]+)\):?\s*(.*)", line)
            if link_match:
                title, url, summary = link_match.groups()
                elements = [
                    {
                        "text_run": {
                            "content": title,
                            "text_element_style": {"link": {"url": url}, "bold": True}
                        }
                    }
                ]
                if summary:
                    elements.append({"text_run": {"content": f": {summary}"}})
                
                blocks.append(self._make_text_block("", elements=elements))
                continue
            
            # Plain text
            blocks.append(self._make_text_block(line))
            
        return blocks

    async def render(self, items: List[NewsItem], curated_content: Optional[str] = None):
        if not items and not curated_content:
            logger.info("FeishuDocSink: Nothing to render.")
            return

        token = await self._get_tenant_access_token()
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json; charset=utf-8"}

        async with httpx.AsyncClient() as client:
            try:
                document_id = None
                if self.space_id:
                    wiki_url = self.WIKI_NODE_CREATE_URL_TEMPLATE.format(space_id=self.space_id)
                    create_body = {"obj_type": "docx", "node_type": "origin", "title": self.default_title}
                    create_resp = await client.post(wiki_url, json=create_body, headers=headers)
                    create_resp.raise_for_status()
                    create_data = create_resp.json()
                    document_id = create_data.get("data", {}).get("node", {}).get("obj_token")
                else:
                    create_body = {"title": self.default_title} 
                    create_resp = await client.post(self.DOC_CREATE_URL, json=create_body, headers=headers)
                    create_resp.raise_for_status()
                    create_data = create_resp.json()
                    document_id = create_data.get("data", {}).get("document", {}).get("document_id")

                if not document_id:
                    logger.error("Failed to determine document_id.")
                    return

                logger.info(f"FeishuDocSink: Document {document_id} created. Inserting content...")

                # Parse content
                if curated_content:
                    # Add top level title
                    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    initial_blocks = [self._make_heading_block(f"InsightHub 周刊 {now}", 1)]
                    content_blocks = self._parse_markdown_to_blocks(curated_content)
                    all_blocks = initial_blocks + content_blocks
                else:
                    # Legacy fallback
                    all_blocks = [self._make_text_block("No curated content provided.")]

                # Send in batches
                BATCH_SIZE = 50
                create_children_url = self.BLOCK_CHILDREN_CREATE_URL_TEMPLATE.format(
                    document_id=document_id, block_id=document_id
                )

                for i in range(0, len(all_blocks), BATCH_SIZE):
                    batch = all_blocks[i : i + BATCH_SIZE]
                    payload = {"children": batch, "index": -1}
                    resp = await client.post(create_children_url, json=payload, headers=headers)
                    resp.raise_for_status()

                logger.info(f"FeishuDocSink: Successfully rendered document {document_id}")

            except Exception as e:
                logger.error(f"Error in FeishuDocSink: {e}", exc_info=True)
