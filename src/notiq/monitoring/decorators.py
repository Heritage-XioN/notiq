import asyncio
import functools
import inspect
import time
import warnings
from collections.abc import Callable
from typing import Any, ParamSpec, TypeVar, cast

from notiq.monitoring.loggers import Logger, get_log_context
from notiq.monitoring.metrics import REQUEST_COUNT, REQUEST_LATENCY
from notiq.monitoring.validation import validate_metric_name

P = ParamSpec("P")  # captures the parameters of the user's function (args/kwargs)
R = TypeVar("R")  # captures the return type of the user's function


def monitor(
    metric_name: str,
    file_output: bool = False,
    json_serialize: bool = True,
    log_calls: bool = True,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    A decorator to measure the execution time of a function.
    Handles both sync and async functions.

    Args:
        metric_name: The label used for logging and Prometheus metrics.
            Must match Prometheus naming: [a-zA-Z_][a-zA-Z0-9_]* (max 64 chars).
        file_output: Controls writing logs to a file (./logs/metric_name.log).
        json_serialize: Controls serializing log output for log file.
        log_calls: If True, logs start/end of each function call. Set to False
            for high-frequency functions to reduce logging overhead.

    Raises:
        ValueError: If metric_name doesn't match Prometheus naming conventions.

    Note:
        Generator and async generator functions are not fully supported.
        The decorator will issue a warning if applied to such functions,
        as timing will only capture generator creation, not iteration.

    Example:
        from notiq.monitoring.decorators import monitor
        from notiq.monitoring.loggers import log_context

        @monitor("payment_process", file_output=True)
        async def process_payment(amount: float) -> str:
            ...

        # Use with context:
        with log_context(correlation_id="abc-123", user_id=456):
            await process_payment(100.0)
    """
    # Validate metric_name early to prevent cardinality attacks
    validate_metric_name(metric_name)

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        # Warn if decorating a generator function (timing would be misleading)
        if inspect.isgeneratorfunction(func) or inspect.isasyncgenfunction(func):
            warnings.warn(
                f"@monitor applied to generator function '{func.__name__}'. "
                "Timing will only capture generator creation, not iteration. "
                "Consider monitoring the consuming code instead.",
                UserWarning,
                stacklevel=2,
            )

        # Initialize logger instance
        log = Logger(
            metric_name, file_output=file_output, json_serialize=json_serialize
        ).setup()

        # Handle async functions
        if inspect.iscoroutinefunction(func):

            @functools.wraps(func)  # captures wrapped async func/method metadata
            async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> Any:
                start_time: float = time.perf_counter()
                try:
                    if log_calls:
                        log.info("started func execution", extra=get_log_context())
                    # Execute the user async function
                    result = await func(*args, **kwargs)
                    if log_calls:
                        log.info("func successfully ran", extra=get_log_context())

                    # Record Success
                    REQUEST_COUNT.labels(
                        function_name=metric_name, status="success"
                    ).inc()

                    return result
                except asyncio.CancelledError:
                    # Handle task cancellation separately (not an error)
                    log.info("task cancelled", extra=get_log_context())
                    REQUEST_COUNT.labels(
                        function_name=metric_name, status="cancelled"
                    ).inc()
                    raise  # Re-raise to propagate cancellation
                except Exception:
                    # Record Failure
                    log.exception(
                        "error occurred", exc_info=True, extra=get_log_context()
                    )
                    REQUEST_COUNT.labels(
                        function_name=metric_name, status="error"
                    ).inc()
                    raise  # Re-raise to preserve traceback
                finally:
                    duration: float = time.perf_counter() - start_time
                    # Latency metric
                    REQUEST_LATENCY.labels(function_name=metric_name).observe(duration)

            return cast(Callable[P, R], async_wrapper)

        # Handle sync functions
        @functools.wraps(func)  # captures wrapped func/method metadata
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> Any:
            start_time: float = time.perf_counter()
            try:
                if log_calls:
                    log.info("started func execution", extra=get_log_context())
                # Execute the user sync function
                result = func(*args, **kwargs)
                if log_calls:
                    log.info("func successfully ran", extra=get_log_context())

                # Record Success
                REQUEST_COUNT.labels(function_name=metric_name, status="success").inc()

                return result
            except Exception:
                # Record Failure
                log.exception("error occurred", exc_info=True, extra=get_log_context())
                REQUEST_COUNT.labels(function_name=metric_name, status="error").inc()
                raise  # Re-raise to preserve traceback
            finally:
                duration: float = time.perf_counter() - start_time
                # Latency metric
                REQUEST_LATENCY.labels(function_name=metric_name).observe(duration)

        return wrapper

    return decorator
