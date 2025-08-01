"""
Output writing stage.

This stage appends classification results to a JSON Lines file. Each
result is expected to be a serialisable dictionary containing at
minimum the file hash, original path and classification information.
Concurrent writers are synchronised by a lock passed into
``write_result``.
"""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Dict, Any


def write_result(output_file: Path, result: Dict[str, Any], lock: threading.Lock) -> None:
    """Append a classification result to the output JSONL file.

    Parameters
    ----------
    output_file:
        Path to the output .jsonl file. Parent directories will be
        created if necessary.
    result:
        A dictionary representing the result to write. It must be JSON
        serialisable.
    lock:
        A threading lock that must be held while writing to the file to
        prevent race conditions when multiple workers write concurrently.
    """

    output_file.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(result, ensure_ascii=False)
    with lock:
        with output_file.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
