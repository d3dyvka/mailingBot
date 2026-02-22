"""
Power Manager for Telegram Mailer MacOS App.

Prevents macOS from going to sleep during mailing campaigns using the
caffeinate command. Ensures continuous operation without interruption.
"""

import subprocess
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class PowerManager:
    """
    Manages macOS sleep prevention during mailing campaigns.
    
    Uses the macOS 'caffeinate' command to prevent the system from sleeping
    while a mailing campaign is in progress. This ensures network connections
    remain active and messages are sent without interruption.
    
    Attributes:
        _process: The caffeinate subprocess (None if not active)
        _is_prevented: Flag indicating if sleep is currently prevented
    """
    
    def __init__(self):
        """
        Initialize the power manager.
        
        The manager starts in an inactive state. Call prevent_sleep() to
        activate sleep prevention.
        """
        self._process: Optional[subprocess.Popen] = None
        self._is_prevented: bool = False
    
    def prevent_sleep(self) -> None:
        """
        Prevent the Mac from going to sleep.
        
        Starts the caffeinate process with the following flags:
        - -d: Prevent display sleep
        - -i: Prevent idle sleep
        - -s: Prevent system sleep (when on AC power)
        
        This ensures the system stays awake and network connections remain
        active during the mailing campaign.
        
        Note:
            If sleep prevention is already active, this method does nothing.
            
        Raises:
            RuntimeError: If caffeinate command fails to start
        """
        if self._is_prevented:
            logger.info("Sleep prevention already active")
            return
        
        try:
            # Start caffeinate process
            # -d: prevent display sleep
            # -i: prevent idle sleep
            # -s: prevent system sleep (when on AC power)
            self._process = subprocess.Popen(
                ['caffeinate', '-d', '-i', '-s'],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            self._is_prevented = True
            logger.info("Sleep prevention activated (caffeinate started)")
            
        except FileNotFoundError:
            # caffeinate command not found (not on macOS?)
            error_msg = "caffeinate command not found. Are you running on macOS?"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        
        except Exception as e:
            error_msg = f"Failed to start caffeinate: {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
    
    def allow_sleep(self) -> None:
        """
        Allow the Mac to go to sleep normally.
        
        Terminates the caffeinate process, allowing the system to sleep
        according to its normal power management settings.
        
        Note:
            If sleep prevention is not active, this method does nothing.
            Safe to call multiple times.
        """
        if not self._is_prevented:
            logger.info("Sleep prevention not active, nothing to do")
            return
        
        if self._process is not None:
            try:
                # Terminate the caffeinate process
                self._process.terminate()
                
                # Wait for process to finish (with timeout)
                try:
                    self._process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    # Force kill if it doesn't terminate gracefully
                    logger.warning("caffeinate didn't terminate gracefully, forcing kill")
                    self._process.kill()
                    self._process.wait()
                
                logger.info("Sleep prevention deactivated (caffeinate stopped)")
                
            except Exception as e:
                logger.error(f"Error stopping caffeinate: {e}")
            
            finally:
                self._process = None
                self._is_prevented = False
        else:
            # Process was None but flag was set - reset flag
            self._is_prevented = False
            logger.warning("Sleep prevention flag was set but no process found")
    
    def is_sleep_prevented(self) -> bool:
        """
        Check if sleep prevention is currently active.
        
        Returns:
            bool: True if sleep is currently being prevented, False otherwise
        """
        # Double-check that process is still running
        if self._is_prevented and self._process is not None:
            # Check if process is still alive
            if self._process.poll() is not None:
                # Process has terminated unexpectedly
                logger.warning("caffeinate process terminated unexpectedly")
                self._is_prevented = False
                self._process = None
                return False
        
        return self._is_prevented
    
    def __del__(self):
        """
        Cleanup when the PowerManager is destroyed.
        
        Ensures the caffeinate process is terminated when the PowerManager
        object is garbage collected.
        """
        if self._is_prevented:
            logger.info("PowerManager being destroyed, cleaning up")
            self.allow_sleep()
    
    def __enter__(self):
        """
        Context manager entry: activate sleep prevention.
        
        Usage:
            with PowerManager() as pm:
                # Sleep is prevented here
                send_messages()
            # Sleep is allowed again
        """
        self.prevent_sleep()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Context manager exit: deactivate sleep prevention.
        """
        self.allow_sleep()
        return False  # Don't suppress exceptions

