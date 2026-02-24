import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from unittest.mock import patch

import pytest

from notiq.monitoring.loggers import (
    JsonFormatter,
    Logger,
    clear_log_context,
    get_log_context,
    log_context,
    set_log_context,
)

# ---------------------------------------------------------------------------
# Logger.setup() tests
# ---------------------------------------------------------------------------


class TestLoggerSetup:
    """Tests for Logger.setup() handler creation and idempotency."""

    def test_setup_adds_console_handler(self):
        logger = Logger("test_setup_console")
        result = logger.setup()

        # Should have at least one StreamHandler
        stream_handlers = [
            h
            for h in result.handlers
            if isinstance(h, logging.StreamHandler)
            and not isinstance(h, RotatingFileHandler)
        ]
        assert len(stream_handlers) >= 1  # pyright: ignore[reportUnknownArgumentType]

    def test_setup_is_idempotent(self):
        logger = Logger("test_setup_idempotent")
        result1 = logger.setup()
        initial_count = len(result1.handlers)

        # Calling setup again should not duplicate handlers
        result2 = logger.setup()
        assert len(result2.handlers) == initial_count

    def test_setup_disables_propagation(self):
        logger = Logger("test_setup_propagation")
        result = logger.setup()
        assert result.propagate is False

    def test_setup_with_file_output(self, tmp_path: Path):
        logger = Logger(
            "test_setup_file",
            log_dir=tmp_path,
            file_output=True,
        )
        result = logger.setup()

        try:
            # Should have a RotatingFileHandler
            file_handlers = [
                h for h in result.handlers if isinstance(h, RotatingFileHandler)
            ]
            assert len(file_handlers) >= 1

            # Log file should exist
            log_file = tmp_path / "test_setup_file.log"
            assert log_file.exists()
        finally:
            # Close handlers to release file locks (Windows)
            for h in result.handlers[:]:
                h.close()
                result.removeHandler(h)

    def test_setup_file_handler_uses_json_formatter(self, tmp_path: Path):
        logger = Logger(
            "test_json_formatter_setup",
            log_dir=tmp_path,
            file_output=True,
            json_serialize=True,
        )
        result = logger.setup()

        try:
            file_handlers = [
                h for h in result.handlers if isinstance(h, RotatingFileHandler)
            ]
            assert len(file_handlers) >= 1
            assert isinstance(file_handlers[0].formatter, JsonFormatter)
        finally:
            for h in result.handlers[:]:
                h.close()
                result.removeHandler(h)

    def test_setup_file_handler_uses_text_formatter_when_json_disabled(
        self, tmp_path: Path
    ):
        logger = Logger(
            "test_text_formatter_setup",
            log_dir=tmp_path,
            file_output=True,
            json_serialize=False,
        )
        result = logger.setup()

        try:
            file_handlers = [
                h for h in result.handlers if isinstance(h, RotatingFileHandler)
            ]
            assert len(file_handlers) >= 1
            assert not isinstance(file_handlers[0].formatter, JsonFormatter)
        finally:
            for h in result.handlers[:]:
                h.close()
                result.removeHandler(h)

    def test_setup_file_handler_graceful_on_permission_error(
        self, capsys: pytest.CaptureFixture[str]
    ):
        with patch("notiq.monitoring.loggers.Path.mkdir", side_effect=PermissionError):
            logger = Logger(
                "test_permission_error",
                file_output=True,
            )
            # Should not raise — gracefully degrades
            result = logger.setup()
            assert result is not None

            # Should write warning to stderr
            captured = capsys.readouterr()
            assert "Permission denied" in captured.err

    def test_setup_file_handler_graceful_on_os_error(
        self, capsys: pytest.CaptureFixture[str]
    ):
        with patch(
            "notiq.monitoring.loggers.Path.mkdir", side_effect=OSError("disk full")
        ):
            logger = Logger(
                "test_os_error",
                file_output=True,
            )
            result = logger.setup()
            assert result is not None

            captured = capsys.readouterr()
            assert "Failed to create file handler" in captured.err


# ---------------------------------------------------------------------------
# JsonFormatter tests
# ---------------------------------------------------------------------------


