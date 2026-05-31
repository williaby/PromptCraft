"""Secure random number generation utility for project-wide use.

This module provides cryptographically secure random number generation
that can be used across the entire PromptCraft project for security-sensitive
operations like jitter, sampling, and simulation.
"""

from collections.abc import Sequence
import secrets
from typing import Any, TypeVar


T = TypeVar("T")


class SecureRandom:
    """Cryptographically secure random number generator.

    This class provides a centralized, secure alternative to the standard
    `random` module for use in security-sensitive contexts. It uses the
    `secrets` module which is designed for cryptographic use.

    Example:
        >>> secure_rng = SecureRandom()
        >>> jitter_factor = secure_rng.uniform(0.5, 1.5)
        >>> should_fail = secure_rng.random() < 0.1
    """

    def __init__(self) -> None:
        """Initialize secure random number generator."""
        self._rng = secrets.SystemRandom()

    def random(self) -> float:
        """Generate cryptographically secure random float between 0.0 and 1.0.

        Returns:
            float: Random float in range [0.0, 1.0).
        """
        return self._rng.random()

    def uniform(self, low: float, high: float) -> float:
        """Generate cryptographically secure uniform random float.

        Args:
            low (float): Lower bound (inclusive).
            high (float): Upper bound (exclusive).

        Returns:
            float: Random float in range [low, high).

        Raises:
            ValueError: If low >= high.
        """
        if low >= high:
            raise ValueError("low must be less than high")
        return self._rng.uniform(low, high)

    def randint(self, low: int, high: int) -> int:
        """Generate cryptographically secure random integer.

        Args:
            low (int): Lower bound (inclusive).
            high (int): Upper bound (inclusive).

        Returns:
            int: Random integer in range [low, high].

        Raises:
            ValueError: If low > high.
        """
        if low > high:
            raise ValueError("low must be less than or equal to high")
        return self._rng.randint(low, high)

    def choice(self, sequence: Sequence[T]) -> T:
        """Choose cryptographically secure random element from sequence.

        Args:
            sequence (Sequence[T]): Non-empty sequence to choose from.

        Returns:
            T: Random element from sequence.

        Raises:
            IndexError: If sequence is empty.
        """
        if not sequence:
            raise IndexError("Cannot choose from empty sequence")
        return self._rng.choice(sequence)

    def sample(self, population: Sequence[T], k: int) -> list[T]:
        """Choose k unique cryptographically secure random elements.

        Args:
            population (Sequence[T]): Sequence to sample from.
            k (int): Number of elements to sample.

        Returns:
            list[T]: List of k unique random elements.

        Raises:
            ValueError: If k > len(population).
        """
        if k > len(population):
            raise ValueError("Sample size cannot exceed population size")
        return self._rng.sample(population, k)

    def shuffle(self, sequence: list[Any]) -> None:
        """Shuffle list in place using cryptographically secure randomness.

        Args:
            sequence (list[Any]): List to shuffle in place.
        """
        self._rng.shuffle(sequence)

    def bytes(self, n: int) -> bytes:
        """Generate n cryptographically secure random bytes.

        Args:
            n (int): Number of bytes to generate.

        Returns:
            bytes: Random bytes.

        Raises:
            ValueError: If n < 0.
        """
        if n < 0:
            raise ValueError("Number of bytes must be non-negative")
        return secrets.token_bytes(n)

    def hex(self, n: int) -> str:
        """Generate cryptographically secure random hex string.

        Args:
            n (int): Number of bytes to use for hex generation.

        Returns:
            str: Random hex string of length 2*n.

        Raises:
            ValueError: If n < 0.
        """
        if n < 0:
            raise ValueError("Number of bytes must be non-negative")
        return secrets.token_hex(n)

    def jitter(self, value: float, factor: float = 0.1) -> float:
        """Apply cryptographically secure jitter to a value.

        Args:
            value (float): Base value to apply jitter to.
            factor (float): Jitter factor (0.1 means ±10% jitter).

        Returns:
            float: Value with jitter applied.

        Raises:
            ValueError: If factor < 0 or factor > 1.
        """
        if not 0 <= factor <= 1:
            raise ValueError("Jitter factor must be between 0 and 1")

        if factor == 0:
            return value

        # Apply jitter: value * (1 ± factor)
        min_multiplier = 1 - factor
        max_multiplier = 1 + factor
        multiplier = self.uniform(min_multiplier, max_multiplier)

        return value * multiplier

    def exponential_backoff_jitter(
        self,
        base_delay: float,
        attempt: int,
        max_delay: float = 60.0,
    ) -> float:
        """Calculate exponential backoff delay with secure jitter.

        Args:
            base_delay (float): Base delay in seconds.
            attempt (int): Attempt number (0-based).
            max_delay (float): Maximum delay in seconds.

        Returns:
            float: Delay with exponential backoff and jitter applied.

        Raises:
            ValueError: If parameters are invalid.
        """
        if base_delay <= 0:
            raise ValueError("base_delay must be positive")
        if attempt < 0:
            raise ValueError("attempt must be non-negative")
        if max_delay <= 0:
            raise ValueError("max_delay must be positive")

        # Limit attempt to prevent overflow
        safe_attempt = min(attempt, 10)

        # Calculate exponential delay
        delay = base_delay * (2**safe_attempt)
        delay = min(delay, max_delay)

        # Apply jitter (±25%)
        return self.jitter(delay, 0.25)


# Global instance for convenient access
secure_random = SecureRandom()


def get_secure_random() -> SecureRandom:
    """Get the global secure random instance.

    Returns:
        SecureRandom: Global SecureRandom instance.
    """
    return secure_random


# Convenience functions for common operations
def secure_jitter(value: float, factor: float = 0.1) -> float:
    """Apply secure jitter to a value using global instance.

    Args:
        value (float): Base value to apply jitter to.
        factor (float): Jitter factor (0.1 means ±10% jitter).

    Returns:
        float: Value with jitter applied.
    """
    return secure_random.jitter(value, factor)


def secure_uniform(low: float, high: float) -> float:
    """Generate secure uniform random float using global instance.

    Args:
        low (float): Lower bound (inclusive).
        high (float): Upper bound (exclusive).

    Returns:
        float: Random float in range [low, high).
    """
    return secure_random.uniform(low, high)


def secure_choice(sequence: Sequence[T]) -> T:
    """Choose secure random element using global instance.

    Args:
        sequence (Sequence[T]): Non-empty sequence to choose from.

    Returns:
        T: Random element from sequence.
    """
    return secure_random.choice(sequence)
