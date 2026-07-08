from abc import ABC, abstractmethod


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
    async def score(self, content: str, prompt_template: str) -> str:
        """
        Scores the content and returns a JSON string with quality assessment.

        Args:
            content: The text content to be scored.
            prompt_template: The template for the prompt with placeholders.

        Returns:
            A JSON string containing quality_score (0-10), include (bool), and reason (str).
        """
        pass

    async def aclose(self) -> None:
        """Optional cleanup hook for providers with network clients."""
        return None

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