class TestJsonFormatter:
    """Tests for JsonFormatter JSON output structure."""

    def _make_record(self, msg: str = "test message", **kwargs) -> logging.LogRecord:  # pyright: ignore[reportUnknownParameterType, reportMissingParameterType]
        """Helper to create a LogRecord with optional extras."""
        record = logging.LogRecord(
            name="test_formatter",
            level=logging.INFO,
            pathname="test.py",
            lineno=42,
            msg=msg,
            args=(),
            exc_info=None,
        )
        for key, value in kwargs.items():
            setattr(record, key, value)
        return record

    def test_format_returns_valid_json(self):
        formatter = JsonFormatter()
        record = self._make_record()
        result = formatter.format(record)

        parsed = json.loads(result)
        assert isinstance(parsed, dict)

    def test_format_contains_required_fields(self):
        formatter = JsonFormatter()
        record = self._make_record()
        parsed = json.loads(formatter.format(record))

        assert "timestamp" in parsed
        assert "name" in parsed
        assert "level" in parsed
        assert "message" in parsed
        assert "module" in parsed
        assert "line" in parsed
        assert "process_id" in parsed
        assert "thread_name" in parsed
        assert "hostname" in parsed
        assert "context" in parsed

    def test_format_message_content(self):
        formatter = JsonFormatter()
        record = self._make_record("payment processed")
        parsed = json.loads(formatter.format(record))

        assert parsed["message"] == "payment processed"
        assert parsed["name"] == "test_formatter"
        assert parsed["level"] == "INFO"
        assert parsed["line"] == 42

    def test_format_includes_extras_in_context(self):
        formatter = JsonFormatter()
        record = self._make_record(correlation_id="abc-123", user_id=456)
        parsed = json.loads(formatter.format(record))

        assert parsed["context"]["correlation_id"] == "abc-123"
        assert parsed["context"]["user_id"] == 456

    def test_format_includes_exception_info(self):
        formatter = JsonFormatter()
        record = self._make_record()
        try:
            raise ValueError("test error")
        except ValueError:
            import sys

            record.exc_info = sys.exc_info()

        parsed = json.loads(formatter.format(record))
        assert "exception" in parsed
        assert "ValueError" in parsed["exception"]
        assert "test error" in parsed["exception"]

    def test_format_timestamp_is_utc_iso(self):
        formatter = JsonFormatter()
        record = self._make_record()
        parsed = json.loads(formatter.format(record))

        # Should be ISO format with timezone info
        assert "T" in parsed["timestamp"]
        assert "+" in parsed["timestamp"] or "Z" in parsed["timestamp"]


# ---------------------------------------------------------------------------
# Log context API tests
# ---------------------------------------------------------------------------


class TestLogContext:
    """Tests for set_log_context, get_log_context, clear_log_context, and log_context."""  # noqa: E501

    def setup_method(self):
        """Clear context before each test to ensure isolation."""
        clear_log_context()

    def test_get_log_context_returns_empty_dict_by_default(self):
        assert get_log_context() == {}

    def test_set_and_get_log_context(self):
        set_log_context({"correlation_id": "abc-123", "user_id": 456})
        ctx = get_log_context()

        assert ctx["correlation_id"] == "abc-123"
        assert ctx["user_id"] == 456

    def test_set_log_context_replaces_by_default(self):
        set_log_context({"key1": "value1"})
        set_log_context({"key2": "value2"})
        ctx = get_log_context()

        assert "key1" not in ctx
        assert ctx["key2"] == "value2"

    def test_set_log_context_merge_mode(self):
        set_log_context({"key1": "value1"})
        set_log_context({"key2": "value2"}, merge=True)
        ctx = get_log_context()

        assert ctx["key1"] == "value1"
        assert ctx["key2"] == "value2"

    def test_set_log_context_merge_overwrites_existing_keys(self):
        set_log_context({"key1": "old"})
        set_log_context({"key1": "new"}, merge=True)

        assert get_log_context()["key1"] == "new"

    def test_clear_log_context(self):
        set_log_context({"key1": "value1"})
        clear_log_context()

        assert get_log_context() == {}

    def test_get_log_context_returns_copy(self):
        set_log_context({"key1": "value1"})
        ctx = get_log_context()
        ctx["mutated"] = True

        # Original should be unchanged
        assert "mutated" not in get_log_context()

    def test_log_context_manager_sets_context(self):
        with log_context(request_id="xyz-789"):
            ctx = get_log_context()
            assert ctx["request_id"] == "xyz-789"

    def test_log_context_manager_restores_on_exit(self):
        set_log_context({"outer": "value"})
        with log_context(inner="scoped"):
            assert get_log_context()["inner"] == "scoped"

        # After exit, inner should be gone, outer restored
        ctx = get_log_context()
        assert "inner" not in ctx
        assert ctx["outer"] == "value"

    def test_log_context_manager_nesting(self):
        with log_context(level1="a"):
            with log_context(level2="b"):
                ctx = get_log_context()
                assert ctx["level1"] == "a"
                assert ctx["level2"] == "b"

            # After inner exit, level2 gone but level1 preserved
            ctx = get_log_context()
            assert ctx["level1"] == "a"
            assert "level2" not in ctx

        # After outer exit, everything gone
        assert get_log_context() == {}

    def test_log_context_manager_restores_on_exception(self):
        set_log_context({"safe": True})
        with pytest.raises(RuntimeError):
            with log_context(dangerous="yes"):
                raise RuntimeError("boom")

        # Context should be restored despite exception
        ctx = get_log_context()
        assert ctx["safe"] is True
        assert "dangerous" not in ctx
