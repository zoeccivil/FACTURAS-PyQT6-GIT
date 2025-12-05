"""
Backup Manager Module
Handles automated SQLite database backups with retention policy.
"""

import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path
import config_manager


class BackupManager:
    """Manages SQLite database backups with retention policy"""
    
    def __init__(self, db_path: str, backup_dir: str = None):
        """
        Initialize backup manager.
        
        Args:
            db_path: Path to the SQLite database file
            backup_dir: Directory to store backups (defaults to ./backups)
        """
        self.db_path = db_path
        self.backup_dir = backup_dir or os.path.join(
            os.path.dirname(db_path) or ".",
            "backups"
        )
        self._ensure_backup_dir()
    
    def _ensure_backup_dir(self):
        """Ensure backup directory exists"""
        Path(self.backup_dir).mkdir(parents=True, exist_ok=True)
    
    def create_backup(self) -> tuple[bool, str]:
        """
        Create a new backup of the database.
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            if not os.path.exists(self.db_path):
                return False, f"Database file not found: {self.db_path}"
            
            # Generate backup filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            db_name = os.path.basename(self.db_path)
            backup_name = f"{os.path.splitext(db_name)[0]}_backup_{timestamp}.db"
            backup_path = os.path.join(self.backup_dir, backup_name)
            
            # Copy database file
            shutil.copy2(self.db_path, backup_path)
            
            # Verify backup
            if not os.path.exists(backup_path):
                return False, "Backup file was not created"
            
            backup_size = os.path.getsize(backup_path)
            return True, f"Backup created: {backup_name} ({backup_size:,} bytes)"
            
        except Exception as e:
            return False, f"Error creating backup: {e}"
    
    def cleanup_old_backups(self, retention_days: int = 30) -> tuple[int, str]:
        """
        Remove backups older than retention period.
        
        Args:
            retention_days: Number of days to keep backups (default: 30)
            
        Returns:
            Tuple of (count_deleted: int, message: str)
        """
        try:
            if not os.path.exists(self.backup_dir):
                return 0, "Backup directory does not exist"
            
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            deleted_count = 0
            total_size_freed = 0
            
            # Scan backup directory
            for filename in os.listdir(self.backup_dir):
                if not filename.endswith('.db'):
                    continue
                
                file_path = os.path.join(self.backup_dir, filename)
                
                # Check file age
                file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                
                if file_mtime < cutoff_date:
                    try:
                        file_size = os.path.getsize(file_path)
                        os.remove(file_path)
                        deleted_count += 1
                        total_size_freed += file_size
                    except Exception as e:
                        print(f"Error deleting {filename}: {e}")
            
            if deleted_count > 0:
                size_mb = total_size_freed / (1024 * 1024)
                return deleted_count, f"Deleted {deleted_count} old backup(s), freed {size_mb:.2f} MB"
            else:
                return 0, "No old backups to delete"
                
        except Exception as e:
            return 0, f"Error during cleanup: {e}"
    
    def list_backups(self) -> list[dict]:
        """
        List all available backups.
        
        Returns:
            List of backup info dictionaries
        """
        backups = []
        
        try:
            if not os.path.exists(self.backup_dir):
                return backups
            
            for filename in os.listdir(self.backup_dir):
                if not filename.endswith('.db'):
                    continue
                
                file_path = os.path.join(self.backup_dir, filename)
                stat = os.stat(file_path)
                
                backups.append({
                    'filename': filename,
                    'path': file_path,
                    'size': stat.st_size,
                    'created': datetime.fromtimestamp(stat.st_mtime),
                    'age_days': (datetime.now() - datetime.fromtimestamp(stat.st_mtime)).days
                })
            
            # Sort by creation date (newest first)
            backups.sort(key=lambda x: x['created'], reverse=True)
            
        except Exception as e:
            print(f"Error listing backups: {e}")
        
        return backups
    
    def restore_backup(self, backup_path: str) -> tuple[bool, str]:
        """
        Restore a backup file.
        
        Args:
            backup_path: Path to the backup file to restore
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            if not os.path.exists(backup_path):
                return False, f"Backup file not found: {backup_path}"
            
            # Create a backup of current database before restoring
            if os.path.exists(self.db_path):
                pre_restore_backup = f"{self.db_path}.pre_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
                shutil.copy2(self.db_path, pre_restore_backup)
            
            # Restore the backup
            shutil.copy2(backup_path, self.db_path)
            
            return True, f"Database restored from {os.path.basename(backup_path)}"
            
        except Exception as e:
            return False, f"Error restoring backup: {e}"
    
    def delete_backup(self, backup_path: str) -> tuple[bool, str]:
        """
        Delete a specific backup file.
        
        Args:
            backup_path: Path to the backup file to delete
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            if not os.path.exists(backup_path):
                return False, "Backup file not found"
            
            os.remove(backup_path)
            return True, f"Backup deleted: {os.path.basename(backup_path)}"
            
        except Exception as e:
            return False, f"Error deleting backup: {e}"


def get_backup_manager(db_path: str = None) -> BackupManager:
    """
    Get a BackupManager instance for the configured database.
    
    Args:
        db_path: Optional database path (uses config if not provided)
        
    Returns:
        BackupManager instance
    """
    if not db_path:
        config = config_manager.load_config()
        db_path = config.get('facturas_config') or config.get('database_path')
    
    if not db_path:
        raise ValueError("No database path configured")
    
    return BackupManager(db_path)


def create_daily_backup() -> tuple[bool, str]:
    """
    Create a daily backup and cleanup old backups.
    
    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        manager = get_backup_manager()
        
        # Create backup
        success, msg = manager.create_backup()
        if not success:
            return False, msg
        
        # Cleanup old backups
        deleted, cleanup_msg = manager.cleanup_old_backups(retention_days=30)
        
        full_msg = f"{msg}\n{cleanup_msg}"
        return True, full_msg
        
    except Exception as e:
        return False, f"Error in daily backup: {e}"
