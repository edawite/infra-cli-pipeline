import tempfile
from pathlib import Path

from infra_cli.utils.hashing import hash_file


def test_hash_file_consistency(tmp_path: Path) -> None:
    """The hash function should return the same value across invocations."""
    content = "Hello, world!"
    file_path = tmp_path / "hello.txt"
    file_path.write_text(content)
    h1 = hash_file(file_path)
    h2 = hash_file(file_path)
    assert h1 == h2
