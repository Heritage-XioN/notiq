"""
Integration tests for the monitoring module.

Tests the full monitoring pipeline: decorator → logger → metrics,
verifying that pre-built metrics are correctly wired and observable.
"""

from prometheus_client import CollectorRegistry

from notiq.monitoring.builder import MetricBuilder
from notiq.monitoring.loggers import Logger, log_context


class TestPreBuiltMetrics:
    """
    Integration tests for pre-built REQUEST_COUNT and REQUEST_LATENCY.
    Uses an isolated registry to avoid global pollution.
    """

    def test_counter_metric_increments_on_label(
        self, fresh_registry: CollectorRegistry
    ):
        # Note: prometheus_client appends _total to Counter names automatically
        # so "request_count" becomes "notiq_request_count_total"
        counter = MetricBuilder(
            name="request_count",
            documentation="Total number of function calls",
            labelnames=["function_name", "status"],
            registry=fresh_registry,
        ).counter()

        counter.labels(function_name="test_func", status="success").inc()

        value = fresh_registry.get_sample_value(
            "notiq_request_count_total",
            {"function_name": "test_func", "status": "success"},
        )
        assert value == 1.0

    def test_counter_tracks_multiple_statuses(self, fresh_registry: CollectorRegistry):
        counter = MetricBuilder(
            name="multi_status",
            documentation="Multi-status counter",
            labelnames=["function_name", "status"],
            registry=fresh_registry,
        ).counter()

        counter.labels(function_name="payment", status="success").inc()
        counter.labels(function_name="payment", status="success").inc()
        counter.labels(function_name="payment", status="error").inc()

        success_val = fresh_registry.get_sample_value(
            "notiq_multi_status_total",
            {"function_name": "payment", "status": "success"},
        )
        error_val = fresh_registry.get_sample_value(
            "notiq_multi_status_total",
            {"function_name": "payment", "status": "error"},
        )
        assert success_val == 2.0
        assert error_val == 1.0

    def test_histogram_observes_latency(self, fresh_registry: CollectorRegistry):
        histogram = MetricBuilder(
            name="request_latency_seconds",
            documentation="Time spent processing request",
            labelnames=["function_name"],
            registry=fresh_registry,
        ).histogram()

        histogram.labels(function_name="test_func").observe(0.5)
        histogram.labels(function_name="test_func").observe(1.5)

        count_val = fresh_registry.get_sample_value(
            "notiq_request_latency_seconds_count",
            {"function_name": "test_func"},
        )
        sum_val = fresh_registry.get_sample_value(
            "notiq_request_latency_seconds_sum",
            {"function_name": "test_func"},
        )
        assert count_val == 2.0
        assert sum_val == 2.0


class TestLoggerIntegration:
    """Integration tests for logger setup with context."""

    def test_logger_emits_output_with_context(self, capsys):  # pyright: ignore[reportUnknownParameterType, reportMissingParameterType]
        """Verify that a logger with context produces console output.

        Since Logger sets propagate=False, we verify via captured
        stdout (where the StreamHandler writes) rather than caplog.
        """
        logger = Logger(
            "integration_output_test",
            json_serialize=False,
        )
        log = logger.setup()

        with log_context(correlation_id="abc-123", user_id=456):
            log.info("processing payment")

        captured = capsys.readouterr()
        assert "processing payment" in captured.out


class TestMetricBuilderIdempotency:
    """
    Verify MetricBuilder's safe re-registration logic.
    Creating the same metric twice should return the existing one.
    """

    def test_same_metric_returns_existing(self, fresh_registry: CollectorRegistry):
        builder_args = {
            "name": "idempotent_counter",
            "documentation": "test",
            "registry": fresh_registry,
        }
        counter_1 = MetricBuilder(**builder_args).counter()  # pyright: ignore[reportArgumentType]
        counter_2 = MetricBuilder(**builder_args).counter()  # pyright: ignore[reportArgumentType]

        # Should be the exact same object
        assert counter_1 is counter_2
