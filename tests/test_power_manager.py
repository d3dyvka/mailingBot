"""
Unit tests for PowerManager.

Tests sleep prevention functionality on macOS using the caffeinate command.
"""

import pytest
import time
import subprocess
from unittest.mock import patch, MagicMock
from utils.power_manager import PowerManager


class TestPowerManager:
    """Test suite for PowerManager class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.pm = PowerManager()
    
    def teardown_method(self):
        """Clean up - ensure sleep prevention is stopped."""
        if self.pm.is_sleep_prevented():
            self.pm.allow_sleep()
    
    def test_initialization(self):
        """Test PowerManager initialization."""
        assert not self.pm.is_sleep_prevented()
        assert self.pm._process is None
        assert self.pm._is_prevented is False
    
    def test_prevent_sleep_activates(self):
        """Test that prevent_sleep activates sleep prevention."""
        self.pm.prevent_sleep()
        
        assert self.pm.is_sleep_prevented()
        assert self.pm._process is not None
        assert self.pm._is_prevented is True
        
        # Verify caffeinate process is running
        assert self.pm._process.poll() is None  # None means still running
    
    def test_allow_sleep_deactivates(self):
        """Test that allow_sleep deactivates sleep prevention."""
        self.pm.prevent_sleep()
        assert self.pm.is_sleep_prevented()
        
        self.pm.allow_sleep()
        
        assert not self.pm.is_sleep_prevented()
        assert self.pm._process is None
        assert self.pm._is_prevented is False
    
    def test_prevent_sleep_idempotent(self):
        """Test that calling prevent_sleep multiple times is safe."""
        self.pm.prevent_sleep()
        first_process = self.pm._process
        
        # Call again
        self.pm.prevent_sleep()
        
        # Should still be the same process
        assert self.pm._process is first_process
        assert self.pm.is_sleep_prevented()
    
    def test_allow_sleep_idempotent(self):
        """Test that calling allow_sleep multiple times is safe."""
        self.pm.prevent_sleep()
        self.pm.allow_sleep()
        
        # Call again - should not raise error
        self.pm.allow_sleep()
        
        assert not self.pm.is_sleep_prevented()
    
    def test_allow_sleep_without_prevent(self):
        """Test that allow_sleep works even if prevent_sleep was never called."""
        # Should not raise error
        self.pm.allow_sleep()
        
        assert not self.pm.is_sleep_prevented()
    
    def test_is_sleep_prevented_accuracy(self):
        """Test that is_sleep_prevented accurately reflects state."""
        assert not self.pm.is_sleep_prevented()
        
        self.pm.prevent_sleep()
        assert self.pm.is_sleep_prevented()
        
        self.pm.allow_sleep()
        assert not self.pm.is_sleep_prevented()
    
    def test_context_manager_prevents_sleep(self):
        """Test PowerManager as context manager."""
        with PowerManager() as pm:
            assert pm.is_sleep_prevented()
        
        # After exiting context, sleep should be allowed
        assert not pm.is_sleep_prevented()
    
    def test_context_manager_cleanup_on_exception(self):
        """Test that context manager cleans up even on exception."""
        pm = PowerManager()
        
        try:
            with pm:
                assert pm.is_sleep_prevented()
                raise ValueError("Test exception")
        except ValueError:
            pass
        
        # Sleep prevention should be deactivated
        assert not pm.is_sleep_prevented()
    
    def test_destructor_cleanup(self):
        """Test that __del__ cleans up caffeinate process."""
        pm = PowerManager()
        pm.prevent_sleep()
        
        process = pm._process
        assert process.poll() is None  # Process is running
        
        # Delete the PowerManager
        del pm
        
        # Give it a moment to clean up
        time.sleep(0.1)
        
        # Process should be terminated
        assert process.poll() is not None
    
    def test_caffeinate_command_arguments(self):
        """Test that caffeinate is called with correct arguments."""
        with patch('subprocess.Popen') as mock_popen:
            mock_process = MagicMock()
            mock_process.poll.return_value = None
            mock_popen.return_value = mock_process
            
            pm = PowerManager()
            pm.prevent_sleep()
            
            # Verify caffeinate was called with correct flags
            mock_popen.assert_called_once()
            call_args = mock_popen.call_args
            assert call_args[0][0] == ['caffeinate', '-d', '-i', '-s']
    
    def test_caffeinate_not_found_error(self):
        """Test error handling when caffeinate command is not found."""
        with patch('subprocess.Popen', side_effect=FileNotFoundError()):
            pm = PowerManager()
            
            with pytest.raises(RuntimeError) as exc_info:
                pm.prevent_sleep()
            
            assert "caffeinate command not found" in str(exc_info.value)
            assert not pm.is_sleep_prevented()
    
    def test_caffeinate_start_error(self):
        """Test error handling when caffeinate fails to start."""
        with patch('subprocess.Popen', side_effect=Exception("Start failed")):
            pm = PowerManager()
            
            with pytest.raises(RuntimeError) as exc_info:
                pm.prevent_sleep()
            
            assert "Failed to start caffeinate" in str(exc_info.value)
            assert not pm.is_sleep_prevented()
    
    def test_process_termination_graceful(self):
        """Test that allow_sleep terminates process gracefully."""
        self.pm.prevent_sleep()
        process = self.pm._process
        
        self.pm.allow_sleep()
        
        # Process should be terminated
        assert process.poll() is not None
    
    def test_process_termination_forced(self):
        """Test that allow_sleep force-kills process if it doesn't terminate."""
        with patch('subprocess.Popen') as mock_popen:
            mock_process = MagicMock()
            mock_process.poll.return_value = None
            mock_process.wait.side_effect = subprocess.TimeoutExpired('caffeinate', 5)
            mock_popen.return_value = mock_process
            
            pm = PowerManager()
            pm.prevent_sleep()
            pm.allow_sleep()
            
            # Verify kill was called after timeout
            mock_process.kill.assert_called_once()
    
    def test_is_sleep_prevented_detects_dead_process(self):
        """Test that is_sleep_prevented detects when process dies unexpectedly."""
        self.pm.prevent_sleep()
        
        # Manually kill the process
        self.pm._process.kill()
        self.pm._process.wait()
        
        # is_sleep_prevented should detect this and return False
        assert not self.pm.is_sleep_prevented()
        assert self.pm._process is None
        assert not self.pm._is_prevented
    
    def test_multiple_instances(self):
        """Test that multiple PowerManager instances work independently."""
        pm1 = PowerManager()
        pm2 = PowerManager()
        
        pm1.prevent_sleep()
        assert pm1.is_sleep_prevented()
        assert not pm2.is_sleep_prevented()
        
        pm2.prevent_sleep()
        assert pm1.is_sleep_prevented()
        assert pm2.is_sleep_prevented()
        
        pm1.allow_sleep()
        assert not pm1.is_sleep_prevented()
        assert pm2.is_sleep_prevented()
        
        pm2.allow_sleep()
        assert not pm1.is_sleep_prevented()
        assert not pm2.is_sleep_prevented()
    
    def test_prevent_sleep_during_operation(self):
        """Test that sleep prevention works during a simulated operation."""
        self.pm.prevent_sleep()
        
        # Simulate some work
        time.sleep(0.5)
        
        # Should still be prevented
        assert self.pm.is_sleep_prevented()
        assert self.pm._process.poll() is None
        
        self.pm.allow_sleep()
    
    def test_state_consistency_after_error(self):
        """Test that state remains consistent after errors."""
        with patch('subprocess.Popen', side_effect=Exception("Test error")):
            pm = PowerManager()
            
            try:
                pm.prevent_sleep()
            except RuntimeError:
                pass
            
            # State should be consistent
            assert not pm.is_sleep_prevented()
            assert pm._process is None
            assert not pm._is_prevented
    
    def test_allow_sleep_handles_missing_process(self):
        """Test that allow_sleep handles case where process is None but flag is set."""
        self.pm._is_prevented = True
        self.pm._process = None
        
        # Should not raise error
        self.pm.allow_sleep()
        
        assert not self.pm.is_sleep_prevented()
        assert not self.pm._is_prevented
    
    def test_context_manager_nested(self):
        """Test nested context managers."""
        with PowerManager() as pm1:
            assert pm1.is_sleep_prevented()
            
            with PowerManager() as pm2:
                assert pm1.is_sleep_prevented()
                assert pm2.is_sleep_prevented()
            
            # pm2 should be deactivated, pm1 still active
            assert pm1.is_sleep_prevented()
            assert not pm2.is_sleep_prevented()
        
        # Both should be deactivated
        assert not pm1.is_sleep_prevented()
        assert not pm2.is_sleep_prevented()
    
    def test_prevent_sleep_after_allow_sleep(self):
        """Test that sleep can be prevented again after being allowed."""
        self.pm.prevent_sleep()
        self.pm.allow_sleep()
        
        # Should be able to prevent again
        self.pm.prevent_sleep()
        
        assert self.pm.is_sleep_prevented()
        assert self.pm._process is not None
        assert self.pm._process.poll() is None
    
    def test_caffeinate_process_output_suppressed(self):
        """Test that caffeinate output is suppressed (DEVNULL)."""
        with patch('subprocess.Popen') as mock_popen:
            mock_process = MagicMock()
            mock_process.poll.return_value = None
            mock_popen.return_value = mock_process
            
            pm = PowerManager()
            pm.prevent_sleep()
            
            # Verify stdout and stderr are set to DEVNULL
            call_kwargs = mock_popen.call_args[1]
            assert call_kwargs['stdout'] == subprocess.DEVNULL
            assert call_kwargs['stderr'] == subprocess.DEVNULL


