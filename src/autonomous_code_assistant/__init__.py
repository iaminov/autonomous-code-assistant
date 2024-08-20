"""
Autonomous Code Assistant

An advanced AI-powered coding assistant with pluggable LLM providers,
intelligent file analysis, and automated testing capabilities.
"""

__version__ = "0.1.0"
__author__ = "iaminov"
__email__ = "alexeaminov@gmail.com"

from .core import CodeAssistant
from .exceptions import CodeAssistantError, LLMProviderError, FileOperationError
from .providers.base import CodeContext

__all__ = [
    "CodeAssistant",
    "CodeAssistantError", 
    "LLMProviderError",
    "FileOperationError",
    "CodeContext",
    "__version__",
]
