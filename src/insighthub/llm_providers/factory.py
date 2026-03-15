import inspect
from typing import Type, List
from insighthub.core.registry import registry
from insighthub.llm_providers.base import BaseLLMProvider

class LLMFactory:
    """
    Factory for creating LLM provider instances.
    Now delegates to the central registry.
    """
    
    @staticmethod
    def create_provider(provider_name: str, **kwargs) -> BaseLLMProvider:
        """
        Creates an instance of the specified LLM provider using the registry.
        """
        provider_types = registry.get_llm_types()
        provider_class = provider_types.get(provider_name.lower())
        if not provider_class:
            raise ValueError(f"Unsupported LLM provider: {provider_name}")

        # Dispatch only parameters supported by the provider constructor
        sig = inspect.signature(provider_class.__init__)
        accepted = {
            name
            for name, param in sig.parameters.items()
            if name != "self" and param.kind in (inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.KEYWORD_ONLY)
        }
        filtered_kwargs = {k: v for k, v in kwargs.items() if k in accepted}
        return provider_class(**filtered_kwargs)

    @staticmethod
    def get_available_providers() -> List[str]:
        """Returns a list of available provider names from the registry."""
        return list(registry.get_llm_types().keys())
