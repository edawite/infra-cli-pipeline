# Changelog

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-08-01

### Added

* Initial release of **infra-cli-pipeline** with a modular document
  processing pipeline consisting of discovery, parsing, classification
  and writing stages.
* Concurrency via `ProcessPoolExecutor` with backpressure and rate
  limiting.
* Idempotency through file hashing and checkpointing.
* Exponential backoff retry decorator with configurable retries and
  jitter.
* Prometheus metrics (counters, gauges, histograms) and HTTP
  exposition endpoint.
* JSON structured logging with configurable log level and rotating
  file handler.
* CLI built with Typer supporting `run` and `bench` commands, plus a
  configuration loader with YAML overrides.
* Test suite covering hashing consistency, rate limiter behaviour and
  an end‑to‑end pipeline smoke test.
* Dockerfile and optional docker‑compose setup with Prometheus.
* Scripts for generating demo data.