"""Data models for SARA conversation memory."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


def utc_now_iso() -> str:
    """Return the current UTC timestamp formatted as an ISO-8601 string."""
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class Conversation:
    """Representation of a conversation thread."""

    id: str
    title: str
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class Message:
    """Representation of an individual message within a conversation."""

    id: int | None
    conversation_id: str
    role: str
    content: str
    created_at: str
