"""Custom exceptions for the autonomous code assistant."""


class CodeAssistantError(Exception):
    """Base exception class for all code assistant errors."""
    
    def __init__(self, message: str, code: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.code = code


class LLMProviderError(CodeAssistantError):
    """Exception raised when LLM provider operations fail."""
    
    def __init__(
        self, 
        message: str, 
        provider: str | None = None,
        model: str | None = None,
        original_error: Exception | None = None
    ) -> None:
        super().__init__(message)
        self.provider = provider
        self.model = model
        self.original_error = original_error


class FileOperationError(CodeAssistantError):
    """Exception raised when file operations fail."""
    
    def __init__(
        self, 
        message: str, 
        filepath: str | None = None,
        operation: str | None = None,
        original_error: Exception | None = None
    ) -> None:
        super().__init__(message)
        self.filepath = filepath
        self.operation = operation
        self.original_error = original_error


class ConfigurationError(CodeAssistantError):
    """Exception raised for configuration-related errors."""
    
    def __init__(
        self, 
        message: str, 
        config_key: str | None = None,
        config_file: str | None = None
    ) -> None:
        super().__init__(message)
        self.config_key = config_key
        self.config_file = config_file


class ValidationError(CodeAssistantError):
    """Exception raised when input validation fails."""
    
    def __init__(
        self, 
        message: str, 
        field: str | None = None,
        value: str | None = None
    ) -> None:
        super().__init__(message)
        self.field = field
        self.value = value
