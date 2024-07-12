"""Advanced file reader with encoding detection and security checks."""

import os
import mimetypes
from pathlib import Path
from typing import BinaryIO, TextIO

import pathspec

from ..exceptions import FileOperationError


class FileReader:
    """Advanced file reader with security and encoding detection."""
    
    # Maximum file size (10MB by default)
    DEFAULT_MAX_SIZE = 10 * 1024 * 1024
    
    # Supported text file extensions
    TEXT_EXTENSIONS = {
        '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c', '.h', '.hpp',
        '.cs', '.go', '.rs', '.php', '.rb', '.swift', '.kt', '.scala', '.dart',
        '.html', '.htm', '.css', '.scss', '.sass', '.less', '.xml', '.json',
        '.yaml', '.yml', '.toml', '.ini', '.cfg', '.conf', '.md', '.rst', '.txt',
        '.sql', '.sh', '.bash', '.zsh', '.fish', '.ps1', '.bat', '.cmd', '.dockerfile',
        '.makefile', '.cmake', '.gradle', '.maven', '.pom', '.lock', '.gitignore',
        '.gitattributes', '.editorconfig', '.flake8', '.pylintrc', '.mypy.ini',
    }
    
    # Binary file extensions to avoid
    BINARY_EXTENSIONS = {
        '.pyc', '.pyo', '.pyd', '.exe', '.dll', '.so', '.dylib', '.o', '.obj',
        '.a', '.lib', '.jar', '.war', '.ear', '.zip', '.tar', '.gz', '.bz2',
        '.xz', '.7z', '.rar', '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt',
        '.pptx', '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.svg', '.ico',
        '.mp3', '.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.ogg', '.wav',
    }
    
    def __init__(self, max_file_size: int = DEFAULT_MAX_SIZE) -> None:
        self.max_file_size = max_file_size
        self._ignore_spec: pathspec.PathSpec | None = None
    
    def set_ignore_patterns(self, patterns: list[str]) -> None:
        """Set patterns for files to ignore."""
        if patterns:
            self._ignore_spec = pathspec.PathSpec.from_lines('gitwildmatch', patterns)
        else:
            self._ignore_spec = None
    
    def read_file(self, filepath: str | Path) -> str:
        """
        Read a text file with automatic encoding detection.
        
        Args:
            filepath: Path to the file to read
            
        Returns:
            File content as string
            
        Raises:
            FileOperationError: If file cannot be read
        """
        filepath = Path(filepath)
        
        self._validate_file(filepath)
        
        try:
            # Try to detect encoding
            encoding = self._detect_encoding(filepath)
            
            with open(filepath, 'r', encoding=encoding, errors='replace') as f:
                content = f.read()
                
            return content
            
        except Exception as e:
            raise FileOperationError(
                f"Failed to read file: {str(e)}",
                filepath=str(filepath),
                operation="read",
                original_error=e
            )
    
    def read_file_lines(self, filepath: str | Path, start_line: int = 1, end_line: int | None = None) -> list[str]:
        """
        Read specific lines from a file.
        
        Args:
            filepath: Path to the file to read
            start_line: Starting line number (1-based)
            end_line: Ending line number (1-based, inclusive)
            
        Returns:
            List of lines
            
        Raises:
            FileOperationError: If file cannot be read
        """
        content = self.read_file(filepath)
        lines = content.splitlines()
        
        # Convert to 0-based indexing
        start_idx = max(0, start_line - 1)
        end_idx = min(len(lines), end_line) if end_line else len(lines)
        
        return lines[start_idx:end_idx]
    
    def is_text_file(self, filepath: str | Path) -> bool:
        """
        Check if a file is likely a text file.
        
        Args:
            filepath: Path to check
            
        Returns:
            True if likely a text file
        """
        filepath = Path(filepath)
        
        # Check extension first
        if filepath.suffix.lower() in self.BINARY_EXTENSIONS:
            return False
            
        if filepath.suffix.lower() in self.TEXT_EXTENSIONS:
            return True
        
        # Check MIME type
        mime_type, _ = mimetypes.guess_type(str(filepath))
        if mime_type:
            return mime_type.startswith('text/') or mime_type in {
                'application/json',
                'application/xml',
                'application/javascript',
                'application/x-python-code',
            }
        
        # Sample-based detection for files without clear indicators
        try:
            with open(filepath, 'rb') as f:
                sample = f.read(8192)  # Read first 8KB
            
            # Check for null bytes (strong indicator of binary)
            if b'\x00' in sample:
                return False
            
            # Try to decode as UTF-8
            try:
                sample.decode('utf-8')
                return True
            except UnicodeDecodeError:
                # Try other common encodings
                for encoding in ['latin1', 'cp1252', 'iso-8859-1']:
                    try:
                        sample.decode(encoding)
                        return True
                    except UnicodeDecodeError:
                        continue
                        
                return False
                
        except Exception:
            return False
    
    def should_ignore_file(self, filepath: str | Path) -> bool:
        """
        Check if a file should be ignored based on patterns.
        
        Args:
            filepath: Path to check
            
        Returns:
            True if file should be ignored
        """
        if not self._ignore_spec:
            return False
        
        return self._ignore_spec.match_file(str(filepath))
    
    def get_file_info(self, filepath: str | Path) -> dict[str, str | int | float]:
        """
        Get information about a file.
        
        Args:
            filepath: Path to analyze
            
        Returns:
            Dictionary with file information
        """
        filepath = Path(filepath)
        
        try:
            stat = filepath.stat()
            
            return {
                'path': str(filepath),
                'name': filepath.name,
                'stem': filepath.stem,
                'suffix': filepath.suffix,
                'size': stat.st_size,
                'modified': stat.st_mtime,
                'is_text': self.is_text_file(filepath),
                'should_ignore': self.should_ignore_file(filepath),
            }
            
        except Exception as e:
            raise FileOperationError(
                f"Failed to get file info: {str(e)}",
                filepath=str(filepath),
                operation="stat",
                original_error=e
            )
    
    def _validate_file(self, filepath: Path) -> None:
        """Validate that a file can be safely read."""
        if not filepath.exists():
            raise FileOperationError(
                f"File does not exist: {filepath}",
                filepath=str(filepath),
                operation="validate"
            )
        
        if not filepath.is_file():
            raise FileOperationError(
                f"Path is not a file: {filepath}",
                filepath=str(filepath),
                operation="validate"
            )
        
        # Check file size
        size = filepath.stat().st_size
        if size > self.max_file_size:
            raise FileOperationError(
                f"File too large: {size} bytes (max: {self.max_file_size})",
                filepath=str(filepath),
                operation="validate"
            )
        
        # Check if file should be ignored
        if self.should_ignore_file(filepath):
            raise FileOperationError(
                f"File matches ignore patterns: {filepath}",
                filepath=str(filepath),
                operation="validate"
            )
        
        # Check if it's a text file
        if not self.is_text_file(filepath):
            raise FileOperationError(
                f"File is not a text file: {filepath}",
                filepath=str(filepath),
                operation="validate"
            )
    
    def _detect_encoding(self, filepath: Path) -> str:
        """
        Detect file encoding.
        
        Args:
            filepath: Path to analyze
            
        Returns:
            Detected encoding name
        """
        # Try UTF-8 first (most common for code files)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                f.read(1024)  # Read a sample
            return 'utf-8'
        except UnicodeDecodeError:
            pass
        
        # Try other common encodings
        for encoding in ['latin1', 'cp1252', 'iso-8859-1']:
            try:
                with open(filepath, 'r', encoding=encoding) as f:
                    f.read(1024)
                return encoding
            except UnicodeDecodeError:
                continue
        
        # Fallback to utf-8 with error handling
        return 'utf-8'
