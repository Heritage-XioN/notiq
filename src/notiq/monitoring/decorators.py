import functools
import time
from collections.abc import Callable
from typing import ParamSpec, TypeVar

from notiq.monitoring.loggers import Logger
from notiq.monitoring.metrics import REQUEST_COUNT, REQUEST_LATENCY

P = ParamSpec("P")  # captures the parameters of the user's function (args/kwargs)
R = TypeVar("R")  # captures the return type of the user's function


def monitor(
    metric_name: str, file_output: bool = False, json_serialize: bool = True
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    A decorator to measure the execution time of a function.

    Args:
        metric_name: The label used for logging and Prometheus metrics.
        file_output: controls writing logs to a file (./logs/metric_name.log)
        json_serialize: controls serializing log output for log file.
    """

    # initialise logger instance
    log = Logger(
        metric_name, file_output=file_output, json_serialize=json_serialize
    ).setup()

    # The decorator func
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        # The wrapper that replaces the user's function
        @functools.wraps(func)  # capures wrapped func/method metadata
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            start_time: float = time.perf_counter()

            try:
                # TODO: refine logger implementation and or display

                log.info("started func execution")
                # Execute the actual user function
                result = func(*args, **kwargs)
                log.info("func successfully ran")

                # Record Success
                REQUEST_COUNT.labels(function_name=metric_name, status="success").inc()

                return result
            except Exception as e:
                # Record Failure
                log.exception("error occured", exc_info=True)
                REQUEST_COUNT.labels(function_name=metric_name, status="error").inc()
                # re-raise, exception so it can be caught by the user
                raise e
            finally:
                # This runs whether the function succeeds or fails
                end_time: float = time.perf_counter()
                duration: float = end_time - start_time

                REQUEST_LATENCY.labels(function_name=metric_name).observe(duration)

        return wrapper

    return decorator
