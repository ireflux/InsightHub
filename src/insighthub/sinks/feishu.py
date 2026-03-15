import httpx
import logging
from datetime import datetime
from typing import List, Optional
from insighthub.core.registry import registry
from insighthub.errors import SinkDeliveryError
from insighthub.publishing import TitlePolicy
from insighthub.sinks.base import BaseSink
from insighthub.models import NewsItem

logger = logging.getLogger(__name__)

@registry.register_sink("feishu_doc")
class FeishuDocSink(BaseSink):
    """
    Sink that creates or updates a Feishu Cloud Document.
    Optimized to parse curated Markdown content into Doc blocks.
    """

    AUTH_URL = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    DOC_CREATE_URL = "https://open.feishu.cn/open-apis/docx/v1/documents"
    WIKI_NODE_CREATE_URL_TEMPLATE = "https://open.feishu.cn/open-apis/wiki/v2/spaces/{space_id}/nodes"
    BLOCK_CHILDREN_CREATE_URL_TEMPLATE = "https://open.feishu.cn/open-apis/docx/v1/documents/{document_id}/blocks/{block_id}/children"
    BLOCK_CONVERT_URL = "https://open.feishu.cn/open-apis/docx/v1/documents/blocks/convert"
    BLOCK_DESCENDANT_CREATE_URL_TEMPLATE = "https://open.feishu.cn/open-apis/docx/v1/documents/{document_id}/blocks/{block_id}/descendant"

    def __init__(
        self,
        app_id: str,
        app_secret: str,
        title_policy: Optional[TitlePolicy] = None,
        space_id: Optional[str] = None,
        doc_id: Optional[str] = None,
    ):
        if not app_id or not app_secret:
            raise ValueError("Feishu app_id and app_secret are required for FeishuDocSink")
        self.app_id = app_id
        self.app_secret = app_secret
        self.title_policy = title_policy
        self.space_id = space_id
        self.doc_id = doc_id
        self.name = "feishu_doc"

    async def _get_tenant_access_token(self) -> str:
        async with httpx.AsyncClient() as client:
            resp = await client.post(self.AUTH_URL, json={"app_id": self.app_id, "app_secret": self.app_secret})
            resp.raise_for_status()
            data = resp.json()
            token = data.get("tenant_access_token") or data.get("data", {}).get("tenant_access_token")
            if not token:
                raise RuntimeError(f"Failed to obtain tenant_access_token: {data}")
            return token

    async def render(self, items: List[NewsItem], curated_content: Optional[str] = None):
        if not items and not curated_content:
            logger.info("FeishuDocSink: Nothing to render.")
            return {"status": "skipped", "reason": "empty_input"}

        token = await self._get_tenant_access_token()
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json; charset=utf-8"}

        now = datetime.now()
        doc_title = self.title_policy.render(now)

        async with httpx.AsyncClient() as client:
            try:
                if self.doc_id:
                    document_id = self.doc_id
                    logger.info(f"FeishuDocSink: Updating existing document {document_id}.")
                elif self.space_id:
                    wiki_url = self.WIKI_NODE_CREATE_URL_TEMPLATE.format(space_id=self.space_id)
                    create_body = {"obj_type": "docx", "node_type": "origin", "title": doc_title}
                    create_resp = await client.post(wiki_url, json=create_body, headers=headers)
                    create_resp.raise_for_status()
                    document_id = create_resp.json().get("data", {}).get("node", {}).get("obj_token")
                else:
                    create_body = {"title": doc_title} 
                    create_resp = await client.post(self.DOC_CREATE_URL, json=create_body, headers=headers)
                    create_resp.raise_for_status()
                    document_id = create_resp.json().get("data", {}).get("document", {}).get("document_id")

                if not document_id:
                    raise SinkDeliveryError("Failed to determine document_id.")

                logger.info(f"FeishuDocSink: Converting content for document {document_id}...")

                # 1. Convert Markdown to Blocks
                content = curated_content or "No curated content provided."
                if self.doc_id:
                    # Append a dated section when updating an existing doc.
                    section_title = self.title_policy.render(now)
                    full_markdown = f"## {section_title}\n\n{content}"
                else:
                    # For new docs, use content as-is (doc title is already set in Feishu metadata).
                    full_markdown = content
                
                convert_resp = await client.post(
                    self.BLOCK_CONVERT_URL, 
                    json={"content_type": "markdown", "content": full_markdown}, 
                    headers=headers
                )
                convert_resp.raise_for_status()
                convert_data = convert_resp.json().get("data", {})
                
                blocks = convert_data.get("blocks", [])
                first_level_block_ids = convert_data.get("first_level_block_ids", [])

                if not blocks or not first_level_block_ids:
                    logger.warning("No blocks converted from Markdown.")
                    return

                # 2. Clean blocks (remove merge_info from tables as it's read-only)
                for block in blocks:
                    if block.get("block_type") == 31:  # Table
                        table_data = block.get("table", {})
                        if "property" in table_data and "merge_info" in table_data["property"]:
                            del table_data["property"]["merge_info"]

                # 3. Insert blocks into document
                descendant_url = f"{self.BLOCK_DESCENDANT_CREATE_URL_TEMPLATE.format(document_id=document_id, block_id=document_id)}?document_revision_id=-1"
                
                # Batching: descendant API supports up to 1000 blocks in 'descendants' list.
                if len(blocks) <= 1000:
                    payload = {
                        "children_id": first_level_block_ids,
                        "descendants": blocks,
                        "index": -1
                    }
                    resp = await client.post(descendant_url, json=payload, headers=headers)
                    resp.raise_for_status()
                else:
                    # Batching logic: group first-level blocks and their descendants
                    block_map = {b["block_id"]: b for b in blocks}
                    
                    def get_subtree(block_id, subtree_list):
                        block = block_map.get(block_id)
                        if not block: return
                        subtree_list.append(block)
                        for child_id in block.get("children", []):
                            get_subtree(child_id, subtree_list)

                    current_batch_children = []
                    current_batch_descendants = []
                    
                    for fl_id in first_level_block_ids:
                        subtree = []
                        get_subtree(fl_id, subtree)
                        
                        if len(current_batch_descendants) + len(subtree) > 1000:
                            if current_batch_children:
                                payload = {
                                    "children_id": current_batch_children,
                                    "descendants": current_batch_descendants,
                                    "index": -1
                                }
                                resp = await client.post(descendant_url, json=payload, headers=headers)
                                resp.raise_for_status()
                            
                            current_batch_children = [fl_id]
                            current_batch_descendants = subtree
                        else:
                            current_batch_children.append(fl_id)
                            current_batch_descendants.extend(subtree)
                    
                    if current_batch_children:
                        payload = {
                            "children_id": current_batch_children,
                            "descendants": current_batch_descendants,
                            "index": -1
                        }
                        resp = await client.post(descendant_url, json=payload, headers=headers)
                        resp.raise_for_status()

                logger.info(f"FeishuDocSink: Successfully rendered document {document_id}")
                return {"status": "success", "document_id": document_id}

            except Exception as e:
                logger.error(f"Error in FeishuDocSink: {e}", exc_info=True)
                raise SinkDeliveryError(f"Feishu sink delivery failed: {e}") from e
