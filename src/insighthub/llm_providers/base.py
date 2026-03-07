from abc import ABC, abstractmethod
from typing import List

class BaseLLMProvider(ABC):
    """
    Abstract base class for all LLM providers (e.g., OpenRouter, ZhipuAI),
    following the Strategy Pattern.

    This ensures that the core logic can easily switch between different
    LLM providers without changing the main workflow.
    """

    @abstractmethod
    async def summarize(self, content: str, prompt_template: str) -> str:
        """
        Summarizes the given content using a specific prompt template.

        Args:
            content: The text content to be summarized.
            prompt_template: The template for the prompt with a placeholder for content.

        Returns:
            The summarized text.
        """
        pass

    @abstractmethod
    async def classify(self, content: str, categories: List[str], prompt_template: str) -> str:
        """
        Classifies the content into one of the given categories.

        Args:
            content: The text content to be classified.
            categories: A list of possible categories.
            prompt_template: The template for the prompt with placeholders.

        Returns:
            The most likely category from the list.
        """
        pass

    @staticmethod
    def render_prompt(prompt_template: str, **values: str) -> str:
        """
        Safely render prompt templates with known variables while keeping unknown
        placeholders untouched.
        """

        class SafeDict(dict):
            def __missing__(self, key):
                return "{" + key + "}"

        return prompt_template.format_map(SafeDict(values))
