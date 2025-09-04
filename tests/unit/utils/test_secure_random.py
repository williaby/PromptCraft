"""Tests for secure_random utility module.

Tests the cryptographically secure random number generation utility
using minimal mocking and actual functionality testing.
"""

import secrets
from unittest.mock import patch

import pytest

from src.utils.secure_random import (
    SecureRandom,
    get_secure_random,
    secure_choice,
    secure_jitter,
    secure_random,
    secure_uniform,
)


class TestSecureRandom:
    """Test SecureRandom class functionality."""

    def setup_method(self):
        """Setup test fixtures."""
        self.rng = SecureRandom()

    def test_init_creates_system_random(self):
        """Test that initialization creates SystemRandom instance."""
        assert hasattr(self.rng, "_rng")
        assert isinstance(self.rng._rng, secrets.SystemRandom)

    def test_random_returns_float_in_range(self):
        """Test random() returns float in [0.0, 1.0) range."""
        # Test multiple values to ensure range consistency
        for _ in range(100):
            value = self.rng.random()
            assert isinstance(value, float)
            assert 0.0 <= value < 1.0

    def test_uniform_valid_range(self):
        """Test uniform() with valid range parameters."""
        low, high = 5.0, 10.0

        # Test multiple values to ensure range consistency
        for _ in range(100):
            value = self.rng.uniform(low, high)
            assert isinstance(value, float)
            assert low <= value < high

    def test_uniform_equal_bounds_edge_case(self):
        """Test uniform() behavior when low equals high."""
        with pytest.raises(ValueError, match="low must be less than high"):
            self.rng.uniform(5.0, 5.0)

    def test_uniform_invalid_range(self):
        """Test uniform() raises error for invalid range."""
        with pytest.raises(ValueError, match="low must be less than high"):
            self.rng.uniform(10.0, 5.0)

    def test_uniform_negative_values(self):
        """Test uniform() works with negative values."""
        value = self.rng.uniform(-10.0, -5.0)
        assert -10.0 <= value < -5.0

    def test_randint_valid_range(self):
        """Test randint() with valid range parameters."""
        low, high = 1, 10

        # Test multiple values to ensure range consistency
        for _ in range(100):
            value = self.rng.randint(low, high)
            assert isinstance(value, int)
            assert low <= value <= high

    def test_randint_equal_bounds(self):
        """Test randint() when low equals high."""
        value = self.rng.randint(5, 5)
        assert value == 5

    def test_randint_invalid_range(self):
        """Test randint() raises error for invalid range."""
        with pytest.raises(ValueError, match="low must be less than or equal to high"):
            self.rng.randint(10, 5)

    def test_randint_negative_values(self):
        """Test randint() works with negative values."""
        value = self.rng.randint(-10, -5)
        assert -10 <= value <= -5

    def test_choice_valid_sequence(self):
        """Test choice() with valid sequence."""
        sequence = ["a", "b", "c", "d", "e"]

        # Test multiple choices to ensure all elements can be selected
        choices = [self.rng.choice(sequence) for _ in range(100)]
        assert all(choice in sequence for choice in choices)

        # Verify we get different choices (probabilistic test)
        unique_choices = set(choices)
        assert len(unique_choices) > 1  # Should get multiple different choices

    def test_choice_single_element(self):
        """Test choice() with single-element sequence."""
        sequence = ["only_element"]
        value = self.rng.choice(sequence)
        assert value == "only_element"

    def test_choice_empty_sequence(self):
        """Test choice() raises error for empty sequence."""
        with pytest.raises(IndexError, match="Cannot choose from empty sequence"):
            self.rng.choice([])

    def test_choice_different_types(self):
        """Test choice() works with different sequence types."""
        # Test with tuple
        value = self.rng.choice((1, 2, 3))
        assert value in (1, 2, 3)

        # Test with string
        value = self.rng.choice("abc")
        assert value in "abc"

    def test_sample_valid_parameters(self):
        """Test sample() with valid parameters."""
        population = ["a", "b", "c", "d", "e"]
        k = 3

        sample = self.rng.sample(population, k)

        assert len(sample) == k
        assert all(item in population for item in sample)
        assert len(set(sample)) == k  # All elements should be unique

    def test_sample_full_population(self):
        """Test sample() with k equal to population size."""
        population = ["a", "b", "c"]
        sample = self.rng.sample(population, 3)

        assert len(sample) == 3
        assert set(sample) == set(population)

    def test_sample_zero_elements(self):
        """Test sample() with k=0."""
        population = ["a", "b", "c"]
        sample = self.rng.sample(population, 0)

        assert sample == []

    def test_sample_invalid_size(self):
        """Test sample() raises error when k > population size."""
        population = ["a", "b", "c"]

        with pytest.raises(ValueError, match="Sample size cannot exceed population size"):
            self.rng.sample(population, 5)

    def test_shuffle_modifies_list_in_place(self):
        """Test shuffle() modifies list in place."""
        original = [1, 2, 3, 4, 5]
        sequence = original.copy()

        self.rng.shuffle(sequence)

        # List should have same elements but potentially different order
        assert set(sequence) == set(original)
        assert len(sequence) == len(original)

        # For a reasonable test, shuffle multiple times and ensure we get different orders
        orders = []
        for _ in range(10):
            test_sequence = [1, 2, 3, 4, 5]
            self.rng.shuffle(test_sequence)
            orders.append(tuple(test_sequence))

        # Should get at least some different orders
        unique_orders = set(orders)
        assert len(unique_orders) > 1

    def test_shuffle_empty_list(self):
        """Test shuffle() with empty list."""
        sequence = []
        self.rng.shuffle(sequence)  # Should not raise error
        assert sequence == []

    def test_shuffle_single_element(self):
        """Test shuffle() with single-element list."""
        sequence = [42]
        self.rng.shuffle(sequence)
        assert sequence == [42]

    def test_bytes_valid_size(self):
        """Test bytes() generates correct number of bytes."""
        for n in [0, 1, 16, 32, 256]:
            result = self.rng.bytes(n)
            assert isinstance(result, bytes)
            assert len(result) == n

    def test_bytes_randomness(self):
        """Test bytes() generates different values."""
        # Generate multiple byte sequences and ensure they're different
        byte_sequences = [self.rng.bytes(16) for _ in range(10)]
        unique_sequences = set(byte_sequences)

        # Should get different sequences (very high probability)
        assert len(unique_sequences) == len(byte_sequences)

    def test_bytes_negative_size(self):
        """Test bytes() raises error for negative size."""
        with pytest.raises(ValueError, match="Number of bytes must be non-negative"):
            self.rng.bytes(-1)

    def test_hex_valid_size(self):
        """Test hex() generates correct length hex string."""
        for n in [0, 1, 8, 16, 32]:
            result = self.rng.hex(n)
            assert isinstance(result, str)
            assert len(result) == 2 * n  # Hex string is 2 characters per byte

            if n > 0:
                # Verify it's valid hex
                int(result, 16)  # Should not raise ValueError

    def test_hex_randomness(self):
        """Test hex() generates different values."""
        hex_strings = [self.rng.hex(16) for _ in range(10)]
        unique_strings = set(hex_strings)

        # Should get different hex strings
        assert len(unique_strings) == len(hex_strings)

    def test_hex_negative_size(self):
        """Test hex() raises error for negative size."""
        with pytest.raises(ValueError, match="Number of bytes must be non-negative"):
            self.rng.hex(-1)

    def test_jitter_default_factor(self):
        """Test jitter() with default factor."""
        base_value = 10.0

        # Test multiple values to check range
        jittered_values = [self.rng.jitter(base_value) for _ in range(100)]

        # With default factor 0.1, values should be in range [9.0, 11.0)
        expected_min = base_value * 0.9
        expected_max = base_value * 1.1

        for value in jittered_values:
            assert expected_min <= value < expected_max

        # Should get different values
        assert len(set(jittered_values)) > 10

    def test_jitter_custom_factor(self):
        """Test jitter() with custom factor."""
        base_value = 20.0
        factor = 0.25  # ±25%

        jittered_value = self.rng.jitter(base_value, factor)

        # Should be in range [15.0, 25.0)
        expected_min = base_value * 0.75
        expected_max = base_value * 1.25

        assert expected_min <= jittered_value < expected_max

    def test_jitter_zero_factor(self):
        """Test jitter() with zero factor returns original value."""
        base_value = 42.0
        result = self.rng.jitter(base_value, 0.0)
        assert result == base_value

    def test_jitter_invalid_factor(self):
        """Test jitter() raises error for invalid factor."""
        base_value = 10.0

        # Test negative factor
        with pytest.raises(ValueError, match="Jitter factor must be between 0 and 1"):
            self.rng.jitter(base_value, -0.1)

        # Test factor > 1
        with pytest.raises(ValueError, match="Jitter factor must be between 0 and 1"):
            self.rng.jitter(base_value, 1.5)

    def test_jitter_with_negative_value(self):
        """Test jitter() works with negative base values."""
        base_value = -10.0
        factor = 0.1

        jittered_value = self.rng.jitter(base_value, factor)

        # For negative values, the range is [-11.0, -9.0)
        expected_min = base_value * 1.1  # More negative
        expected_max = base_value * 0.9  # Less negative

        assert expected_min <= jittered_value < expected_max

    def test_exponential_backoff_jitter_basic(self):
        """Test exponential_backoff_jitter() basic functionality."""
        base_delay = 1.0
        attempt = 2

        delay = self.rng.exponential_backoff_jitter(base_delay, attempt)

        # For attempt 2, base delay would be 1.0 * 2^2 = 4.0
        # With 25% jitter, range is [3.0, 5.0)
        expected_base = base_delay * (2**attempt)
        expected_min = expected_base * 0.75
        expected_max = expected_base * 1.25

        assert expected_min <= delay < expected_max

    def test_exponential_backoff_jitter_max_delay_capping(self):
        """Test exponential_backoff_jitter() respects max_delay."""
        base_delay = 1.0
        attempt = 10  # Would normally result in very large delay
        max_delay = 30.0

        delay = self.rng.exponential_backoff_jitter(base_delay, attempt, max_delay)

        # Should be capped at max_delay with jitter
        # Max possible with 25% jitter is max_delay * 1.25
        assert delay <= max_delay * 1.25

    def test_exponential_backoff_jitter_attempt_limiting(self):
        """Test exponential_backoff_jitter() limits attempt to prevent overflow."""
        base_delay = 1.0
        huge_attempt = 100  # Would cause overflow
        max_delay = 1000.0

        # Should not raise overflow error
        delay = self.rng.exponential_backoff_jitter(base_delay, huge_attempt, max_delay)
        assert isinstance(delay, float)
        assert delay <= max_delay * 1.25

    def test_exponential_backoff_jitter_invalid_parameters(self):
        """Test exponential_backoff_jitter() raises errors for invalid parameters."""
        # Negative base_delay
        with pytest.raises(ValueError, match="base_delay must be positive"):
            self.rng.exponential_backoff_jitter(-1.0, 1)

        # Zero base_delay
        with pytest.raises(ValueError, match="base_delay must be positive"):
            self.rng.exponential_backoff_jitter(0.0, 1)

        # Negative attempt
        with pytest.raises(ValueError, match="attempt must be non-negative"):
            self.rng.exponential_backoff_jitter(1.0, -1)

        # Negative max_delay
        with pytest.raises(ValueError, match="max_delay must be positive"):
            self.rng.exponential_backoff_jitter(1.0, 1, -30.0)

        # Zero max_delay
        with pytest.raises(ValueError, match="max_delay must be positive"):
            self.rng.exponential_backoff_jitter(1.0, 1, 0.0)

    def test_exponential_backoff_jitter_attempt_zero(self):
        """Test exponential_backoff_jitter() with attempt=0."""
        base_delay = 2.0

        delay = self.rng.exponential_backoff_jitter(base_delay, 0)

        # For attempt 0, delay should be base_delay * 2^0 = base_delay
        # With 25% jitter: [1.5, 2.5)
        expected_min = base_delay * 0.75
        expected_max = base_delay * 1.25

        assert expected_min <= delay < expected_max


