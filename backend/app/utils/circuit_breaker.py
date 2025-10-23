"""
Circuit Breaker Pattern Implementation
Prevents cascading failures and provides graceful degradation
"""

import asyncio
import time
from typing import Callable, Any, Optional, Dict, TypeVar, Generic
from enum import Enum
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
from functools import wraps

logger = logging.getLogger(__name__)

T = TypeVar('T')


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"        # Normal operation
    OPEN = "open"            # Failures threshold reached, rejecting calls
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker"""
    failure_threshold: int = 5          # Number of failures before opening
    success_threshold: int = 2          # Number of successes to close from half-open
    timeout_seconds: int = 60           # Timeout before attempting reset
    expected_exception: type = Exception # Exception type to catch
    exclude_exceptions: tuple = ()       # Exceptions to not count as failures
    half_open_max_calls: int = 3        # Max calls allowed in half-open state


@dataclass
class CircuitStats:
    """Statistics for circuit breaker"""
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    rejected_calls: int = 0
    last_failure_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None
    state_changes: int = 0


class CircuitBreaker(Generic[T]):
    """
    Circuit Breaker implementation for async functions

    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Failure threshold reached, requests are rejected
    - HALF_OPEN: Testing if service recovered, limited requests allowed

    Usage:
        breaker = CircuitBreaker(config)
        result = await breaker.call(some_async_function, arg1, arg2)
    """

    def __init__(
        self,
        name: str,
        config: Optional[CircuitBreakerConfig] = None,
        fallback: Optional[Callable] = None
    ):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.fallback = fallback

        # State management
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.half_open_calls = 0
        self.last_failure_time: Optional[float] = None
        self.opened_at: Optional[float] = None

        # Statistics
        self.stats = CircuitStats()

        # Lock for thread safety
        self._lock = asyncio.Lock()

        logger.info(f"Circuit breaker '{name}' initialized in {self.state.value} state")

    async def call(self, func: Callable[..., T], *args, **kwargs) -> T:
        """
        Execute function with circuit breaker protection

        Args:
            func: Async function to execute
            *args: Positional arguments for function
            **kwargs: Keyword arguments for function

        Returns:
            Function result or fallback result

        Raises:
            CircuitBreakerOpenError: If circuit is open and no fallback
        """
        async with self._lock:
            self.stats.total_calls += 1

            # Check if we should reject the call
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self._transition_to_half_open()
                else:
                    self.stats.rejected_calls += 1
                    logger.warning(
                        f"Circuit breaker '{self.name}' is OPEN, "
                        f"rejecting call (failures: {self.failure_count})"
                    )
                    return await self._handle_rejection()

            # In half-open state, limit concurrent calls
            if self.state == CircuitState.HALF_OPEN:
                if self.half_open_calls >= self.config.half_open_max_calls:
                    self.stats.rejected_calls += 1
                    logger.warning(
                        f"Circuit breaker '{self.name}' HALF_OPEN limit reached, "
                        "rejecting call"
                    )
                    return await self._handle_rejection()

                self.half_open_calls += 1

        # Execute the function
        try:
            result = await self._execute(func, *args, **kwargs)
            await self._on_success()
            return result

        except Exception as e:
            # Check if exception should be excluded
            if isinstance(e, self.config.exclude_exceptions):
                logger.debug(f"Circuit breaker '{self.name}' ignoring excluded exception: {type(e)}")
                raise

            # Count as failure
            await self._on_failure(e)

            # If fallback available, use it
            if self.fallback:
                logger.info(f"Circuit breaker '{self.name}' using fallback after failure")
                return await self._execute_fallback(*args, **kwargs)

            raise

    async def _execute(self, func: Callable[..., T], *args, **kwargs) -> T:
        """Execute the protected function"""
        if asyncio.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        else:
            # Run sync function in executor
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, func, *args, **kwargs)

    async def _execute_fallback(self, *args, **kwargs) -> Any:
        """Execute fallback function"""
        if self.fallback:
            if asyncio.iscoroutinefunction(self.fallback):
                return await self.fallback(*args, **kwargs)
            else:
                loop = asyncio.get_event_loop()
                return await loop.run_in_executor(None, self.fallback, *args, **kwargs)
        return None

    async def _on_success(self):
        """Handle successful call"""
        async with self._lock:
            self.stats.successful_calls += 1
            self.stats.last_success_time = datetime.now()

            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                self.half_open_calls -= 1

                logger.info(
                    f"Circuit breaker '{self.name}' successful call in HALF_OPEN "
                    f"({self.success_count}/{self.config.success_threshold})"
                )

                if self.success_count >= self.config.success_threshold:
                    self._transition_to_closed()

            elif self.state == CircuitState.CLOSED:
                # Reset failure count on success
                self.failure_count = 0

    async def _on_failure(self, exception: Exception):
        """Handle failed call"""
        async with self._lock:
            self.stats.failed_calls += 1
            self.stats.last_failure_time = datetime.now()
            self.last_failure_time = time.time()

            logger.warning(
                f"Circuit breaker '{self.name}' call failed: {type(exception).__name__}: {str(exception)}"
            )

            if self.state == CircuitState.HALF_OPEN:
                self.half_open_calls -= 1
                # Any failure in half-open state reopens the circuit
                self._transition_to_open()

            elif self.state == CircuitState.CLOSED:
                self.failure_count += 1

                if self.failure_count >= self.config.failure_threshold:
                    self._transition_to_open()

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        if self.opened_at is None:
            return True

        elapsed = time.time() - self.opened_at
        return elapsed >= self.config.timeout_seconds

    async def _handle_rejection(self) -> Any:
        """Handle rejected call (circuit is open)"""
        if self.fallback:
            logger.info(f"Circuit breaker '{self.name}' using fallback (circuit OPEN)")
            return await self._execute_fallback()

        raise CircuitBreakerOpenError(
            f"Circuit breaker '{self.name}' is OPEN "
            f"(failures: {self.failure_count}, "
            f"threshold: {self.config.failure_threshold})"
        )

    def _transition_to_open(self):
        """Transition circuit to OPEN state"""
        self.state = CircuitState.OPEN
        self.opened_at = time.time()
        self.stats.state_changes += 1

        logger.error(
            f"Circuit breaker '{self.name}' transitioned to OPEN state "
            f"(failures: {self.failure_count}, threshold: {self.config.failure_threshold})"
        )

    def _transition_to_half_open(self):
        """Transition circuit to HALF_OPEN state"""
        self.state = CircuitState.HALF_OPEN
        self.success_count = 0
        self.half_open_calls = 0
        self.stats.state_changes += 1

        logger.info(
            f"Circuit breaker '{self.name}' transitioned to HALF_OPEN state "
            f"(attempting recovery after {self.config.timeout_seconds}s timeout)"
        )

    def _transition_to_closed(self):
        """Transition circuit to CLOSED state"""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.half_open_calls = 0
        self.opened_at = None
        self.stats.state_changes += 1

        logger.info(
            f"Circuit breaker '{self.name}' transitioned to CLOSED state (recovered)"
        )

    async def reset(self):
        """Manually reset circuit breaker to CLOSED state"""
        async with self._lock:
            self._transition_to_closed()
            logger.info(f"Circuit breaker '{self.name}' manually reset")

    def get_state(self) -> CircuitState:
        """Get current state"""
        return self.state

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics"""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "stats": {
                "total_calls": self.stats.total_calls,
                "successful_calls": self.stats.successful_calls,
                "failed_calls": self.stats.failed_calls,
                "rejected_calls": self.stats.rejected_calls,
                "success_rate": (
                    self.stats.successful_calls / self.stats.total_calls
                    if self.stats.total_calls > 0 else 0.0
                ),
                "failure_rate": (
                    self.stats.failed_calls / self.stats.total_calls
                    if self.stats.total_calls > 0 else 0.0
                ),
                "rejection_rate": (
                    self.stats.rejected_calls / self.stats.total_calls
                    if self.stats.total_calls > 0 else 0.0
                ),
                "last_failure_time": (
                    self.stats.last_failure_time.isoformat()
                    if self.stats.last_failure_time else None
                ),
                "last_success_time": (
                    self.stats.last_success_time.isoformat()
                    if self.stats.last_success_time else None
                ),
                "state_changes": self.stats.state_changes
            },
            "config": {
                "failure_threshold": self.config.failure_threshold,
                "success_threshold": self.config.success_threshold,
                "timeout_seconds": self.config.timeout_seconds
            }
        }

    def is_closed(self) -> bool:
        """Check if circuit is closed (normal operation)"""
        return self.state == CircuitState.CLOSED

    def is_open(self) -> bool:
        """Check if circuit is open (rejecting calls)"""
        return self.state == CircuitState.OPEN

    def is_half_open(self) -> bool:
        """Check if circuit is half-open (testing recovery)"""
        return self.state == CircuitState.HALF_OPEN


