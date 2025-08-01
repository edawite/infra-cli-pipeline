"""
Checkpoint management for idempotent processing.

The pipeline uses a simple checkpoint file to record the hashes of
files that have already been processed. This allows the pipeline to
resume after interruption without reprocessing data. The format of
the checkpoint file is one hash per line.
"""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Set


class CheckpointManager:
    """Manage reading and writing file hashes to a checkpoint file.

    The checkpoint file lives on disk and contains one SHA‑256 hash per
    line. The manager loads all existing hashes into memory on
    initialisation. Calls to :meth:`mark_processed` update both the
    in‑memory set and append to the file. Accesses are protected by a
    lock to support concurrent calls across threads.
    """

    def __init__(self, path: Path) -> None:
        self._path = path
        self._lock = threading.Lock()
        self.processed: Set[str] = set()
        # Ensure parent directory exists
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            with path.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        self.processed.add(line)

    def is_processed(self, file_hash: str) -> bool:
        """Return True if the given hash is already recorded."""
        return file_hash in self.processed

    def mark_processed(self, file_hash: str) -> None:
        """Record a file hash as processed.

        This appends the hash to the checkpoint file and updates the
        in‑memory set atomically. Duplicate entries are ignored.
        """
        with self._lock:
            if file_hash not in self.processed:
                with self._path.open("a", encoding="utf-8") as f:
                    f.write(file_hash + "\n")
                self.processed.add(file_hash)
