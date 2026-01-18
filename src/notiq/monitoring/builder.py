# src/notiq/monitoring/builder.py
from collections.abc import Iterable, Sequence
from typing import Any, TypeVar, cast

from prometheus_client import (
    REGISTRY,
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    Summary,
)
from prometheus_client.metrics import MetricWrapperBase

# Define a Generic Type that covers all Metric types
M = TypeVar("M", bound=MetricWrapperBase)


class MetricBuilder:
    """
    A builder class to standardize metric creation across the Notiq package.
    Enforces namespaces and safe registration.

    Args:
        name: str - the name of the metric
        documentation: str - the documentation of the metric
        labelnames: Iterable[str] - the labelnames of the metric
        namespace: str - the namespace of the metric
        subsystem: str - the subsystem of the metric
        unit: str - the unit of the metric
        registry: CollectorRegistry | None - the registry to use
    """

    def __init__(
        self,
        name: str,
        documentation: str,
        labelnames: Iterable[str] = (),
        namespace: str = "notiq",
        subsystem: str = "",
        unit: str = "",
        registry: CollectorRegistry | None = None,
    ) -> None:
        self.name = name
        self.documentation = documentation
        self.labelnames = labelnames
        self.namespace = namespace
        self.subsystem = subsystem
        self.unit = unit
        # Default to the global registry if None is passed
        self.registry = registry if registry is not None else REGISTRY

    def _get_full_name(self) -> str:
        """Helper to generate the final prometheus name."""
        parts = [self.namespace, self.subsystem, self.name]
        return "_".join(p for p in parts if p)

    def _get_or_create(self, metric_cls: type[M], **kwargs: Any) -> M:
        """
        Safely retrieves a metric from the registry or creates a new one.
        Uses Generics (Type[M]) to ensure the return type matches the input class.
        """
        full_name = self._get_full_name()

        # Check if the metric already exists in the registry.
        # NOTE: We access the private '_names_to_collectors' to avoid crashing.
        # We use getattr to safely access it without angering the linter too much,
        # but for Mypy strict mode, we must suppress the attribute error explicitly
        # because the library does not expose this publicly.

        # We assume self.registry is never None because of the __init__ logic
        existing_collectors = getattr(self.registry, "_names_to_collectors", {})

        if full_name in existing_collectors:
            # if found, we must cast it to type 'M' because Python
            # doesn't know for sure if the stored object matches 'metric_cls'.
            return cast(M, existing_collectors[full_name])

        # If not found, create a new one with thread-safety.
        try:
            # The metric automatically registers itself upon init.
            return cast(M, metric_cls(**kwargs))
        except ValueError:
            # Handle duplicate registration under race conditions
            existing = getattr(self.registry, "_names_to_collectors", {}).get(full_name)
            return cast(M, existing)

    # prometheus counter metric
    def counter(self) -> Counter:
        """Create a counter metric."""
        return self._get_or_create(
            Counter,
            name=self.name,
            documentation=self.documentation,
            labelnames=self.labelnames,
            namespace=self.namespace,
            subsystem=self.subsystem,
            unit=self.unit,
            registry=self.registry,
        )

    # prometheus gauge metric
    def gauge(self) -> Gauge:
        """Create a gauge metric."""
        return self._get_or_create(
            Gauge,
            name=self.name,
            documentation=self.documentation,
            labelnames=self.labelnames,
            namespace=self.namespace,
            subsystem=self.subsystem,
            unit=self.unit,
            registry=self.registry,
        )

    # prometheus histogram metric
    def histogram(
        self, buckets: Sequence[float] = Histogram.DEFAULT_BUCKETS
    ) -> Histogram:
        """Create a histogram metric."""
        return self._get_or_create(
            Histogram,
            name=self.name,
            documentation=self.documentation,
            labelnames=self.labelnames,
            namespace=self.namespace,
            subsystem=self.subsystem,
            unit=self.unit,
            registry=self.registry,
            buckets=buckets,
        )

    # prometheus summary metric
    def summary(self) -> Summary:
        """Create a summary metric."""
        return self._get_or_create(
            Summary,
            name=self.name,
            documentation=self.documentation,
            labelnames=self.labelnames,
            namespace=self.namespace,
            subsystem=self.subsystem,
            unit=self.unit,
            registry=self.registry,
        )
