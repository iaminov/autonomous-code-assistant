"""OpenAI provider implementation with advanced features and error handling."""

import re
import os
from typing import Any

from openai import OpenAI
from openai.types.chat import ChatCompletion

from .base import (
    LLMProvider, 
    ProviderCapability, 
    GenerationRequest, 
    GenerationResponse,
    CodeContext,
)
from ..exceptions import LLMProviderError


class OpenAIProvider(LLMProvider):
    """OpenAI provider implementation with comprehensive capabilities."""
    
    # Token estimation multiplier (rough approximation for GPT models)
    CHARS_PER_TOKEN = 4
    
    # Supported models and their capabilities
    MODEL_CAPABILITIES = {
        "gpt-4": {
            ProviderCapability.CODE_GENERATION,
            ProviderCapability.CODE_REVIEW,
            ProviderCapability.CODE_REFACTORING,
            ProviderCapability.DOCUMENTATION,
            ProviderCapability.TESTING,
            ProviderCapability.FUNCTION_CALLING,
        },
        "gpt-4-turbo": {
            ProviderCapability.CODE_GENERATION,
            ProviderCapability.CODE_REVIEW,
            ProviderCapability.CODE_REFACTORING,
            ProviderCapability.DOCUMENTATION,
            ProviderCapability.TESTING,
            ProviderCapability.FUNCTION_CALLING,
            ProviderCapability.VISION,
        },
        "gpt-4-turbo-preview": {
            ProviderCapability.CODE_GENERATION,
            ProviderCapability.CODE_REVIEW,
            ProviderCapability.CODE_REFACTORING,
            ProviderCapability.DOCUMENTATION,
            ProviderCapability.TESTING,
            ProviderCapability.FUNCTION_CALLING,
        },
        "gpt-3.5-turbo": {
            ProviderCapability.CODE_GENERATION,
            ProviderCapability.CODE_REVIEW,
            ProviderCapability.DOCUMENTATION,
            ProviderCapability.FUNCTION_CALLING,
        },
    }
    
    def __init__(self, api_key: str | None = None, model: str = "gpt-4-turbo-preview") -> None:
        super().__init__(model)
        
        # Get API key from parameter or environment
        self._api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self._api_key:
            raise LLMProviderError(
                "OpenAI API key is required. Set OPENAI_API_KEY environment variable or pass api_key parameter.",
                provider="OpenAI"
            )
        
        try:
            self._client = OpenAI(api_key=self._api_key)
        except Exception as e:
            raise LLMProviderError(
                f"Failed to initialize OpenAI client: {str(e)}",
                provider="OpenAI",
                original_error=e
            )
        
        # Set capabilities based on model
        self._capabilities = self.MODEL_CAPABILITIES.get(model, set())
        
        # Validate model exists
        if not self._capabilities:
            raise LLMProviderError(
                f"Unsupported model: {model}. Supported models: {list(self.MODEL_CAPABILITIES.keys())}",
                provider="OpenAI",
                model=model
            )
    
    def generate_code(self, request: GenerationRequest) -> GenerationResponse:
        """Generate code using OpenAI's chat completion API."""
        self.validate_request(request)
        
        try:
            messages = self._build_messages(request)
            
            response: ChatCompletion = self._client.chat.completions.create(
                model=self._model_name,
                messages=messages,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                stop=request.stop_sequences or None,
            )
            
            choice = response.choices[0]
            usage = response.usage
            
            return GenerationResponse(
                content=choice.message.content or "",
                tokens_used=usage.total_tokens if usage else 0,
                model=response.model,
                finish_reason=choice.finish_reason or "unknown",
                metadata={
                    "prompt_tokens": usage.prompt_tokens if usage else 0,
                    "completion_tokens": usage.completion_tokens if usage else 0,
                    "response_id": response.id,
                }
            )
            
        except Exception as e:
            raise LLMProviderError(
                f"Code generation failed: {str(e)}",
                provider="OpenAI",
                model=self._model_name,
                original_error=e
            )
    
    def validate_request(self, request: GenerationRequest) -> None:
        """Validate a generation request for OpenAI compatibility."""
        if not request.instruction.strip():
            raise LLMProviderError(
                "Instruction cannot be empty",
                provider="OpenAI"
            )
        
        if request.max_tokens <= 0:
            raise LLMProviderError(
                "max_tokens must be positive",
                provider="OpenAI"
            )
        
        if not 0.0 <= request.temperature <= 2.0:
            raise LLMProviderError(
                "temperature must be between 0.0 and 2.0",
                provider="OpenAI"
            )
        
        # Estimate token usage to prevent exceeding limits
        estimated_tokens = self._estimate_request_tokens(request)
        model_limit = self._get_model_token_limit()
        
        if estimated_tokens > model_limit:
            raise LLMProviderError(
                f"Estimated request tokens ({estimated_tokens}) exceed model limit ({model_limit})",
                provider="OpenAI",
                model=self._model_name
            )
    
    def estimate_tokens(self, text: str) -> int:
        """Estimate token count using character-based approximation."""
        return max(1, len(text) // self.CHARS_PER_TOKEN)
    
    def check_health(self) -> bool:
        """Check if the OpenAI API is accessible."""
        try:
            # Make a minimal request to test connectivity
            self._client.chat.completions.create(
                model=self._model_name,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=1,
            )
            return True
        except Exception:
            return False
    
    def _build_messages(self, request: GenerationRequest) -> list[dict[str, str]]:
        """Build messages array for OpenAI chat completion."""
        messages = [
            {
                "role": "system",
                "content": self._build_system_prompt(request.context)
            },
            {
                "role": "user", 
                "content": request.instruction
            }
        ]
        
        if request.context and request.context.content:
            messages.append({
                "role": "user",
                "content": f"Here's the current code for context:\n\n```{request.context.language or ''}\n{request.context.content}\n```"
            })
        
        return messages
    
    def _build_system_prompt(self, context: CodeContext | None) -> str:
        """Build system prompt based on context."""
        base_prompt = (
            "You are an expert software developer and code assistant. "
            "Generate clean, efficient, well-structured code following best practices. "
            "Include proper error handling, type hints, and documentation when appropriate. "
            "Focus on maintainability, performance, and readability."
        )
        
        if context and context.language:
            language_prompt = f" You are working with {context.language} code."
            base_prompt += language_prompt
        
        if context and context.filepath:
            file_prompt = f" The target file is: {context.filepath}"
            base_prompt += file_prompt
        
        return base_prompt
    
    def _estimate_request_tokens(self, request: GenerationRequest) -> int:
        """Estimate total tokens for a request including response."""
        instruction_tokens = self.estimate_tokens(request.instruction)
        context_tokens = 0
        
        if request.context and request.context.content:
            context_tokens = self.estimate_tokens(request.context.content)
        
        system_prompt_tokens = self.estimate_tokens(self._build_system_prompt(request.context))
        
        return instruction_tokens + context_tokens + system_prompt_tokens + request.max_tokens
    
    def _get_model_token_limit(self) -> int:
        """Get token limit for the current model."""
        limits = {
            "gpt-4": 8192,
            "gpt-4-turbo": 128000,
            "gpt-4-turbo-preview": 128000,
            "gpt-3.5-turbo": 16384,
        }
        return limits.get(self._model_name, 4096)
