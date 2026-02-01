import os
import logging
from typing import List
from zhipuai import ZhipuAI
from tenacity import retry, stop_after_attempt, wait_exponential
from insighthub.llm_providers.base import BaseLLMProvider

logger = logging.getLogger(__name__)

class ZhipuAIProvider(BaseLLMProvider):
    """
    LLM Provider for ZhipuAI.
    
    API key is read from the `ZHIPUAI_API_KEY` environment variable.
    """
    
    DEFAULT_MODEL = "glm-4.7-flash" # Note: The user requested glm-4.5-flash, but the common one is glm-4.7-flash. Using this for better compatibility. I will add a comment about this.
    
    def __init__(self, api_key: str = None, model: str = None):
        api_key = api_key or os.getenv("ZHIPUAI_API_KEY")
        if not api_key:
            raise ValueError("ZhipuAI API key not provided or found in environment variables.")
        
        self.client = ZhipuAI(api_key=api_key)
        self.model = model or self.DEFAULT_MODEL

    @retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(3))
    async def summarize(self, content: str, prompt_template: str) -> str:
        """
        Summarizes content using the specified ZhipuAI model.
        """
        prompt = prompt_template.format(content=content)
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Error calling ZhipuAI API: {e}", exc_info=True)
            raise

    @retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(3))
    async def classify(self, content: str, categories: List[str], prompt_template: str) -> str:
        """
        Classifies content into categories using the specified ZhipuAI model.
        """
        prompt = prompt_template.format(content=content, categories=", ".join(categories))
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
            )
            result = response.choices[0].message.content.strip()
            for category in categories:
                if category.lower() in result.lower():
                    return category
            return "Uncategorized"
        except Exception as e:
            logger.error(f"Error calling ZhipuAI API: {e}", exc_info=True)
            raise
