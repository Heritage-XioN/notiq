import asyncio
import logging
import time
from pathlib import Path

import pytest
from prometheus_client import (
    Counter,
    Gauge,
    Histogram,
    Summary,
)

from notiq import Logger, MetricBuilder, monitor
from notiq.monitoring.validation import sanitize_log_filename, validate_metric_name


def test_metrics_builder():
    builder = MetricBuilder(
        name="test_metric",
        documentation="test documentation",
        labelnames=["test_label"],
        namespace="test_namespace",
        subsystem="test_subsystem",
        unit="test_unit",
    )
    assert builder.name == "test_metric"
    assert builder.documentation == "test documentation"
    assert builder.labelnames == ("test_label",)
    assert builder.namespace == "test_namespace"
    assert builder.subsystem == "test_subsystem"
    assert builder.unit == "test_unit"


def test_metrics_builder_with_defaults():
    builder = MetricBuilder(
        name="test_metric",
        documentation="test documentation",
    )
    assert builder.name == "test_metric"
    assert builder.documentation == "test documentation"
    assert builder.labelnames == ()
    assert builder.namespace == "notiq"
    assert builder.subsystem == ""
    assert builder.unit == ""


def test_metrics_builder_methods():
    counter = MetricBuilder(
        name="test_counter_metric", documentation="test documentation"
    ).counter()
    gauge = MetricBuilder(
        name="test_gauge_metric", documentation="test documentation"
    ).gauge()
    histogram = MetricBuilder(
        name="test_histogram_metric", documentation="test documentation"
    ).histogram()
    summary = MetricBuilder(
        name="test_summary_metric", documentation="test documentation"
    ).summary()
    assert isinstance(counter, Counter)
    assert isinstance(gauge, Gauge)
    assert isinstance(histogram, Histogram)
    assert isinstance(summary, Summary)


def test_loggers():
    logger = Logger("test_logger")
    assert logger.logger_name == "test_logger"
    assert logger.logger == logging.getLogger("test_logger")
    assert logger.log_dir == Path("./logs")
    assert logger.level == logging.DEBUG
    assert logger.file_output is False
    assert logger.json_serialize is True


@pytest.mark.parametrize(
    "logger_name, log_dir, level, file_output, json_serialize",
    [
        ("test_logger", Path("./test_logs"), logging.INFO, True, True),
        ("test_logger_2", Path("./test_logs_2"), logging.ERROR, False, False),
        ("test_logger_3", Path("./test_logs_3"), logging.WARNING, True, False),
        ("test_logger_4", Path("./test_logs_4"), logging.CRITICAL, False, True),
    ],
)
def test_loggers_with_custom_parameters(
    logger_name: str, log_dir: Path, level: int, file_output: bool, json_serialize: bool
):
    logger = Logger(
        logger_name=logger_name,
        log_dir=log_dir,
        level=level,
        file_output=file_output,
        json_serialize=json_serialize,
    )
    assert logger.logger_name == logger_name
    assert logger.logger == logging.getLogger(logger_name)
    assert logger.log_dir == log_dir
    assert logger.level == level
    assert logger.file_output == file_output
    assert logger.json_serialize == json_serialize


@pytest.mark.parametrize(
    "log_file_name", [("./logs/test%.log"), ("./logs/test@.log"), ("./logs/test!.log")]
)
def test_sanitize_log_filename(log_file_name: str):
    assert sanitize_log_filename(log_file_name) == "test_.log"


@pytest.mark.parametrize("metric_name", ["_test_metric", "testMetric_2", "test_metric"])
def test_validate_metric_name(metric_name: str):
    assert validate_metric_name(metric_name) == metric_name


@pytest.mark.parametrize(
    "metric_name",
    [
        "test_metric_&",
        "test_metric_#",
        "test_metric_%",
        "test_metric_@",
        "test_metric_!",
        "test_metric_?",
        "test_metric_+",
        "test_metric_-",
        "test_metric_=",
        "3_test_metric",
    ],
)
def test_validate_metric_name_with_invalid_name(metric_name: str):
    with pytest.raises(ValueError):
        validate_metric_name(metric_name)


def test_metrics_decorator():
    @monitor(metric_name="payment", file_output=True)
    def payment(amount: float):
        # Simulate work
        time.sleep(0.2)
        if amount < 0:
            raise ValueError("Negative amount")
        return "Success"

    assert payment(100) == "Success"


def test_metrics_decorator_async():
    @monitor(metric_name="payment", file_output=True)
    async def payment(amount: float):
        # Simulate work
        await asyncio.sleep(0.2)
        if amount < 0:
            raise ValueError("Negative amount")
        return "Success"

    val = asyncio.run(payment(100))
    assert val == "Success"