class TestGlobalFunctions:
    """Test global convenience functions."""

    def test_get_secure_random_returns_global_instance(self):
        """Test get_secure_random() returns the global instance."""
        instance = get_secure_random()
        assert instance is secure_random
        assert isinstance(instance, SecureRandom)

    def test_secure_jitter_uses_global_instance(self):
        """Test secure_jitter() uses global instance."""
        base_value = 10.0
        factor = 0.2

        # Mock global instance to verify it's used
        with patch.object(secure_random, "jitter", return_value=42.0) as mock_jitter:
            result = secure_jitter(base_value, factor)

            mock_jitter.assert_called_once_with(base_value, factor)
            assert result == 42.0

    def test_secure_jitter_default_factor(self):
        """Test secure_jitter() with default factor."""
        base_value = 15.0

        # Test that it produces values in expected range
        result = secure_jitter(base_value)

        # Default factor is 0.1, so range is [13.5, 16.5)
        expected_min = base_value * 0.9
        expected_max = base_value * 1.1

        assert expected_min <= result < expected_max

    def test_secure_uniform_uses_global_instance(self):
        """Test secure_uniform() uses global instance."""
        low, high = 5.0, 10.0

        with patch.object(secure_random, "uniform", return_value=7.5) as mock_uniform:
            result = secure_uniform(low, high)

            mock_uniform.assert_called_once_with(low, high)
            assert result == 7.5

    def test_secure_uniform_functionality(self):
        """Test secure_uniform() actual functionality."""
        low, high = 1.0, 5.0

        # Test multiple values to ensure range consistency
        for _ in range(50):
            result = secure_uniform(low, high)
            assert low <= result < high

    def test_secure_choice_uses_global_instance(self):
        """Test secure_choice() uses global instance."""
        sequence = ["a", "b", "c"]

        with patch.object(secure_random, "choice", return_value="b") as mock_choice:
            result = secure_choice(sequence)

            mock_choice.assert_called_once_with(sequence)
            assert result == "b"

    def test_secure_choice_functionality(self):
        """Test secure_choice() actual functionality."""
        sequence = [1, 2, 3, 4, 5]

        # Test multiple choices
        choices = [secure_choice(sequence) for _ in range(50)]

        assert all(choice in sequence for choice in choices)
        # Should get multiple different choices (probabilistic)
        assert len(set(choices)) > 1