class TestPowerManagerIntegration:
    """Integration tests for PowerManager with real caffeinate process."""
    
    def test_real_caffeinate_process(self):
        """Test with real caffeinate process (integration test)."""
        pm = PowerManager()
        
        try:
            pm.prevent_sleep()
            
            # Verify process is actually running
            assert pm.is_sleep_prevented()
            assert pm._process is not None
            
            # Check that caffeinate is in the process list
            result = subprocess.run(
                ['pgrep', '-f', 'caffeinate'],
                capture_output=True,
                text=True
            )
            
            # Should find at least one caffeinate process
            assert result.returncode == 0
            assert len(result.stdout.strip()) > 0
            
        finally:
            pm.allow_sleep()
            
            # Give it a moment to terminate
            time.sleep(0.1)
            
            # Verify process is stopped
            assert not pm.is_sleep_prevented()
    
    def test_real_context_manager(self):
        """Test context manager with real caffeinate process."""
        with PowerManager() as pm:
            assert pm.is_sleep_prevented()
            
            # Verify caffeinate is running
            result = subprocess.run(
                ['pgrep', '-f', 'caffeinate'],
                capture_output=True,
                text=True
            )
            assert result.returncode == 0
        
        # After context, should be stopped
        assert not pm.is_sleep_prevented()

