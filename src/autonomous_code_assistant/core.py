"""Core autonomous code assistant with advanced capabilities and workflow management."""

import os
from pathlib import Path
from typing import Any

from .exceptions import CodeAssistantError, LLMProviderError, FileOperationError
from .file_operations import FileReader, FileWriter, CodeAnalyzer, BackupManager
from .providers import ProviderFactory, GenerationRequest, CodeContext
from .providers.base import LLMProvider, ProviderCapability


class CodeAssistant:
    """
    Advanced autonomous code assistant with comprehensive capabilities.
    
    Features:
    - Multi-provider LLM support with automatic fallback
    - Intelligent file analysis and language detection
    - Safe file operations with automatic backups
    - Context-aware code generation
    - Workflow management and task tracking
    """
    
    def __init__(
        self,
        provider_name: str = "openai",
        project_root: str | Path = ".",
        **provider_kwargs: Any
    ) -> None:
        self.project_root = Path(project_root).resolve()
        
        # Initialize components
        self.file_reader = FileReader()
        self.file_writer = FileWriter()
        self.code_analyzer = CodeAnalyzer()
        self.backup_manager = BackupManager(self.project_root / ".backups")
        
        # Initialize LLM provider
        try:
            self.provider = ProviderFactory.create_provider(provider_name, **provider_kwargs)
        except Exception as e:
            raise CodeAssistantError(
                f"Failed to initialize LLM provider '{provider_name}': {str(e)}",
                code="PROVIDER_INIT_ERROR"
            )
        
        # Set up ignore patterns from common files
        self._setup_ignore_patterns()
    
    def process_instruction(
        self,
        instruction: str,
        target_file: str | Path | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.2,
        create_backup: bool = True
    ) -> dict[str, Any]:
        """
        Process a code generation instruction.
        
        Args:
            instruction: The instruction for code generation
            target_file: Optional target file to modify
            max_tokens: Maximum tokens for generation
            temperature: Generation temperature
            create_backup: Whether to create backup before modifying files
            
        Returns:
            Dictionary with operation results
            
        Raises:
            CodeAssistantError: If processing fails
        """
        try:
            # Validate instruction
            if not instruction.strip():
                raise CodeAssistantError("Instruction cannot be empty", code="EMPTY_INSTRUCTION")
            
            # Prepare context if target file is specified
            context = None
            if target_file:
                context = self._prepare_file_context(target_file)
            
            # Create generation request
            request = GenerationRequest(
                instruction=instruction,
                context=context,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            # Validate the request
            self.provider.validate_request(request)
            
            # Check provider capabilities
            if not self.provider.supports_capability(ProviderCapability.CODE_GENERATION):
                raise CodeAssistantError(
                    f"Provider {self.provider.__class__.__name__} does not support code generation",
                    code="CAPABILITY_NOT_SUPPORTED"
                )
            
            # Generate code
            response = self.provider.generate_code(request)
            
            # Process the response
            result = {
                "instruction": instruction,
                "target_file": str(target_file) if target_file else None,
                "generated_content": response.content,
                "tokens_used": response.tokens_used,
                "model": response.model,
                "finish_reason": response.finish_reason,
                "success": True,
                "backup_created": False,
                "file_modified": False,
            }
            
            # Apply changes to target file if specified
            if target_file:
                result.update(self._apply_changes_to_file(
                    target_file, 
                    response.content, 
                    create_backup
                ))
            
            return result
            
        except (LLMProviderError, FileOperationError) as e:
            raise CodeAssistantError(
                f"Failed to process instruction: {str(e)}",
                code="PROCESSING_ERROR"
            ) from e
        except Exception as e:
            raise CodeAssistantError(
                f"Unexpected error during processing: {str(e)}",
                code="UNEXPECTED_ERROR"
            ) from e
    
    def analyze_project(self, include_patterns: list[str] | None = None) -> dict[str, Any]:
        """
        Analyze the entire project structure and dependencies.
        
        Args:
            include_patterns: Optional list of glob patterns to include
            
        Returns:
            Dictionary with project analysis
        """
        try:
            analysis = {
                "project_root": str(self.project_root),
                "files": [],
                "languages": {},
                "dependencies": set(),
                "total_files": 0,
                "total_lines": 0,
                "errors": [],
            }
            
            # Find all relevant files
            if include_patterns:
                files = []
                for pattern in include_patterns:
                    files.extend(self.project_root.glob(pattern))
            else:
                files = [f for f in self.project_root.rglob("*") if f.is_file()]
            
            for filepath in files:
                try:
                    # Skip if should be ignored
                    if self.file_reader.should_ignore_file(filepath):
                        continue
                    
                    # Skip if not a text file
                    if not self.file_reader.is_text_file(filepath):
                        continue
                    
                    # Analyze the file
                    file_analysis = self.code_analyzer.analyze_file_structure(filepath)
                    analysis["files"].append(file_analysis)
                    
                    # Update aggregated data
                    language = file_analysis.get("language")
                    if language:
                        analysis["languages"][language] = analysis["languages"].get(language, 0) + 1
                    
                    dependencies = file_analysis.get("dependencies", [])
                    analysis["dependencies"].update(dependencies)
                    
                    analysis["total_files"] += 1
                    analysis["total_lines"] += file_analysis.get("line_count", 0)
                    
                except Exception as e:
                    analysis["errors"].append({
                        "file": str(filepath),
                        "error": str(e)
                    })
            
            # Convert dependencies set to sorted list
            analysis["dependencies"] = sorted(list(analysis["dependencies"]))
            
            return analysis
            
        except Exception as e:
            raise CodeAssistantError(
                f"Failed to analyze project: {str(e)}",
                code="ANALYSIS_ERROR"
            ) from e
    
    def review_code(self, filepath: str | Path) -> dict[str, Any]:
        """
        Review code in a file and provide suggestions.
        
        Args:
            filepath: Path to the file to review
            
        Returns:
            Dictionary with code review results
            
        Raises:
            CodeAssistantError: If review fails
        """
        if not self.provider.supports_capability(ProviderCapability.CODE_REVIEW):
            raise CodeAssistantError(
                f"Provider {self.provider.__class__.__name__} does not support code review",
                code="CAPABILITY_NOT_SUPPORTED"
            )
        
        try:
            # Prepare context
            context = self._prepare_file_context(filepath)
            
            # Create review instruction
            instruction = (
                "Review this code for potential issues, improvements, and best practices. "
                "Provide specific, actionable feedback focusing on:\n"
                "1. Code quality and maintainability\n"
                "2. Performance considerations\n"
                "3. Security vulnerabilities\n"
                "4. Error handling\n"
                "5. Code style and conventions\n"
                "Format your response as a structured review."
            )
            
            request = GenerationRequest(
                instruction=instruction,
                context=context,
                max_tokens=2048,
                temperature=0.1  # Lower temperature for more consistent reviews
            )
            
            response = self.provider.generate_code(request)
            
            return {
                "filepath": str(filepath),
                "language": context.language if context else None,
                "review": response.content,
                "tokens_used": response.tokens_used,
                "model": response.model,
            }
            
        except Exception as e:
            raise CodeAssistantError(
                f"Failed to review code: {str(e)}",
                code="REVIEW_ERROR"
            ) from e
    
    def refactor_code(self, filepath: str | Path, refactor_instruction: str) -> dict[str, Any]:
        """
        Refactor code in a file based on instructions.
        
        Args:
            filepath: Path to the file to refactor
            refactor_instruction: Specific refactoring instructions
            
        Returns:
            Dictionary with refactoring results
            
        Raises:
            CodeAssistantError: If refactoring fails
        """
        if not self.provider.supports_capability(ProviderCapability.CODE_REFACTORING):
            raise CodeAssistantError(
                f"Provider {self.provider.__class__.__name__} does not support code refactoring",
                code="CAPABILITY_NOT_SUPPORTED"
            )
        
        instruction = f"Refactor the following code according to these instructions: {refactor_instruction}"
        
        return self.process_instruction(
            instruction=instruction,
            target_file=filepath,
            temperature=0.1  # Lower temperature for consistent refactoring
        )
    
    def generate_documentation(self, filepath: str | Path) -> dict[str, Any]:
        """
        Generate documentation for code in a file.
        
        Args:
            filepath: Path to the file to document
            
        Returns:
            Dictionary with documentation generation results
            
        Raises:
            CodeAssistantError: If documentation generation fails
        """
        if not self.provider.supports_capability(ProviderCapability.DOCUMENTATION):
            raise CodeAssistantError(
                f"Provider {self.provider.__class__.__name__} does not support documentation generation",
                code="CAPABILITY_NOT_SUPPORTED"
            )
        
        try:
            context = self._prepare_file_context(filepath)
            language = context.language if context else "code"
            
            instruction = (
                f"Generate comprehensive documentation for this {language} code. "
                "Include:\n"
                "1. Module/file overview\n"
                "2. Function and class documentation\n"
                "3. Parameter descriptions\n"
                "4. Return value descriptions\n"
                "5. Usage examples where appropriate\n"
                "Follow the standard documentation conventions for the language."
            )
            
            request = GenerationRequest(
                instruction=instruction,
                context=context,
                max_tokens=3072,
                temperature=0.2
            )
            
            response = self.provider.generate_code(request)
            
            return {
                "filepath": str(filepath),
                "language": language,
                "documentation": response.content,
                "tokens_used": response.tokens_used,
                "model": response.model,
            }
            
        except Exception as e:
            raise CodeAssistantError(
                f"Failed to generate documentation: {str(e)}",
                code="DOCUMENTATION_ERROR"
            ) from e
    
    def get_provider_info(self) -> dict[str, Any]:
        """Get information about the current LLM provider."""
        info = self.provider.get_provider_info()
        info["health_check"] = self.provider.check_health()
        return info
    
    def _prepare_file_context(self, filepath: str | Path) -> CodeContext:
        """Prepare code context for a file."""
        filepath = Path(filepath)
        
        if not filepath.is_absolute():
            filepath = self.project_root / filepath
        
        try:
            content = self.file_reader.read_file(filepath)
            language = self.code_analyzer.detect_language(filepath, content)
            dependencies = self.code_analyzer.extract_dependencies(filepath, content)
            
            return CodeContext(
                content=content,
                filepath=str(filepath.relative_to(self.project_root)),
                language=language,
                dependencies=dependencies
            )
            
        except Exception as e:
            raise FileOperationError(
                f"Failed to prepare file context: {str(e)}",
                filepath=str(filepath),
                operation="prepare_context",
                original_error=e
            )
    
    def _apply_changes_to_file(
        self, 
        filepath: str | Path, 
        content: str, 
        create_backup: bool
    ) -> dict[str, Any]:
        """Apply generated content to a file."""
        filepath = Path(filepath)
        
        if not filepath.is_absolute():
            filepath = self.project_root / filepath
        
        result = {
            "backup_created": False,
            "file_modified": False,
            "backup_path": None,
        }
        
        try:
            # Create backup if requested and file exists
            if create_backup and filepath.exists():
                backup_path = self.backup_manager.create_backup(filepath)
                result["backup_created"] = True
                result["backup_path"] = str(backup_path)
            
            # Write the new content
            self.file_writer.write_file(filepath, content)
            result["file_modified"] = True
            
            return result
            
        except Exception as e:
            raise FileOperationError(
                f"Failed to apply changes to file: {str(e)}",
                filepath=str(filepath),
                operation="apply_changes",
                original_error=e
            )
    
    def _setup_ignore_patterns(self) -> None:
        """Set up file ignore patterns from .gitignore and other sources."""
        patterns = []
        
        # Default patterns
        default_patterns = [
            "__pycache__/*",
            "*.pyc",
            "*.pyo",
            "*.pyd",
            ".git/*",
            ".svn/*",
            ".hg/*",
            "node_modules/*",
            "*.log",
            "*.tmp",
            "*.temp",
            ".DS_Store",
            "Thumbs.db",
        ]
        patterns.extend(default_patterns)
        
        # Read .gitignore if it exists
        gitignore_path = self.project_root / ".gitignore"
        if gitignore_path.exists():
            try:
                gitignore_content = self.file_reader.read_file(gitignore_path)
                gitignore_patterns = [
                    line.strip() for line in gitignore_content.splitlines()
                    if line.strip() and not line.startswith('#')
                ]
                patterns.extend(gitignore_patterns)
            except Exception:
                pass  # Ignore errors reading .gitignore
        
        # Set patterns on file reader
        self.file_reader.set_ignore_patterns(patterns)
