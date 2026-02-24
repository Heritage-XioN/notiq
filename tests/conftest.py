import pytest
from prometheus_client import CollectorRegistry


@pytest.fixture
def fresh_registry() -> CollectorRegistry:
    """
    Provide a fresh Prometheus CollectorRegistry for each test.

    Prevents global registry pollution where metrics registered in one test
    would conflict with metrics in another test (since Prometheus disallows
    duplicate metric names in the same registry).
    """
    return CollectorRegistry()
