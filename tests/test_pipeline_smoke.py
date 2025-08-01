from pathlib import Path
import json

from infra_cli.pipeline import Pipeline
from infra_cli.utils.config import Config, BackoffConfig, MetricsConfig, LoggingConfig


def test_pipeline_smoke(tmp_path: Path) -> None:
    """Run the pipeline on a single text file and ensure output is produced."""
    input_dir = tmp_path / "input"
    output_file = tmp_path / "out.jsonl"
    checkpoint_file = tmp_path / "checkpoints.txt"
    input_dir.mkdir()
    (input_dir / "test.txt").write_text("quick brown fox jumps over the lazy dog")
    config = Config(
        input_dir=input_dir,
        output_file=output_file,
        checkpoint_file=checkpoint_file,
        workers=2,
        max_queue_size=10,
        rate_limit_per_sec=10,
        backoff=BackoffConfig(retries=1, base_delay=0.1),
        metrics=MetricsConfig(enabled=False, port=0, prefix="test"),
        logging=LoggingConfig(level="INFO", json=False, file=str(tmp_path / "log.txt")),
    )
    pipeline = Pipeline(config)
    pipeline.run()
    assert output_file.exists()
    lines = output_file.read_text().splitlines()
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["label"] in {"short", "long"}
