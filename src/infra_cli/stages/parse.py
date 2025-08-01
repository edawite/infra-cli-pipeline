"""
Document parsing stage.

This stage loads the contents of a file and returns a text string. PDF
files are parsed via ``pdfminer.six`` when available; text files are
read directly. Unsupported suffixes result in an empty string.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Union


logger = logging.getLogger(__name__)

try:
    # ``pdfminer.six`` is used to extract text from PDF documents. It is
    # optional; if unavailable the fallback will return an empty string
    # for PDFs.
    from pdfminer.high_level import extract_text  # type: ignore
except ImportError:
    extract_text = None  # type: ignore


def parse_file(path: Union[str, Path]) -> str:
    """Return the textual contents of ``path``.

    Parameters
    ----------
    path:
        Path to the document to be parsed.

    Returns
    -------
    str
        The extracted text. If parsing fails the exception is
        propagated to the caller.
    """
    p = Path(path)
    if p.suffix.lower() == ".pdf":
        if extract_text is None:
            logger.warning("pdfminer.six not installed; cannot parse PDF %s", p)
            return ""
        return extract_text(str(p)) or ""
    # Treat anything else as a text file.
    with p.open("r", encoding="utf-8", errors="ignore") as f:
        return f.read()
