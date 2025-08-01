"""
File discovery stage.

This stage is responsible for finding candidate files for processing.
Files are yielded recursively from the configured ``input_dir`` if
their suffix matches supported document types (.pdf, .txt). Hidden
files and directories (starting with '.') are ignored.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Iterator


SUPPORTED_SUFFIXES = {".pdf", ".txt"}


def discover(input_dir: Path) -> Iterator[Path]:
    """Yield paths to supported files within ``input_dir``.

    Parameters
    ----------
    input_dir:
        Directory to search. The search is recursive.

    Yields
    ------
    pathlib.Path
        Paths to files that should be processed.
    """

    root = Path(input_dir)
    if not root.exists() or not root.is_dir():
        return
    for path in root.rglob("*"):
        if path.is_file() and not any(part.startswith(".") for part in path.parts):
            if path.suffix.lower() in SUPPORTED_SUFFIXES:
                yield path
