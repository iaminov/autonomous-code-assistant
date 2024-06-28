"""Abstract base class for LLM providers with comprehensive capabilities."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field

from ..exceptions import LLMProviderError


class ProviderCapability(Enum):
    """Enumeration of provider capabilities."""
    
    CODE_GENERATION = "code_generation"
    CODE_REVIEW = "code_review" 
    CODE_REFACTORING = "code_refactoring"
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    STREAMING = "streaming"
    FUNCTION_CALLING = "function_calling"
    VISION = "vision"


@dataclass
class CodeContext:
    """Container for code context information."""
    
    content: str
    filepath: str | None = None
    language: str | None = None
    line_start: int | None = None
    line_end: int | None = None
    dependencies: list[str] | None = None


class GenerationRequest(BaseModel):
    """Request object for code generation."""
    
    instruction: str = Field(..., description="The instruction for code generation")
    context: CodeContext | None = Field(None, description="Optional code context")
    max_tokens: int = Field(4096, description="Maximum tokens to generate")
    temperature: float = Field(0.2, description="Generation temperature")
    stop_sequences: list[str] = Field(default_factory=list, description="Stop sequences")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class GenerationResponse(BaseModel):
    """Response object for code generation."""
    
    content: str = Field(..., description="Generated content")
    tokens_used: int = Field(..., description="Number of tokens used")
    model: str = Field(..., description="Model used for generation")
    finish_reason: str = Field(..., description="Reason for completion")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class LLMProvider(ABC):
    """Abstract base class for LLM providers with comprehensive capabilities."""
    
    def __init__(self, model_name: str) -> None:
        self._model_name = model_name
        self._capabilities: set[ProviderCapability] = set()
    
    @property
    def model_name(self) -> str:
        """Get the current model name."""
        return self._model_name
    
    @property 
    def capabilities(self) -> set[ProviderCapability]:
        """Get the provider's capabilities."""
        return self._capabilities.copy()
    
    def supports_capability(self, capability: ProviderCapability) -> bool:
        """Check if the provider supports a specific capability."""
        return capability in self._capabilities
    
    @abstractmethod
    def generate_code(self, request: GenerationRequest) -> GenerationResponse:
        """
        Generate code based on the provided request.
        
        Args:
            request: The generation request containing instruction and context
            
        Returns:
            GenerationResponse with the generated content and metadata
            
        Raises:
            LLMProviderError: If generation fails
        """
        pass
    
    @abstractmethod
    def validate_request(self, request: GenerationRequest) -> None:
        """
        Validate a generation request.
        
        Args:
            request: The request to validate
            
        Raises:
            LLMProviderError: If the request is invalid
        """
        pass
    
    @abstractmethod 
    def estimate_tokens(self, text: str) -> int:
        """
        Estimate the number of tokens in the given text.
        
        Args:
            text: The text to estimate tokens for
            
        Returns:
            Estimated token count
        """
        pass
    
    @abstractmethod
    def check_health(self) -> bool:
        """
        Check if the provider is healthy and can handle requests.
        
        Returns:
            True if healthy, False otherwise
        """
        pass
    
    def get_provider_info(self) -> dict[str, Any]:
        """Get information about the provider."""
        return {
            "name": self.__class__.__name__,
            "model": self._model_name,
            "capabilities": [cap.value for cap in self._capabilities],
        }
