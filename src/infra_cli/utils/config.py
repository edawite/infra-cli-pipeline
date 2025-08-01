"""
Configuration utilities for infra_cli.

This module provides a small dataclass representation of the pipeline
configuration and helper functions to load YAML files into that
structure. Configuration values can be overridden on the command line
via the CLI; see :mod:`infra_cli.main` for details.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import yaml


@dataclass
class BackoffConfig:
    """Retry/backoff settings for handling transient errors."""

    retries: int = 3
    base_delay: float = 0.2


@dataclass
class MetricsConfig:
    """Metrics configuration for exposing Prometheus counters and histograms."""

    enabled: bool = True
    port: int = 8000
    prefix: str = "infra_cli"


@dataclass
class LoggingConfig:
    """Logging configuration for structured JSON logs and file output."""

    level: str = "INFO"
    json: bool = True
    file: str = "./results/infra_cli.log"


@dataclass
class Config:
    """Top‑level pipeline configuration.

    Paths are stored as :class:`pathlib.Path` objects. Most values
    correspond directly to keys in the YAML configuration file.
    """

    input_dir: Path
    output_file: Path
    checkpoint_file: Path
    workers: int = 4
    max_queue_size: int = 64
    rate_limit_per_sec: float = 10.0
    backoff: BackoffConfig = BackoffConfig()
    metrics: MetricsConfig = MetricsConfig()
    logging: LoggingConfig = LoggingConfig()


def _deep_update(dst: dict, src: dict) -> dict:
    """Recursively merge ``src`` into ``dst`` and return the result.

    This helper is used to overlay user‑provided configuration on top
    of defaults loaded from ``default.yaml``. It performs a deep
    update of nested dictionaries without mutating the originals.
    """

    result = dict(dst)
    for key, value in src.items():
        if isinstance(value, dict) and key in result and isinstance(result[key], dict):
            result[key] = _deep_update(result[key], value)
        else:
            result[key] = value
    return result


def _load_yaml(path: Path) -> dict:
    """Load a YAML file into a plain dictionary.

    Raises a ``FileNotFoundError`` if the file does not exist.
    """

    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_config(config_path: Optional[Path] = None) -> Config:
    """Load the pipeline configuration.

    If ``config_path`` is provided it is loaded and merged with the
    default configuration file. Command‑line overrides should be
    applied by the caller after loading. Returns an instance of
    :class:`Config`.
    """

    # Determine where the default config lives relative to this file.
    default_path = Path(__file__).resolve().parents[3] / "config" / "default.yaml"
    default_config = _load_yaml(default_path)
    user_config = {}  # type: dict
    if config_path:
        user_config = _load_yaml(config_path)

    merged = _deep_update(default_config, user_config)

    # Build the dataclass structure. Use explicit conversions for
    # nested objects.
    backoff_conf = merged.get("backoff", {})
    metrics_conf = merged.get("metrics", {})
    logging_conf = merged.get("logging", {})

    config = Config(
        input_dir=Path(merged.get("input_dir", "./data")),
        output_file=Path(merged.get("output_file", "./results/output.jsonl")),
        checkpoint_file=Path(merged.get("checkpoint_file", "./results/checkpoints.txt")),
        workers=int(merged.get("workers", 4)),
        max_queue_size=int(merged.get("max_queue_size", 64)),
        rate_limit_per_sec=float(merged.get("rate_limit_per_sec", 10)),
        backoff=BackoffConfig(
            retries=int(backoff_conf.get("retries", 3)),
            base_delay=float(backoff_conf.get("base_delay", 0.2)),
        ),
        metrics=MetricsConfig(
            enabled=bool(metrics_conf.get("enabled", True)),
            port=int(metrics_conf.get("port", 8000)),
            prefix=str(metrics_conf.get("prefix", "infra_cli")),
        ),
        logging=LoggingConfig(
            level=str(logging_conf.get("level", "INFO")),
            json=bool(logging_conf.get("json", True)),
            file=str(logging_conf.get("file", "./results/infra_cli.log")),
        ),
    )
    return config
