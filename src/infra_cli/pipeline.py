"""
Pipeline orchestration.

The :class:`Pipeline` encapsulates the orchestration logic for the
document processing pipeline. It manages the discovery of files, the
parallel parsing of documents, classification, and writing of
results. Concurrency is implemented via a process pool executor for
CPU‑bound tasks (parsing) and thread‑safe primitives for writing and
rate limiting.

Key features:

* **Idempotency** – processed files are tracked via a checkpoint file;
  hashes are computed once and reused to skip duplicates.
* **Rate limiting** – a token‑bucket limiter controls how many files per
  second enter the pipeline.
* **Backoff and retry** – transient errors in parsing or classification
  trigger exponential backoff before reattempting.
* **Metrics** – counters and histograms record throughput and latency
  for Prometheus scraping.
* **Structured logging** – each stage logs using a JSON formatter with
  contextual information (file ID, stage name).
"""

from __future__ import annotations

import logging
import time
from concurrent.futures import ProcessPoolExecutor, as_completed, Future
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

from .stages import discover, parse, classify, write
from .utils import hashing
from .utils.backoff import retry
from .utils.checkpoints import CheckpointManager
from .utils.metrics import PipelineMetrics
from .utils.rate_limiter import RateLimiter

import threading


class Pipeline:
    """Document processing pipeline.

    Parameters
    ----------
    config:
        Loaded configuration object specifying pipeline options.
    """

    def __init__(self, config) -> None:
        self.config = config
        self.logger = logging.getLogger(__name__ + ".Pipeline")
        # Process pool for CPU‑bound parsing.
        self.pool = ProcessPoolExecutor(max_workers=self.config.workers)
        # Rate limiter controls ingestion rate.
        self.rate_limiter = RateLimiter(
            rate_per_sec=self.config.rate_limit_per_sec,
            capacity=self.config.rate_limit_per_sec,
        )
        self.checkpoints = CheckpointManager(self.config.checkpoint_file)
        self.write_lock = threading.Lock()  # For serialising writes
        # Metrics instrumentation
        self.metrics = PipelineMetrics(prefix=self.config.metrics.prefix) if self.config.metrics.enabled else None
        if self.metrics and self.config.metrics.enabled:
            # Start Prometheus metrics server. It's idempotent – calling twice has no effect.
            self.metrics.start_http_server(self.config.metrics.port)
        # Prepare classifier instance once; reuse across calls.
        self.classifier = classify.DummyClassifier()
        # Wrap parse and classify methods with retry logic.
        self.parse_with_retry = retry(
            parse.parse_file,
            retries=self.config.backoff.retries,
            base_delay=self.config.backoff.base_delay,
            logger=self.logger,
        )
        self.classify_with_retry = retry(
            self.classifier.classify,
            retries=self.config.backoff.retries,
            base_delay=self.config.backoff.base_delay,
            logger=self.logger,
        )

    def _submit_parse(self, path: Path) -> Future:
        """Submit a parse task to the process pool and return the future."""
        return self.pool.submit(self.parse_with_retry, path)

    def run(self) -> None:
        """Execute the pipeline end‑to‑end.

        Discovers input files, schedules parsing tasks with rate limiting,
        waits for results, performs classification, writes outputs and
        updates checkpoints. Metrics and logs are recorded throughout.
        """
        self.logger.info("Starting pipeline run")
        start_time = time.perf_counter()
        to_process: List[Path] = list(discover.discover(self.config.input_dir))
        total_candidates = len(to_process)
        self.logger.info("Discovered %s candidate files", total_candidates)

        futures: Dict[Future, Tuple[Path, str]] = {}
        submitted = 0
        for path in to_process:
            file_hash = hashing.hash_file(path)
            if self.checkpoints.is_processed(file_hash):
                # Skip already processed files
                self.logger.debug(
                    "Skipping already processed file", extra={"file_id": file_hash, "stage": "discover"}
                )
                continue
            # Apply ingestion rate limiting before submitting to pool.
            self.rate_limiter.acquire()
            future = self._submit_parse(path)
            futures[future] = (path, file_hash)
            submitted += 1
            # Track queue depth metric
            if self.metrics:
                self.metrics.queue_depth.set(len(futures))

        self.logger.info("Submitted %s files for processing", submitted)
        # Collect results as they complete
        for future in as_completed(futures):
            path, file_hash = futures[future]
            start = time.perf_counter()
            try:
                text = future.result()
                # Classification (in main process to avoid heavy model in child processes)
                classification_result = self.classify_with_retry(text)
                result_record = {
                    "id": file_hash,
                    "path": str(path),
                    **classification_result,
                }
                # Write result
                write.write_result(self.config.output_file, result_record, self.write_lock)
                # Mark checkpoint
                self.checkpoints.mark_processed(file_hash)
                # Record metrics and log
                duration = time.perf_counter() - start
                if self.metrics:
                    self.metrics.files_processed.inc()
                    self.metrics.processing_seconds.labels(stage="total").observe(duration)
                self.logger.info(
                    "Processed file",
                    extra={"file_id": file_hash, "stage": "pipeline", "duration_ms": round(duration * 1000, 2)},
                )
            except Exception as exc:
                # Increment error metric and log the exception
                if self.metrics:
                    self.metrics.errors_total.labels(stage="pipeline").inc()
                self.logger.exception(
                    "Failed to process file",
                    extra={"file_id": file_hash, "stage": "pipeline", "error": str(exc)}
                )
            finally:
                # Update queue depth gauge when a task completes
                if self.metrics:
                    remaining = len([f for f in futures if not f.done()])
                    self.metrics.queue_depth.set(remaining)

        # All tasks have completed; shut down the process pool to free resources
        self.pool.shutdown(wait=True)

        total_time = time.perf_counter() - start_time
        self.logger.info(
            "Pipeline complete", extra={"stage": "pipeline", "duration_ms": round(total_time * 1000, 2), "processed": submitted}
        )

    def bench(self, n: int = 100) -> None:
        """Benchmark the pipeline on ``n`` dummy inputs.

        This method generates ``n`` synthetic text samples of fixed size,
        simulating parse and classify workloads. It measures throughput
        and p95 latency and prints the results to stdout. The dummy
        workload uses the real classifier but bypasses file I/O.
        """
        import statistics
        self.logger.info("Starting benchmark with %s samples", n)
        # Generate dummy data
        dummy_text = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. " * 10
        latencies: List[float] = []
        start = time.perf_counter()
        for _ in range(n):
            t0 = time.perf_counter()
            # Directly classify dummy text without parsing from disk
            _ = self.classify_with_retry(dummy_text)
            duration = time.perf_counter() - t0
            latencies.append(duration)
        total_duration = time.perf_counter() - start
        throughput = n / total_duration if total_duration > 0 else 0.0
        # Compute the 95th percentile; fall back to the maximum value for small n
        if latencies:
            if len(latencies) >= 20:
                sorted_latencies = sorted(latencies)
                index = int(0.95 * len(sorted_latencies)) - 1
                p95 = sorted_latencies[max(0, index)]
            else:
                p95 = max(latencies)
        else:
            p95 = 0.0
        self.logger.info(
            "Benchmark complete: throughput=%.2f ops/sec, p95=%.3f s",
            throughput,
            p95,
        )
