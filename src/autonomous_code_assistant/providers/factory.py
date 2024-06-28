"""Factory for creating LLM providers."""

from typing import Any

from .base import LLMProvider
from .openai import OpenAIProvider
from ..exceptions import LLMProviderError


class ProviderFactory:
    """Factory class for creating LLM providers."""
    
    _providers: dict[str, type[LLMProvider]] = {
        "openai": OpenAIProvider,
    }
    
    @classmethod
    def create_provider(
        self, 
        provider_name: str, 
        **kwargs: Any
    ) -> LLMProvider:
        """
        Create a provider instance by name.
        
        Args:
            provider_name: Name of the provider to create
            **kwargs: Arguments to pass to the provider constructor
            
        Returns:
            Configured provider instance
            
        Raises:
            LLMProviderError: If provider is not supported
        """
        provider_class = self._providers.get(provider_name.lower())
        
        if not provider_class:
            raise LLMProviderError(
                f"Unsupported provider: {provider_name}. "
                f"Available providers: {list(self._providers.keys())}"
            )
        
        try:
            return provider_class(**kwargs)
        except Exception as e:
            raise LLMProviderError(
                f"Failed to create {provider_name} provider: {str(e)}",
                provider=provider_name,
                original_error=e
            )
    
    @classmethod
    def register_provider(
        cls, 
        name: str, 
        provider_class: type[LLMProvider]
    ) -> None:
        """
        Register a new provider class.
        
        Args:
            name: Name to register the provider under
            provider_class: Provider class to register
        """
        if not issubclass(provider_class, LLMProvider):
            raise LLMProviderError(
                f"Provider class must inherit from LLMProvider, got {provider_class}"
            )
        
        cls._providers[name.lower()] = provider_class
    
    @classmethod
    def get_available_providers(cls) -> list[str]:
        """Get list of available provider names."""
        return list(cls._providers.keys())
    
    @classmethod
    def is_provider_available(cls, provider_name: str) -> bool:
        """Check if a provider is available."""
        return provider_name.lower() in cls._providers
