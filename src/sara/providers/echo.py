"""Deterministic local echo provider for Track U."""

from __future__ import annotations

from typing import Any

from sara.providers.base import BaseProvider


class EchoProvider(BaseProvider):
    """Local echo provider with no external dependencies or network activity."""

    def __init__(self, prefix: str = "Sara (echo): ") -> None:
        self.prefix = prefix

    def generate_response(
        self,
        prompt: str,
        history: list[dict[str, str]] | None = None,
        **kwargs: Any,
    ) -> str:
        """Echo back the user's prompt prefixed with a friendly marker."""
        cleaned = prompt.strip()
        if not cleaned:
            return f"{self.prefix}(empty message received)"
        return f"{self.prefix}{cleaned}"
