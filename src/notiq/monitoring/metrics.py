"""
contains pre-configured metrics for notiq
"""

from notiq.monitoring.builder import MetricBuilder

# A Counter goes UP only (e.g., Number of errors, Number of requests)
# We use labels to make them dynamic.
# Label 'function_name' lets us filter by specific functions in Grafana.
REQUEST_COUNT = MetricBuilder(
    name="requests_total",
    documentation="Total number of function calls",
    labelnames=["function_name", "status"],
).counter()

# A Histogram tracks distribution
# (e.g., Latency: how many requests took < 0.1s, < 0.5s, etc.)
REQUEST_LATENCY = MetricBuilder(
    "request_latency_seconds",
    "Time spent processing request",
    labelnames=["function_name"],
).histogram()
