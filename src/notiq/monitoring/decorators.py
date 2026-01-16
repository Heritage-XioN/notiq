import functools
import time
from collections.abc import Callable
from typing import ParamSpec, TypeVar

P = ParamSpec("P")  # captures the parameters of the user's function (args/kwargs)
R = TypeVar("R")  # captures the return type of the user's function


def monitor(metric_name: str) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    A decorator to measure the execution time of a function.

    Args:
        metric_name: The label used for logging (and later Prometheus).
    """

    # The decorator func
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        # The wrapper that replaces the user's function
        @functools.wraps(func)  # capures wrapped func/method metadata
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            print(f"--- [Notiq] Starting: {metric_name} ---")
            start_time = time.perf_counter()

            try:
                # Execute the actual user function
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                print(f"--- [Notiq] Error in {metric_name}: {e} ---")
                # re-raise, exception so it can be caught by the user
                raise e
            finally:
                # This runs whether the function succeeds or fails
                end_time = time.perf_counter()
                duration = end_time - start_time
                print(
                    f"--- [Notiq] Finished: {metric_name} | Time: {duration:.4f}s ---"
                )

                # TODO: Later, we will add:
                # prometheus_client.histogram(metric_name).observe(duration)

        return wrapper

    return decorator
