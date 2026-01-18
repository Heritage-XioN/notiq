import functools
import inspect
import time
from collections.abc import Callable
from typing import Any, ParamSpec, TypeVar, cast

from notiq.monitoring.loggers import Logger
from notiq.monitoring.metrics import REQUEST_COUNT, REQUEST_LATENCY
from notiq.monitoring.validation import validate_metric_name

P = ParamSpec("P")  # captures the parameters of the user's function (args/kwargs)
R = TypeVar("R")  # captures the return type of the user's function


def monitor(
    metric_name: str, file_output: bool = False, json_serialize: bool = True
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    A decorator to measure the execution time of a function.
    it can handle both sync amd async

    Args:
        metric_name: The label used for logging and Prometheus metrics.
            Must match Prometheus naming: [a-zA-Z_][a-zA-Z0-9_]* (max 64 chars).
        file_output: controls writing logs to a file (./logs/metric_name.log)
        json_serialize: controls serializing log output for log file.

    Raises:
        ValueError: If metric_name doesn't match Prometheus naming conventions.
    """
    # Validate metric_name early to prevent cardinality attacks
    validate_metric_name(metric_name)

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        # initialise logger instance
        log = Logger(
            metric_name, file_output=file_output, json_serialize=json_serialize
        ).setup()

        # handle async functions
        if inspect.iscoroutinefunction(func):

            @functools.wraps(func)  # capures wrapped async func/method metadata
            async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> Any:
                start_time: float = time.perf_counter()
                try:
                    log.info("started func execution")
                    # Execute the user async function
                    result = await func(*args, **kwargs)
                    log.info("func successfully ran")

                    # Record Success
                    REQUEST_COUNT.labels(
                        function_name=metric_name, status="success"
                    ).inc()

                    return result
                except Exception:
                    # Record Failure
                    log.exception("error occured", exc_info=True)
                    REQUEST_COUNT.labels(
                        function_name=metric_name, status="error"
                    ).inc()
                    # re-raise to preserve traceback
                    raise
                finally:
                    duration: float = time.perf_counter() - start_time
                    # latency metric
                    REQUEST_LATENCY.labels(function_name=metric_name).observe(duration)

            return cast(Callable[P, R], async_wrapper)

        # handle sync functions
        @functools.wraps(func)  # capures wrapped func/method metadata
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            start_time: float = time.perf_counter()

            try:
                log.info("started func execution")
                # Execute the user sync function
                result = func(*args, **kwargs)
                log.info("func successfully ran")

                # Record Success
                REQUEST_COUNT.labels(function_name=metric_name, status="success").inc()

                return result
            except Exception:
                # Record Failure
                log.exception("error occured", exc_info=True)
                REQUEST_COUNT.labels(function_name=metric_name, status="error").inc()
                # re-raise to preserve traceback
                raise
            finally:
                duration: float = time.perf_counter() - start_time
                # latency metric
                REQUEST_LATENCY.labels(function_name=metric_name).observe(duration)

        return wrapper

    return decorator
