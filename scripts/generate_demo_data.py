#!/usr/bin/env python3
"""
Utility to generate a set of small text files for use with the infra cli
pipeline.  This script is intentionally simple and self contained so
that prospective employers and reviewers can run a quick throughput
benchmark without sourcing external datasets.  It uses Python's
standard library to create random words and writes them to numbered
files within the target directory.

Usage on the command line:

    python generate_demo_data.py --output-dir ./data --n-files 100

The default values will generate 100 files with between 50 and 200
randomly generated words each.  Adjust the ``--min-words`` and
``--max-words`` flags to vary the document length.  Only text files are
generated; PDF support can be added by swapping out the write call for
an appropriate PDF library such as ``fpdf`` or ``reportlab``.
"""

from __future__ import annotations

import random
import string
from pathlib import Path
from typing import Optional

import typer


app = typer.Typer(add_completion=False, help="Generate demo text files for the infra cli pipeline.")


def _random_word(min_len: int = 3, max_len: int = 10) -> str:
    """Return a randomly generated lowercase word.

    The word length is chosen uniformly between ``min_len`` and
    ``max_len`` characters.  Words consist solely of ASCII letters.

    Parameters
    ----------
    min_len: int
        Minimum number of characters in each word (inclusive).
    max_len: int
        Maximum number of characters in each word (inclusive).

    Returns
    -------
    str
        A random lowercase word.
    """
    length = random.randint(min_len, max_len)
    return "".join(random.choices(string.ascii_lowercase, k=length))


@app.command()
def generate(
    output_dir: Path = typer.Option(
        Path("./data"),
        exists=False,
        file_okay=False,
        dir_okay=True,
        help="Directory to write generated text files into.",
    ),
    n_files: int = typer.Option(
        100,
        min=1,
        help="Number of files to generate.",
    ),
    min_words: int = typer.Option(
        50,
        min=1,
        help="Minimum number of words per file.",
    ),
    max_words: int = typer.Option(
        200,
        min=1,
        help="Maximum number of words per file.",
    ),
) -> None:
    """Generate a collection of random text files.

    Creates ``n_files`` text files within ``output_dir``.  Each file is
    populated with a random number of words between ``min_words`` and
    ``max_words`` inclusive.  The filename format is ``doc_<i>.txt``
    where ``i`` starts at 1.

    Raises
    ------
    typer.BadParameter
        If ``max_words`` is less than ``min_words``.
    """
    if max_words < min_words:
        raise typer.BadParameter("max_words must be greater than or equal to min_words")

    output_dir.mkdir(parents=True, exist_ok=True)

    for i in range(1, n_files + 1):
        num_words = random.randint(min_words, max_words)
        words = [_random_word() for _ in range(num_words)]
        text = " ".join(words)
        file_path = output_dir / f"doc_{i}.txt"
        file_path.write_text(text, encoding="utf-8")

    typer.echo(f"Generated {n_files} files in {output_dir}")


if __name__ == "__main__":
    app()