class CircuitBreakerOpenError(Exception):
    """Exception raised when circuit breaker is open"""
    pass


class CircuitBreakerManager:
    """
    Manages multiple circuit breakers
    """

    def __init__(self):
        self.breakers: Dict[str, CircuitBreaker] = {}
        logger.info("Circuit Breaker Manager initialized")

    def create_breaker(
        self,
        name: str,
        config: Optional[CircuitBreakerConfig] = None,
        fallback: Optional[Callable] = None
    ) -> CircuitBreaker:
        """Create and register a circuit breaker"""
        breaker = CircuitBreaker(name, config, fallback)
        self.breakers[name] = breaker
        logger.info(f"Created circuit breaker: {name}")
        return breaker

    def get_breaker(self, name: str) -> Optional[CircuitBreaker]:
        """Get circuit breaker by name"""
        return self.breakers.get(name)

    async def reset_all(self):
        """Reset all circuit breakers"""
        for breaker in self.breakers.values():
            await breaker.reset()
        logger.info("All circuit breakers reset")

    def get_all_stats(self) -> Dict[str, Any]:
        """Get statistics for all circuit breakers"""
        return {
            name: breaker.get_stats()
            for name, breaker in self.breakers.items()
        }

    def get_health_summary(self) -> Dict[str, Any]:
        """Get overall health summary"""
        total_breakers = len(self.breakers)
        closed = sum(1 for b in self.breakers.values() if b.is_closed())
        open_breakers = sum(1 for b in self.breakers.values() if b.is_open())
        half_open = sum(1 for b in self.breakers.values() if b.is_half_open())

        return {
            "total_breakers": total_breakers,
            "closed": closed,
            "open": open_breakers,
            "half_open": half_open,
            "health_percentage": (closed / total_breakers * 100) if total_breakers > 0 else 100.0,
            "breaker_states": {
                name: breaker.get_state().value
                for name, breaker in self.breakers.items()
            }
        }


# Global circuit breaker manager
_global_manager: Optional[CircuitBreakerManager] = None


def get_circuit_breaker_manager() -> CircuitBreakerManager:
    """Get or create global circuit breaker manager"""
    global _global_manager
    if _global_manager is None:
        _global_manager = CircuitBreakerManager()
    return _global_manager


def circuit_breaker(
    name: str,
    failure_threshold: int = 5,
    timeout_seconds: int = 60,
    fallback: Optional[Callable] = None
):
    """
    Decorator to apply circuit breaker to a function

    Usage:
        @circuit_breaker("my_service", failure_threshold=3, timeout_seconds=30)
        async def call_external_service():
            ...
    """
    def decorator(func):
        manager = get_circuit_breaker_manager()

        # Create circuit breaker for this function
        config = CircuitBreakerConfig(
            failure_threshold=failure_threshold,
            timeout_seconds=timeout_seconds
        )
        breaker = manager.create_breaker(name, config, fallback)

        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await breaker.call(func, *args, **kwargs)

        wrapper.circuit_breaker = breaker
        return wrapper

    return decorator
