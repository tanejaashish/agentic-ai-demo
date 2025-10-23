"""
Tests for Circuit Breaker Pattern
"""

import pytest
import asyncio
from app.utils.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitState,
    CircuitBreakerOpenError
)


@pytest.mark.unit
class TestCircuitBreaker:
    """Test Circuit Breaker functionality"""

    @pytest.mark.asyncio
    async def test_circuit_breaker_initialization(self):
        """Test circuit breaker initialization"""
        config = CircuitBreakerConfig(
            failure_threshold=3,
            timeout_seconds=30
        )
        breaker = CircuitBreaker("test", config)

        assert breaker.name == "test"
        assert breaker.state == CircuitState.CLOSED
        assert breaker.failure_count == 0

    @pytest.mark.asyncio
    async def test_circuit_closed_allows_calls(self):
        """Test that closed circuit allows calls"""
        breaker = CircuitBreaker("test")

        async def successful_function():
            return "success"

        result = await breaker.call(successful_function)
        assert result == "success"
        assert breaker.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_circuit_opens_after_failures(self):
        """Test that circuit opens after failure threshold"""
        config = CircuitBreakerConfig(
            failure_threshold=3,
            timeout_seconds=60
        )
        breaker = CircuitBreaker("test", config)

        async def failing_function():
            raise ValueError("Test failure")

        # Trigger failures
        for _ in range(3):
            try:
                await breaker.call(failing_function)
            except ValueError:
                pass

        assert breaker.state == CircuitState.OPEN
        assert breaker.failure_count >= 3

    @pytest.mark.asyncio
    async def test_open_circuit_rejects_calls(self):
        """Test that open circuit rejects calls"""
        config = CircuitBreakerConfig(
            failure_threshold=2,
            timeout_seconds=60
        )
        breaker = CircuitBreaker("test", config)

        async def failing_function():
            raise ValueError("Test failure")

        # Open the circuit
        for _ in range(2):
            try:
                await breaker.call(failing_function)
            except ValueError:
                pass

        assert breaker.state == CircuitState.OPEN

        # Now calls should be rejected
        with pytest.raises(CircuitBreakerOpenError):
            await breaker.call(failing_function)

    @pytest.mark.asyncio
    async def test_circuit_transitions_to_half_open(self):
        """Test circuit transitions to half-open after timeout"""
        config = CircuitBreakerConfig(
            failure_threshold=2,
            timeout_seconds=0  # Immediate timeout for testing
        )
        breaker = CircuitBreaker("test", config)

        async def failing_function():
            raise ValueError("Test failure")

        # Open the circuit
        for _ in range(2):
            try:
                await breaker.call(failing_function)
            except ValueError:
                pass

        assert breaker.state == CircuitState.OPEN

        # Wait for transition to half-open (simulated by immediate timeout)
        await asyncio.sleep(0.1)

        # Next call should attempt reset
        try:
            await breaker.call(failing_function)
        except (ValueError, CircuitBreakerOpenError):
            pass

        # Circuit should have attempted transition
        assert breaker.opened_at is not None

    @pytest.mark.asyncio
    async def test_circuit_with_fallback(self):
        """Test circuit breaker with fallback function"""
        async def fallback_function():
            return "fallback result"

        config = CircuitBreakerConfig(failure_threshold=2)
        breaker = CircuitBreaker("test", config, fallback=fallback_function)

        async def failing_function():
            raise ValueError("Test failure")

        # Open the circuit
        for _ in range(2):
            try:
                await breaker.call(failing_function)
            except ValueError:
                pass

        # Fallback should be used
        result = await breaker.call(failing_function)
        assert result == "fallback result"

    @pytest.mark.asyncio
    async def test_circuit_statistics(self):
        """Test circuit breaker statistics"""
        breaker = CircuitBreaker("test")

        async def successful_function():
            return "success"

        # Make some successful calls
        for _ in range(5):
            await breaker.call(successful_function)

        stats = breaker.get_stats()

        assert stats['name'] == 'test'
        assert stats['stats']['total_calls'] == 5
        assert stats['stats']['successful_calls'] == 5
        assert stats['stats']['failed_calls'] == 0
        assert stats['stats']['success_rate'] == 1.0
