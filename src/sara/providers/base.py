"""Base provider interface for Project SARA."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseProvider(ABC):
    """Abstract interface for model and echo providers."""

    @abstractmethod
    def generate_response(
        self,
        prompt: str,
        history: list[dict[str, str]] | None = None,
        **kwargs: Any,
    ) -> str:
        """Generate a response string for the given prompt and optional conversation history."""
        raise NotImplementedError
