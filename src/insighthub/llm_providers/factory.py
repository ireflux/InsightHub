import inspect
from typing import Type
from insighthub.llm_providers.base import BaseLLMProvider
from insighthub.llm_providers.custom import CustomAnthropicProvider, CustomOpenAIProvider
from insighthub.llm_providers.openrouter import OpenRouterProvider
from insighthub.llm_providers.nvidia import NvidiaProvider
from insighthub.llm_providers.zhipu import ZhipuAIProvider

class LLMFactory:
    """
    Factory for creating LLM provider instances.
    """
    
    _providers = {
        "openrouter": OpenRouterProvider,
        "nvidia": NvidiaProvider,
        "zhipuai": ZhipuAIProvider,
        "custom_openai": CustomOpenAIProvider,
        "custom_anthropic": CustomAnthropicProvider,
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
        # Keep workflow_factory simple: pass a superset of kwargs and
        # dispatch only the parameters supported by each provider constructor.
        sig = inspect.signature(provider_class.__init__)
        accepted = {
            name
            for name, param in sig.parameters.items()
            if name != "self" and param.kind in (inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.KEYWORD_ONLY)
        }
        filtered_kwargs = {k: v for k, v in kwargs.items() if k in accepted}
        return provider_class(**filtered_kwargs)

    @staticmethod
    def get_available_providers() -> list[str]:
        """Returns a list of available provider names."""
        return list(LLMFactory._providers.keys())
