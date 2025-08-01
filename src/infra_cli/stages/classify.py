"""
Classification stage.

This module defines the interfaces and implementations for
classifying document text. The default implementation is a simple
dummy classifier that categorises documents based on length. A
placeholder interface is provided for future integration with large
language models or other machine learning backends.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Protocol


class Classifier(Protocol):
    """Protocol for classifier implementations."""

    def classify(self, text: str) -> Dict[str, Any]:
        """Return a classification for ``text``.

        Implementations should return a dictionary so that additional
        attributes (e.g. scores, labels) may be attached in the future.
        """
        raise NotImplementedError


@dataclass
class DummyClassifier:
    """A trivial classifier used for demonstration and testing.

    The classifier labels a document as 'short' when the word count is
    below ``short_threshold``; otherwise it labels it as 'long'.
    """

    short_threshold: int = 50

    def classify(self, text: str) -> Dict[str, Any]:
        words = text.split()
        length = len(words)
        label = "short" if length < self.short_threshold else "long"
        return {"label": label, "words": length}


class LLMClassifier:
    """Placeholder for a classifier backed by a language model.

    This stub outlines the expected interface. Users can implement
    custom logic here that calls a remote API (e.g. OpenAI, Cohere).
    The current implementation simply raises ``NotImplementedError``.
    """

    def __init__(self, model: str = "gpt-3.5-turbo", temperature: float = 0.0) -> None:
        self.model = model
        self.temperature = temperature

    def classify(self, text: str) -> Dict[str, Any]:  # pragma: no cover - stub
        raise NotImplementedError("LLMClassifier is a stub. Provide your own implementation.")
