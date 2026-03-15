import logging
from typing import Dict, Type, Any, Callable, TypeVar

T = TypeVar("T")

logger = logging.getLogger(__name__)

class ComponentRegistry:
    """
    Generic registry for InsightHub components (Sources, Sinks, LLM Providers).
    """
    def __init__(self):
        self._sources: Dict[str, Type] = {}
        self._sinks: Dict[str, Type] = {}
        self._llms: Dict[str, Type] = {}

    def register_source(self, name: str) -> Callable[[Type[T]], Type[T]]:
        def decorator(cls: Type[T]) -> Type[T]:
            self._sources[name] = cls
            return cls
        return decorator

    def register_sink(self, name: str) -> Callable[[Type[T]], Type[T]]:
        def decorator(cls: Type[T]) -> Type[T]:
            self._sinks[name] = cls
            return cls
        return decorator

    def register_llm(self, name: str) -> Callable[[Type[T]], Type[T]]:
        def decorator(cls: Type[T]) -> Type[T]:
            self._llms[name] = cls
            return cls
        return decorator

    def get_source_types(self) -> Dict[str, Type]:
        return self._sources

    def get_sink_types(self) -> Dict[str, Type]:
        return self._sinks

    def get_llm_types(self) -> Dict[str, Type]:
        return self._llms

    def create_source(self, name: str, **kwargs) -> Any:
        key = name.lower()
        cls = self._sources.get(key)
        if not cls:
            raise ValueError(f"Source type '{name}' not registered.")
        return cls(**kwargs)

    def create_sink(self, name: str, **kwargs) -> Any:
        key = name.lower()
        cls = self._sinks.get(key)
        if not cls:
            raise ValueError(f"Sink type '{name}' not registered.")
        return cls(**kwargs)

    def create_llm(self, name: str, **kwargs) -> Any:
        key = name.lower()
        cls = self._llms.get(key)
        if not cls:
            raise ValueError(f"LLM provider '{name}' not registered.")
        return cls(**kwargs)

registry = ComponentRegistry()