class TestSecureRandomIntegration:
    """Integration tests for SecureRandom."""

    def test_multiple_instances_independent(self):
        """Test that multiple instances are independent."""
        rng1 = SecureRandom()
        rng2 = SecureRandom()

        # Generate random values from both
        values1 = [rng1.random() for _ in range(10)]
        values2 = [rng2.random() for _ in range(10)]

        # Should get different sequences (very high probability)
        assert values1 != values2

    def test_global_instance_consistency(self):
        """Test that global instance is consistent."""
        instance1 = get_secure_random()
        instance2 = get_secure_random()

        assert instance1 is instance2  # Same object
        assert instance1 is secure_random

    def test_cryptographic_quality_basic(self):
        """Test basic cryptographic quality of generated values."""
        rng = SecureRandom()

        # Generate a large number of random bytes
        data = rng.bytes(1000)

        # Basic randomness checks
        assert len(set(data)) > 200  # Should have good byte distribution

        # Check that we don't get obvious patterns
        consecutive_zeros = 0
        max_consecutive_zeros = 0

        for byte in data:
            if byte == 0:
                consecutive_zeros += 1
                max_consecutive_zeros = max(max_consecutive_zeros, consecutive_zeros)
            else:
                consecutive_zeros = 0

        # Shouldn't have too many consecutive zeros
        assert max_consecutive_zeros < 10

    def test_performance_reasonable(self):
        """Test that performance is reasonable for typical usage."""
        import time

        rng = SecureRandom()

        # Time generation of random numbers
        start_time = time.time()

        for _ in range(1000):
            rng.random()
            rng.randint(1, 100)
            rng.uniform(0.0, 1.0)

        elapsed_time = time.time() - start_time

        # Should complete 3000 operations in reasonable time (< 1 second)
        assert elapsed_time < 1.0

    def test_jitter_distribution(self):
        """Test that jitter produces reasonable distribution."""
        rng = SecureRandom()
        base_value = 100.0
        factor = 0.2  # ±20%

        # Generate many jittered values
        jittered_values = [rng.jitter(base_value, factor) for _ in range(1000)]

        # Calculate statistics
        mean_value = sum(jittered_values) / len(jittered_values)
        min_value = min(jittered_values)
        max_value = max(jittered_values)

        # Mean should be close to base value
        assert abs(mean_value - base_value) < 5.0  # Within 5% of base

        # Range should be approximately correct
        expected_min = base_value * 0.8
        expected_max = base_value * 1.2

        assert min_value >= expected_min
        assert max_value < expected_max

        # Should have good spread
        assert max_value - min_value > base_value * 0.3
