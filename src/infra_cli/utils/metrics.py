"""
Prometheus metrics instrumentation.

This module wraps the ``prometheus_client`` library to expose a
handful of counters, histograms and gauges used throughout the
pipeline. A helper function is provided to start the HTTP server that
serves the ``/metrics`` endpoint.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from prometheus_client import Counter, Gauge, Histogram, start_http_server


@dataclass
class PipelineMetrics:
    """Container for Prometheus metrics used by the pipeline.

    When ``prefix`` is provided each metric name will be prefixed
    accordingly, allowing multiple pipelines to run in the same
    process without collisions.
    """

    prefix: str = "infra_cli"

    def __post_init__(self) -> None:
        name = lambda suffix: f"{self.prefix}_{suffix}"
        self.files_processed = Counter(name("files_processed_total"), "Total number of files successfully processed")
        self.processing_seconds = Histogram(
            name("processing_seconds"), "Time spent processing files", ['stage'],
            buckets=(0.01, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0)
        )
        self.errors_total = Counter(
            name("errors_total"), "Total number of errors", ['stage']
        )
        self.queue_depth = Gauge(name("queue_depth"), "Current depth of the work queue")

    def start_http_server(self, port: int = 8000) -> None:
        """Expose the metrics endpoint on ``/metrics``.

        This should be called once during application start‑up when
        metrics are enabled in the configuration.
        """
        start_http_server(port)
