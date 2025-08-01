"""
File hashing utilities.

The functions in this module compute cryptographic hashes of file
contents. A hash value is used as a deterministic identifier for a
document; if the same file is processed twice the pipeline will
recognise it via its hash and avoid redundant work.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Union


def hash_file(path: Union[str, Path], chunk_size: int = 65536) -> str:
    """Compute the SHA‑256 hash of a file and return its hexadecimal digest.

    Parameters
    ----------
    path:
        Path to the file to be hashed. Accepts str or Path.
    chunk_size:
        Read the file in chunks of this size (in bytes) to avoid loading
        large files into memory at once. Defaults to 64 KiB.

    Returns
    -------
    str
        Hexadecimal representation of the file's SHA‑256 digest.

    Raises
    ------
    FileNotFoundError
        If the file does not exist.
    """

    sha256 = hashlib.sha256()
    file_path = Path(path)
    with file_path.open("rb") as f:
        while True:
            data = f.read(chunk_size)
            if not data:
                break
            sha256.update(data)
    return sha256.hexdigest()
