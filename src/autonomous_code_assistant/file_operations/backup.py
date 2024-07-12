"""Backup manager for safe file operations."""

import shutil
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from ..exceptions import FileOperationError


class BackupManager:
    """Manager for creating and restoring file backups."""
    
    def __init__(self, backup_dir: str | Path = ".backups", max_backups: int = 10) -> None:
        self.backup_dir = Path(backup_dir)
        self.max_backups = max_backups
        self.backup_dir.mkdir(exist_ok=True)
    
    def create_backup(self, filepath: str | Path) -> Path:
        """
        Create a timestamped backup of a file.
        
        Args:
            filepath: Path to the file to backup
            
        Returns:
            Path to the created backup file
            
        Raises:
            FileOperationError: If backup creation fails
        """
        filepath = Path(filepath)
        
        if not filepath.exists():
            raise FileOperationError(
                f"Cannot backup non-existent file: {filepath}",
                filepath=str(filepath),
                operation="backup"
            )
        
        # Generate backup filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{filepath.stem}_{timestamp}{filepath.suffix}.bak"
        backup_path = self.backup_dir / backup_name
        
        try:
            shutil.copy2(str(filepath), str(backup_path))
            
            # Clean up old backups
            self._cleanup_old_backups(filepath)
            
            return backup_path
            
        except Exception as e:
            raise FileOperationError(
                f"Failed to create backup: {str(e)}",
                filepath=str(filepath),
                operation="backup",
                original_error=e
            )
    
    def restore_backup(self, backup_path: str | Path, target_path: str | Path | None = None) -> None:
        """
        Restore a file from backup.
        
        Args:
            backup_path: Path to the backup file
            target_path: Target path to restore to (if None, infers from backup name)
            
        Raises:
            FileOperationError: If restore operation fails
        """
        backup_path = Path(backup_path)
        
        if not backup_path.exists():
            raise FileOperationError(
                f"Backup file does not exist: {backup_path}",
                filepath=str(backup_path),
                operation="restore"
            )
        
        if target_path is None:
            # Try to infer original filename from backup
            target_path = self._infer_original_path(backup_path)
        else:
            target_path = Path(target_path)
        
        try:
            # Create target directory if it doesn't exist 
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            shutil.copy2(str(backup_path), str(target_path))
            
        except Exception as e:
            raise FileOperationError(
                f"Failed to restore backup: {str(e)}",
                filepath=str(backup_path),
                operation="restore",
                original_error=e
            )
    
    def list_backups(self, filepath: str | Path | None = None) -> list[dict[str, Any]]:
        """
        List available backups.
        
        Args:
            filepath: Optional path to filter backups for specific file
            
        Returns:
            List of backup information dictionaries
        """
        backups = []
        
        for backup_file in self.backup_dir.glob("*.bak"):
            try:
                stat = backup_file.stat()
                backup_info = {
                    'path': str(backup_file),
                    'name': backup_file.name,
                    'size': stat.st_size,
                    'created': datetime.fromtimestamp(stat.st_ctime),
                    'modified': datetime.fromtimestamp(stat.st_mtime),
                    'original_path': self._infer_original_path(backup_file),
                }
                
                # Filter by filepath if specified
                if filepath is None or backup_info['original_path'] == Path(filepath):
                    backups.append(backup_info)
                    
            except Exception:
                continue  # Skip corrupted backup files
        
        # Sort by creation time (newest first)
        return sorted(backups, key=lambda x: x['created'], reverse=True)
    
    def get_latest_backup(self, filepath: str | Path) -> Path | None:
        """
        Get the latest backup for a specific file.
        
        Args:
            filepath: Path to the original file
            
        Returns:
            Path to the latest backup or None if no backups exist
        """
        backups = self.list_backups(filepath)
        return Path(backups[0]['path']) if backups else None
    
    def cleanup_old_backups(self, filepath: str | Path | None = None, days: int = 30) -> int:
        """
        Clean up old backup files.
        
        Args:
            filepath: Optional path to clean backups for specific file
            days: Age threshold in days for cleanup
            
        Returns:
            Number of backups cleaned up
        """
        cutoff_time = datetime.now() - timedelta(days=days)
        cleaned_count = 0
        
        backups = self.list_backups(filepath)
        for backup in backups:
            if backup['created'] < cutoff_time:
                try:
                    Path(backup['path']).unlink()
                    cleaned_count += 1
                except Exception:
                    continue  # Skip files that can't be deleted
        
        return cleaned_count
    
    def get_backup_stats(self) -> dict[str, Any]:
        """
        Get statistics about backups.
        
        Returns:
            Dictionary with backup statistics
        """
        backups = self.list_backups()
        
        if not backups:
            return {
                'total_backups': 0,
                'total_size': 0,
                'oldest_backup': None,
                'newest_backup': None,
            }
        
        total_size = sum(backup['size'] for backup in backups)
        oldest = min(backups, key=lambda x: x['created'])
        newest = max(backups, key=lambda x: x['created'])
        
        return {
            'total_backups': len(backups),
            'total_size': total_size,
            'oldest_backup': oldest['created'],
            'newest_backup': newest['created'],
        }
    
    def _cleanup_old_backups(self, filepath: Path) -> None:
        """Clean up old backups for a specific file, keeping only max_backups."""
        if self.max_backups <= 0:
            return
        
        backups = self.list_backups(filepath)
        
        # Keep only the most recent backups
        if len(backups) > self.max_backups:
            backups_to_delete = backups[self.max_backups:]
            
            for backup in backups_to_delete:
                try:
                    Path(backup['path']).unlink()
                except Exception:
                    continue  # Skip files that can't be deleted
    
    def _infer_original_path(self, backup_path: Path) -> Path:
        """Infer the original file path from a backup filename."""
        # Expected format: filename_YYYYMMDD_HHMMSS.ext.bak
        name = backup_path.stem  # Remove .bak
        
        # Split by underscore and remove timestamp parts
        parts = name.split('_')
        if len(parts) >= 3:
            # Last two parts should be date and time
            original_name = '_'.join(parts[:-2])
            if '.' in name:
                # Get the original extension
                original_ext = Path(name).suffix
                original_name += original_ext
        else:
            # Fallback: just remove .bak
            original_name = name
        
        return Path(original_name)
