"""
Command‑line interface for infra_cli.

This module exposes a Typer application with two primary commands:
``run`` to execute the pipeline against a directory of documents and
``bench`` to perform a simple throughput benchmark. Configuration can
be supplied via a YAML file and overriden through command‑line
options.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import typer

from .pipeline import Pipeline
from .utils.config import Config, load_config
from .utils.logging import configure_logging


app = typer.Typer(add_completion=False, help="Infra CLI pipeline for batch document processing")



def _apply_overrides(config: Config, input_dir: Optional[Path], output_file: Optional[Path], workers: Optional[int]) -> Config:
    """Return a copy of ``config`` with CLI overrides applied.

    Only non‑None values override the corresponding attributes.
    """
    # Config is a dataclass; create a shallow copy to avoid mutating the original
    cfg = Config(
        input_dir=input_dir or config.input_dir,
        output_file=output_file or config.output_file,
        checkpoint_file=config.checkpoint_file,
        workers=workers if workers is not None else config.workers,
        max_queue_size=config.max_queue_size,
        rate_limit_per_sec=config.rate_limit_per_sec,
        backoff=config.backoff,
        metrics=config.metrics,
        logging=config.logging,
    )
    return cfg


@app.command()
def run(
    input_dir: Optional[Path] = typer.Option(None, exists=True, help="Directory containing input documents"),
    output_file: Optional[Path] = typer.Option(None, help="Path to write JSONL output"),
    config: Optional[Path] = typer.Option(None, help="Path to YAML configuration file"),
    workers: Optional[int] = typer.Option(None, help="Number of worker processes"),
    verbose: bool = typer.Option(False, help="Enable debug logging"),
) -> None:
    """Run the document processing pipeline."""
    cfg = load_config(config)
    cfg = _apply_overrides(cfg, input_dir, output_file, workers)
    # Configure logging
    log_level = "DEBUG" if verbose else cfg.logging.level
    configure_logging(level=log_level, json_output=cfg.logging.json, file_path=cfg.logging.file)
    # Initialise and run pipeline
    pipeline = Pipeline(cfg)
    try:
        pipeline.run()
    except KeyboardInterrupt:
        typer.echo("Interrupted by user", err=True)
        raise typer.Exit(code=1)


@app.command()
def bench(
    n: int = typer.Option(100, min=1, help="Number of synthetic samples to process during the benchmark"),
    config: Optional[Path] = typer.Option(None, help="Optional YAML configuration file"),
    workers: Optional[int] = typer.Option(None, help="Number of worker processes"),
    verbose: bool = typer.Option(False, help="Enable debug logging"),
) -> None:
    """Run a synthetic benchmark of the classification stage."""
    cfg = load_config(config)
    cfg = _apply_overrides(cfg, None, None, workers)
    log_level = "DEBUG" if verbose else cfg.logging.level
    configure_logging(level=log_level, json_output=cfg.logging.json, file_path=cfg.logging.file)
    pipeline = Pipeline(cfg)
    pipeline.bench(n)



def main() -> None:
    """Entry point for console scripts."""
    app()


if __name__ == "__main__":  # pragma: no cover - entry point
    main()
