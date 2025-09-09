"""Retry and circuit breaker utilities for HomeyPro MCP Server."""

import asyncio
import time
from typing import Any, Callable, Dict, Optional, TypeVar
from functools import wraps
from enum import Enum
from dataclasses import dataclass

from ..exceptions import HomeyConnectionError, HomeyTimeoutError
from .logging import get_logger

logger = get_logger(__name__)

T = TypeVar('T')


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"        # Normal operation
    OPEN = "open"            # Circuit is open, requests fail fast
    HALF_OPEN = "half_open"  # Testing if service is back up


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""
    failure_threshold: int = 5      # Number of failures before opening
    recovery_timeout: int = 60      # Seconds before trying half-open
    success_threshold: int = 3      # Successes needed in half-open to close
    timeout: float = 30.0           # Request timeout


class CircuitBreaker:
    """Circuit breaker implementation for resilient API calls."""
    
    def __init__(self, name: str, config: Optional[CircuitBreakerConfig] = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = 0.0
        self.logger = get_logger(f"{__name__}.{name}")
    
    def _should_attempt_call(self) -> bool:
        """Determine if a call should be attempted based on circuit state."""
        if self.state == CircuitState.CLOSED:
            return True
        
        if self.state == CircuitState.OPEN:
            # Check if enough time has passed to try half-open
            if time.time() - self.last_failure_time >= self.config.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
                self.logger.info(f"Circuit breaker {self.name} moving to HALF_OPEN")
                return True
            return False
        
        # HALF_OPEN state
        return True
    
    def _record_success(self):
        """Record a successful call."""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.logger.info(f"Circuit breaker {self.name} moved to CLOSED")
        elif self.state == CircuitState.CLOSED:
            # Reset failure count on success
            self.failure_count = 0
    
    def _record_failure(self):
        """Record a failed call."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.state == CircuitState.CLOSED:
            if self.failure_count >= self.config.failure_threshold:
                self.state = CircuitState.OPEN
                self.logger.warning(f"Circuit breaker {self.name} moved to OPEN after {self.failure_count} failures")
        elif self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.OPEN
            self.logger.warning(f"Circuit breaker {self.name} moved back to OPEN from HALF_OPEN")
    
    async def call(self, func: Callable[[], Any]) -> Any:
        """Execute a function call through the circuit breaker."""
        if not self._should_attempt_call():
            raise HomeyConnectionError(
                f"Circuit breaker {self.name} is OPEN",
                details={"state": self.state.value, "last_failure_time": self.last_failure_time}
            )
        
        try:
            # Execute the function with timeout
            result = await asyncio.wait_for(func(), timeout=self.config.timeout)
            self._record_success()
            return result
        
        except (ConnectionError, TimeoutError, asyncio.TimeoutError) as e:
            self._record_failure()
            if isinstance(e, asyncio.TimeoutError):
                raise HomeyTimeoutError(f"Request timed out after {self.config.timeout}s")
            else:
                raise HomeyConnectionError(str(e))
        
        except Exception as e:
            # Don't count non-network errors as circuit breaker failures
            self.logger.debug(f"Non-network error in circuit breaker: {e}")
            raise
    
    def get_status(self) -> Dict[str, Any]:
        """Get current circuit breaker status."""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure_time": self.last_failure_time,
            "config": {
                "failure_threshold": self.config.failure_threshold,
                "recovery_timeout": self.config.recovery_timeout,
                "success_threshold": self.config.success_threshold,
                "timeout": self.config.timeout,
            }
        }


# Global circuit breaker instances
_circuit_breakers: Dict[str, CircuitBreaker] = {}


def get_circuit_breaker(name: str, config: Optional[CircuitBreakerConfig] = None) -> CircuitBreaker:
    """Get or create a circuit breaker instance."""
    if name not in _circuit_breakers:
        _circuit_breakers[name] = CircuitBreaker(name, config)
    return _circuit_breakers[name]


def with_retry(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff_factor: float = 2.0,
    circuit_breaker_name: Optional[str] = None,
):
    """Decorator to add retry logic to async functions."""
    def decorator(func: Callable[..., Any]):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            
            # Get circuit breaker if specified
            circuit_breaker = None
            if circuit_breaker_name:
                circuit_breaker = get_circuit_breaker(circuit_breaker_name)
            
            for attempt in range(max_retries + 1):
                try:
                    if circuit_breaker:
                        # Use circuit breaker
                        return await circuit_breaker.call(lambda: func(*args, **kwargs))
                    else:
                        # Direct call
                        return await func(*args, **kwargs)
                
                except (ConnectionError, TimeoutError, HomeyConnectionError, HomeyTimeoutError) as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        logger.error(f"Function {func.__name__} failed after {max_retries + 1} attempts: {e}")
                        break
                    
                    # Calculate delay with exponential backoff
                    retry_delay = delay * (backoff_factor ** attempt)
                    logger.warning(
                        f"Function {func.__name__} failed (attempt {attempt + 1}/{max_retries + 1}), "
                        f"retrying in {retry_delay:.1f}s: {e}"
                    )
                    await asyncio.sleep(retry_delay)
                
                except Exception as e:
                    # Don't retry on non-network errors
                    logger.debug(f"Non-retryable error in {func.__name__}: {e}")
                    raise
            
            # Re-raise the last exception
            if last_exception:
                raise last_exception
            
            # Shouldn't reach here, but just in case
            raise RuntimeError(f"Function {func.__name__} failed with unknown error")
        
        return wrapper
    return decorator


def get_all_circuit_breaker_status() -> Dict[str, Dict[str, Any]]:
    """Get status of all circuit breakers."""
    return {name: cb.get_status() for name, cb in _circuit_breakers.items()}
