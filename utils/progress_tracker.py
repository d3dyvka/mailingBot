"""
Progress Tracker for Telegram Mailer MacOS App.

Tracks mailing progress with append-only file logic to ensure data persistence
and prevent duplicate message sends.
"""

from pathlib import Path
from typing import Set, Dict, Any
from datetime import datetime
import hashlib


class ProgressTracker:
    """
    Tracks progress of Telegram mailing campaigns.
    
    Uses append-only file logic where each sent message is appended to a text file.
    The file is never overwritten, ensuring data persistence and crash recovery.
    
    File format uses bilingual field names (Russian/English):
    - ID_Пользователя/User_ID: {user_id}
    - Время_Отправки/Send_Time: {timestamp}
    - ---
    
    Attributes:
        progress_dir: Directory where progress files are stored
        current_group_url: URL of the current group being processed
        sent_users: Set of user IDs that have been sent messages
        progress_file: Path to the current progress file
    """
    
    def __init__(self, progress_dir: Path):
        """
        Initialize Progress Tracker.
        
        Args:
            progress_dir: Directory for storing progress files
        """
        self.progress_dir = Path(progress_dir)
        self.progress_dir.mkdir(parents=True, exist_ok=True)
        
        self.current_group_url: str = ""
        self.sent_users: Set[int] = set()
        self.progress_file: Path = None
        self.total_users: int = 0
        
    def _get_group_hash(self, group_url: str) -> str:
        """
        Generate a hash for the group URL to use as filename.
        
        Args:
            group_url: Telegram group URL
            
        Returns:
            str: SHA256 hash of the group URL (first 16 characters)
        """
        hash_obj = hashlib.sha256(group_url.encode('utf-8'))
        return hash_obj.hexdigest()[:16]
    
    def _get_progress_file_path(self, group_url: str) -> Path:
        """
        Get the path to the progress file for a specific group.
        
        Args:
            group_url: Telegram group URL
            
        Returns:
            Path: Path to the progress file
        """
        group_hash = self._get_group_hash(group_url)
        return self.progress_dir / f"progress_{group_hash}.txt"
    
    def load_progress(self, group_url: str) -> Set[int]:
        """
        Load progress from file for a specific group.
        
        Parses the progress file and extracts all User_IDs that have been sent.
        
        Args:
            group_url: Telegram group URL
            
        Returns:
            Set[int]: Set of user IDs that have already received messages
        """
        self.current_group_url = group_url
        self.progress_file = self._get_progress_file_path(group_url)
        self.sent_users = set()
        
        if not self.progress_file.exists():
            return self.sent_users
        
        try:
            with open(self.progress_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    # Parse lines with format: ID_Пользователя/User_ID: {user_id}
                    if line.startswith('ID_Пользователя/User_ID:'):
                        user_id_str = line.split(':', 1)[1].strip()
                        try:
                            user_id = int(user_id_str)
                            self.sent_users.add(user_id)
                        except ValueError:
                            # Skip invalid lines
                            continue
        except Exception as e:
            # If file is corrupted, start fresh
            print(f"Warning: Could not load progress file: {e}")
            self.sent_users = set()
        
        return self.sent_users
    
    def append_sent_user(self, user_id: int, timestamp: datetime = None) -> None:
        """
        Append a sent user record to the progress file.
        
        This method uses append-only logic - it never overwrites the file,
        only adds new records to the end.
        
        Args:
            user_id: Telegram user ID
            timestamp: Time when message was sent (defaults to current time)
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        if self.progress_file is None:
            raise ValueError("Progress file not initialized. Call load_progress() first.")
        
        # Format timestamp in ISO 8601 format
        timestamp_str = timestamp.strftime('%Y-%m-%dT%H:%M:%S')
        
        # Append to file (never overwrite)
        with open(self.progress_file, 'a', encoding='utf-8') as f:
            f.write(f"ID_Пользователя/User_ID: {user_id}\n")
            f.write(f"Время_Отправки/Send_Time: {timestamp_str}\n")
            f.write("---\n")
        
        # Update in-memory set
        self.sent_users.add(user_id)
    
    def mark_sent(self, user_id: int) -> None:
        """
        Mark a user as having received a message.
        
        This is a convenience method that calls append_sent_user with current timestamp.
        
        Args:
            user_id: Telegram user ID
        """
        self.append_sent_user(user_id)
    
    def is_sent(self, user_id: int) -> bool:
        """
        Check if a user has already received a message.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            bool: True if user has received a message, False otherwise
        """
        return user_id in self.sent_users
    
    def get_statistics(self) -> Dict[str, int]:
        """
        Get statistics about the mailing progress.
        
        Returns:
            Dict[str, int]: Dictionary with keys:
                - sent: Number of messages sent
                - remaining: Number of messages remaining (if total_users is set)
                - total: Total number of users (if set)
        """
        sent_count = len(self.sent_users)
        
        stats = {
            'sent': sent_count,
            'total': self.total_users,
            'remaining': max(0, self.total_users - sent_count) if self.total_users > 0 else 0
        }
        
        return stats
    
    def reset_progress(self, group_url: str) -> None:
        """
        Reset progress for a group to start a new mailing campaign.
        
        This deletes the progress file and clears the in-memory state.
        
        Args:
            group_url: Telegram group URL
        """
        progress_file = self._get_progress_file_path(group_url)
        
        if progress_file.exists():
            progress_file.unlink()
        
        self.sent_users = set()
        self.current_group_url = ""
        self.progress_file = None
        self.total_users = 0
    
    def set_total_users(self, total: int) -> None:
        """
        Set the total number of users for statistics calculation.
        
        Args:
            total: Total number of users in the group
        """
        self.total_users = total
    
    def update_summary(self, total_users: int, sent_count: int) -> None:
        """
        Update summary statistics at the end of the progress file.
        
        This appends summary information to the file for human readability.
        
        Args:
            total_users: Total number of users in the group
            sent_count: Number of messages sent
        """
        if self.progress_file is None:
            raise ValueError("Progress file not initialized. Call load_progress() first.")
        
        timestamp_str = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
        
        # Append summary to file
        with open(self.progress_file, 'a', encoding='utf-8') as f:
            f.write("\n")
            f.write(f"Всего_Пользователей/Total_Users: {total_users}\n")
            f.write(f"Отправлено/Sent_Count: {sent_count}\n")
            f.write(f"Последнее_Обновление/Last_Updated: {timestamp_str}\n")
