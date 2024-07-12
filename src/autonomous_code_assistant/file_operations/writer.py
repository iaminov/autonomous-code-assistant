"""Secure file writer with atomic operations and backup support."""

import os
import shutil
import tempfile
from pathlib import Path
from typing import Any

from ..exceptions import FileOperationError


class FileWriter:
    """Secure file writer with atomic operations and backup support."""
    
    def __init__(self, create_backups: bool = True, backup_suffix: str = ".bak") -> None:
        self.create_backups = create_backups
        self.backup_suffix = backup_suffix
    
    def write_file(self, filepath: str | Path, content: str, encoding: str = "utf-8") -> None:
        """
        Write content to a file atomically with optional backup.
        
        Args:
            filepath: Path to write to
            content: Content to write
            encoding: File encoding to use
            
        Raises:
            FileOperationError: If write operation fails
        """
        filepath = Path(filepath)
        
        # Create parent directories if they don't exist
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        # Create backup if file exists and backups are enabled
        backup_path = None
        if self.create_backups and filepath.exists():
            backup_path = self._create_backup(filepath)
        
        try:
            self._write_atomic(filepath, content, encoding)
        except Exception as e:
            # Restore backup if write failed
            if backup_path and backup_path.exists():
                try:
                    shutil.move(str(backup_path), str(filepath))
                except Exception:
                    pass  # Backup restoration failed, but main error is more important
            
            raise FileOperationError(
                f"Failed to write file: {str(e)}",
                filepath=str(filepath),
                operation="write",
                original_error=e
            )
        
        # Clean up backup on successful write
        if backup_path and backup_path.exists():
            try:
                backup_path.unlink()
            except Exception:
                pass  # Backup cleanup failed, but write succeeded
    
    def append_file(self, filepath: str | Path, content: str, encoding: str = "utf-8") -> None:
        """
        Append content to a file.
        
        Args:
            filepath: Path to append to
            content: Content to append
            encoding: File encoding to use
            
        Raises:
            FileOperationError: If append operation fails
        """
        filepath = Path(filepath)
        
        try:
            with open(filepath, 'a', encoding=encoding) as f:
                f.write(content)
        except Exception as e:
            raise FileOperationError(
                f"Failed to append to file: {str(e)}",
                filepath=str(filepath),
                operation="append",
                original_error=e
            )
    
    def write_file_lines(self, filepath: str | Path, lines: list[str], encoding: str = "utf-8") -> None:
        """
        Write lines to a file.
        
        Args:
            filepath: Path to write to
            lines: Lines to write
            encoding: File encoding to use
            
        Raises:
            FileOperationError: If write operation fails
        """
        content = '\n'.join(lines)
        if lines and not content.endswith('\n'):
            content += '\n'
        
        self.write_file(filepath, content, encoding)
    
    def update_file_section(
        self, 
        filepath: str | Path, 
        new_content: str, 
        start_line: int, 
        end_line: int | None = None,
        encoding: str = "utf-8"
    ) -> None:
        """
        Update a specific section of a file.
        
        Args:
            filepath: Path to the file to update
            new_content: New content to insert
            start_line: Starting line number (1-based)
            end_line: Ending line number (1-based, inclusive). If None, replaces from start_line to end
            encoding: File encoding to use
            
        Raises:
            FileOperationError: If update operation fails
        """
        filepath = Path(filepath)
        
        try:
            # Read existing content
            with open(filepath, 'r', encoding=encoding) as f:
                lines = f.readlines()
            
            # Convert to 0-based indexing
            start_idx = max(0, start_line - 1)
            end_idx = min(len(lines), end_line) if end_line else len(lines)
            
            # Split new content into lines
            new_lines = new_content.splitlines(True)  # Keep line endings
            if new_lines and not new_lines[-1].endswith('\n'):
                new_lines[-1] += '\n'
            
            # Replace the section
            updated_lines = lines[:start_idx] + new_lines + lines[end_idx:]
            
            # Write back
            self.write_file(filepath, ''.join(updated_lines), encoding)
            
        except Exception as e:
            raise FileOperationError(
                f"Failed to update file section: {str(e)}",
                filepath=str(filepath),
                operation="update_section",
                original_error=e
            )
    
    def create_file_if_not_exists(self, filepath: str | Path, content: str = "", encoding: str = "utf-8") -> bool:
        """
        Create a file only if it doesn't exist.
        
        Args:
            filepath: Path to create
            content: Initial content
            encoding: File encoding to use
            
        Returns:
            True if file was created, False if it already existed
            
        Raises:
            FileOperationError: If creation fails
        """
        filepath = Path(filepath)
        
        if filepath.exists():
            return False
        
        self.write_file(filepath, content, encoding)
        return True
    
    def delete_file(self, filepath: str | Path) -> None:
        """
        Delete a file safely.
        
        Args:
            filepath: Path to delete
            
        Raises:
            FileOperationError: If deletion fails
        """
        filepath = Path(filepath)
        
        try:
            if filepath.exists():
                filepath.unlink()
        except Exception as e:
            raise FileOperationError(
                f"Failed to delete file: {str(e)}",
                filepath=str(filepath),
                operation="delete",
                original_error=e
            )
    
    def copy_file(self, src: str | Path, dst: str | Path) -> None:
        """
        Copy a file safely.
        
        Args:
            src: Source path
            dst: Destination path
            
        Raises:
            FileOperationError: If copy fails
        """
        src = Path(src)
        dst = Path(dst)
        
        try:
            # Create destination directory if it doesn't exist
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(src), str(dst))
        except Exception as e:
            raise FileOperationError(
                f"Failed to copy file from {src} to {dst}: {str(e)}",
                filepath=str(src),
                operation="copy",
                original_error=e
            )
    
    def _write_atomic(self, filepath: Path, content: str, encoding: str) -> None:
        """Write content atomically using a temporary file."""
        # Create temporary file in the same directory as the target
        temp_fd, temp_path = tempfile.mkstemp(
            dir=filepath.parent,
            prefix=f".{filepath.name}.",
            suffix=".tmp"
        )
        
        try:
            with os.fdopen(temp_fd, 'w', encoding=encoding) as f:
                f.write(content)
                f.flush()
                os.fsync(f.fileno())  # Ensure data is written to disk
            
            # Atomic move
            if os.name == 'nt':  # Windows
                if filepath.exists():
                    filepath.unlink()
            
            shutil.move(temp_path, str(filepath))
            
        except Exception:
            # Clean up temporary file on error
            try:
                os.unlink(temp_path)
            except Exception:
                pass
            raise
    
    def _create_backup(self, filepath: Path) -> Path:
        """Create a backup of the file."""
        backup_path = filepath.with_suffix(filepath.suffix + self.backup_suffix)
        
        # If backup already exists, add a number
        counter = 1
        original_backup = backup_path
        while backup_path.exists():
            backup_path = original_backup.with_suffix(f"{original_backup.suffix}.{counter}")
            counter += 1
        
        try:
            shutil.copy2(str(filepath), str(backup_path))
            return backup_path
        except Exception as e:
            raise FileOperationError(
                f"Failed to create backup: {str(e)}",
                filepath=str(filepath),
                operation="backup",
                original_error=e
            )
