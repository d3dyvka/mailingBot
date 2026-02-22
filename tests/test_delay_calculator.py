"""
Unit tests for DelayCalculator.

Tests the delay calculation logic, validation, and edge cases.
"""

import pytest
from datetime import datetime, timedelta
from utils.delay_calculator import DelayCalculator, DelayResult
from utils.constants import MIN_SAFE_DELAY_HOURS, MAX_DELAY_HOURS, DEFAULT_BATCH_SIZE


class TestDelayCalculator:
    """Test suite for DelayCalculator class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.calculator = DelayCalculator()
    
    def test_initialization(self):
        """Test DelayCalculator initialization."""
        calc = DelayCalculator()
        assert calc.batch_size == DEFAULT_BATCH_SIZE
        
        calc_custom = DelayCalculator(batch_size=20)
        assert calc_custom.batch_size == 20
    
    def test_calculate_delay_basic(self):
        """Test basic delay calculation."""
        start_date = datetime(2024, 1, 1, 0, 0, 0)
        end_date = datetime(2024, 1, 10, 0, 0, 0)  # 9 days = 216 hours
        total_users = 36  # 2 batches
        
        result = self.calculator.calculate_delay(total_users, end_date, start_date)
        
        assert isinstance(result, DelayResult)
        assert result.num_batches == 2
        # Available hours: 216, send time: 2 * 0.15 = 0.3
        # Available delay time: 216 - 0.3 = 215.7
        # Delay: 215.7 / 1 = 215.7 hours
        # But capped at 24 hours
        assert result.delay_hours == MAX_DELAY_HOURS
        assert result.warning is not None
        assert "exceeds maximum" in result.warning.lower()
    
    def test_calculate_delay_single_batch(self):
        """Test delay calculation with only one batch."""
        start_date = datetime(2024, 1, 1, 0, 0, 0)
        end_date = datetime(2024, 1, 2, 0, 0, 0)
        total_users = 10  # 1 batch
        
        result = self.calculator.calculate_delay(total_users, end_date, start_date)
        
        assert result.num_batches == 1
        assert result.delay_hours == 0  # No delay needed for single batch
        assert result.is_safe  # Single batch is always safe
    
    def test_calculate_delay_exact_batches(self):
        """Test delay calculation with exact batch size."""
        start_date = datetime(2024, 1, 1, 0, 0, 0)
        end_date = datetime(2024, 1, 3, 0, 0, 0)  # 48 hours
        total_users = 18  # Exactly 1 batch
        
        result = self.calculator.calculate_delay(total_users, end_date, start_date)
        
        assert result.num_batches == 1
        assert result.delay_hours == 0
    
    def test_calculate_delay_multiple_batches(self):
        """Test delay calculation with multiple batches."""
        start_date = datetime(2024, 1, 1, 0, 0, 0)
        end_date = datetime(2024, 1, 3, 0, 0, 0)  # 48 hours
        total_users = 54  # 3 batches
        
        result = self.calculator.calculate_delay(total_users, end_date, start_date)
        
        assert result.num_batches == 3
        # Available hours: 48, send time: 3 * 0.15 = 0.45
        # Available delay time: 48 - 0.45 = 47.55
        # Delay: 47.55 / 2 = 23.775 hours
        assert result.delay_hours == pytest.approx(23.775, rel=0.01)
        assert result.is_safe  # > 20 hours
        assert result.warning is None
    
    def test_calculate_delay_unsafe(self):
        """Test delay calculation that results in unsafe delay."""
        start_date = datetime(2024, 1, 1, 0, 0, 0)
        end_date = datetime(2024, 1, 1, 12, 0, 0)  # 12 hours
        total_users = 36  # 2 batches
        
        result = self.calculator.calculate_delay(total_users, end_date, start_date)
        
        assert result.num_batches == 2
        # Available hours: 12, send time: 2 * 0.15 = 0.3
        # Available delay time: 12 - 0.3 = 11.7
        # Delay: 11.7 / 1 = 11.7 hours
        assert result.delay_hours == pytest.approx(11.7, rel=0.01)
        assert not result.is_safe  # < 20 hours
        assert result.warning is not None
        assert "below minimum safe delay" in result.warning.lower()
    
    def test_calculate_delay_max_cap(self):
        """Test that delay is capped at 24 hours."""
        start_date = datetime(2024, 1, 1, 0, 0, 0)
        end_date = datetime(2024, 2, 1, 0, 0, 0)  # 31 days
        total_users = 36  # 2 batches
        
        result = self.calculator.calculate_delay(total_users, end_date, start_date)
        
        assert result.delay_hours == MAX_DELAY_HOURS
        assert result.warning is not None
        assert "exceeds maximum" in result.warning.lower()
    
    def test_calculate_delay_no_start_date(self):
        """Test delay calculation without explicit start date."""
        end_date = datetime.now() + timedelta(days=5)
        total_users = 36
        
        result = self.calculator.calculate_delay(total_users, end_date)
        
        assert isinstance(result, DelayResult)
        assert result.num_batches == 2
    
    def test_calculate_delay_invalid_users(self):
        """Test delay calculation with invalid user count."""
        start_date = datetime(2024, 1, 1, 0, 0, 0)
        end_date = datetime(2024, 1, 2, 0, 0, 0)
        
        with pytest.raises(ValueError, match="total_users must be greater than 0"):
            self.calculator.calculate_delay(0, end_date, start_date)
        
        with pytest.raises(ValueError, match="total_users must be greater than 0"):
            self.calculator.calculate_delay(-10, end_date, start_date)
    
    def test_calculate_delay_past_end_date(self):
        """Test delay calculation with end date in the past."""
        start_date = datetime(2024, 1, 2, 0, 0, 0)
        end_date = datetime(2024, 1, 1, 0, 0, 0)
        total_users = 36
        
        with pytest.raises(ValueError, match="end_date must be after start_date"):
            self.calculator.calculate_delay(total_users, end_date, start_date)
    
    def test_validate_delay(self):
        """Test delay validation."""
        assert self.calculator.validate_delay(20.0) is True
        assert self.calculator.validate_delay(24.0) is True
        assert self.calculator.validate_delay(19.9) is False
        assert self.calculator.validate_delay(0.0) is False
    
    def test_estimate_completion_date(self):
        """Test completion date estimation."""
        start_date = datetime(2024, 1, 1, 0, 0, 0)
        total_users = 36  # 2 batches
        delay_hours = 20.0
        
        completion = self.calculator.estimate_completion_date(
            total_users, delay_hours, start_date
        )
        
        # Total time: 2 * 0.15 (send) + 1 * 20 (delay) = 20.3 hours
        expected = start_date + timedelta(hours=20.3)
        assert completion == expected
    
    def test_estimate_completion_date_single_batch(self):
        """Test completion date estimation for single batch."""
        start_date = datetime(2024, 1, 1, 0, 0, 0)
        total_users = 10  # 1 batch
        delay_hours = 20.0
        
        completion = self.calculator.estimate_completion_date(
            total_users, delay_hours, start_date
        )
        
        # Total time: 1 * 0.15 (send) = 0.15 hours
        expected = start_date + timedelta(hours=0.15)
        assert completion == expected
    
    def test_estimate_completion_date_no_start_date(self):
        """Test completion date estimation without explicit start date."""
        total_users = 36
        delay_hours = 20.0
        
        before = datetime.now()
        completion = self.calculator.estimate_completion_date(total_users, delay_hours)
        after = datetime.now()
        
        # Completion should be roughly 20.3 hours from now
        assert completion > before + timedelta(hours=20)
        assert completion < after + timedelta(hours=21)
    
    def test_estimate_completion_date_invalid_inputs(self):
        """Test completion date estimation with invalid inputs."""
        start_date = datetime(2024, 1, 1, 0, 0, 0)
        
        with pytest.raises(ValueError, match="total_users must be greater than 0"):
            self.calculator.estimate_completion_date(0, 20.0, start_date)
        
        with pytest.raises(ValueError, match="delay_hours must be non-negative"):
            self.calculator.estimate_completion_date(36, -5.0, start_date)
    
    def test_delay_result_str(self):
        """Test DelayResult string representation."""
        start_date = datetime(2024, 1, 1, 0, 0, 0)
        end_date = datetime(2024, 1, 3, 0, 0, 0)
        total_users = 54
        
        result = self.calculator.calculate_delay(total_users, end_date, start_date)
        result_str = str(result)
        
        assert "Delay:" in result_str
        assert "Batches:" in result_str
        assert "Estimated completion:" in result_str
    
    def test_large_user_count(self):
        """Test delay calculation with large user count."""
        start_date = datetime(2024, 1, 1, 0, 0, 0)
        end_date = datetime(2024, 2, 1, 0, 0, 0)  # 31 days
        total_users = 1000  # 56 batches
        
        result = self.calculator.calculate_delay(total_users, end_date, start_date)
        
        assert result.num_batches == 56  # ceil(1000 / 18)
        # With many batches, delay will be capped at 24 hours
        assert result.delay_hours <= MAX_DELAY_HOURS
    
    def test_batch_size_calculation(self):
        """Test that batch size is correctly used in calculations."""
        # Test with 17 users (1 batch)
        result = self.calculator.calculate_delay(
            17,
            datetime(2024, 1, 2, 0, 0, 0),
            datetime(2024, 1, 1, 0, 0, 0)
        )
        assert result.num_batches == 1
        
        # Test with 18 users (1 batch)
        result = self.calculator.calculate_delay(
            18,
            datetime(2024, 1, 2, 0, 0, 0),
            datetime(2024, 1, 1, 0, 0, 0)
        )
        assert result.num_batches == 1
        
        # Test with 19 users (2 batches)
        result = self.calculator.calculate_delay(
            19,
            datetime(2024, 1, 2, 0, 0, 0),
            datetime(2024, 1, 1, 0, 0, 0)
        )
        assert result.num_batches == 2
        
        # Test with 36 users (2 batches)
        result = self.calculator.calculate_delay(
            36,
            datetime(2024, 1, 2, 0, 0, 0),
            datetime(2024, 1, 1, 0, 0, 0)
        )
        assert result.num_batches == 2
        
        # Test with 37 users (3 batches)
        result = self.calculator.calculate_delay(
            37,
            datetime(2024, 1, 2, 0, 0, 0),
            datetime(2024, 1, 1, 0, 0, 0)
        )
        assert result.num_batches == 3
