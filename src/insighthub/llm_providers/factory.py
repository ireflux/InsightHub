from typing import Type
from insighthub.llm_providers.base import BaseLLMProvider
from insighthub.llm_providers.openrouter import OpenRouterProvider
from insighthub.llm_providers.zhipu import ZhipuAIProvider

class LLMFactory:
    """
    Factory for creating LLM provider instances.
    """
    
    _providers = {
        "openrouter": OpenRouterProvider,
        "zhipuai": ZhipuAIProvider,
    }

    @staticmethod
    def create_provider(provider_name: str, **kwargs) -> BaseLLMProvider:
        """
        Creates an instance of the specified LLM provider.

        Args:
            provider_name: The name of the provider to create (e.g., 'openrouter').
            **kwargs: Arguments to pass to the provider's constructor (e.g., api_key, model).

        Returns:
            An instance of the LLM provider.
            
        Raises:
            ValueError: If the provider name is not supported.
        """
        provider_class = LLMFactory._providers.get(provider_name.lower())
        if not provider_class:
            raise ValueError(f"Unsupported LLM provider: {provider_name}")
        return provider_class(**kwargs)

    @staticmethod
    def get_available_providers() -> list[str]:
        """Returns a list of available provider names."""
        return list(LLMFactory._providers.keys())
