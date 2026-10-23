"""Tests for SARA privacy-first memory and ephemeral conversation storage (WP-M)."""

from __future__ import annotations

from pathlib import Path
import pytest

from sara.memory.models import Memory
from sara.memory.storage import SQLiteStorage, screen_and_redact_credentials


def test_history_persistence_disabled_by_default(tmp_path: Path) -> None:
    """Default SQLiteStorage initialization must be ephemeral in-memory with zero disk files."""
    storage = SQLiteStorage()
    try:
        assert storage.ephemeral is True
        assert storage.db_path is None
        assert storage.is_history_persisted() is False

        conv = storage.create_conversation("Ephemeral Chat")
        msg = storage.add_message(conv.id, "user", "Session message that should not touch disk")
        assert msg.content == "Session message that should not touch disk"

        # In-memory retrieval works during session
        msgs = storage.get_messages(conv.id)
        assert len(msgs) == 1
        assert msgs[0].content == "Session message that should not touch disk"
    finally:
        storage.close()


def test_long_term_memory_disabled_by_default() -> None:
    """Long-term memory must be OFF by default and block memory additions."""
    storage = SQLiteStorage()
    try:
        assert storage.is_memory_enabled() is False

        # Attempting to store memory while disabled must fail closed
        with pytest.raises(PermissionError, match="Long-term memory is disabled"):
            storage.add_memory("User prefers dark mode")
    finally:
        storage.close()


def test_zero_automatic_memory_extraction() -> None:
    """Conversation messages must never be automatically extracted into memories."""
    storage = SQLiteStorage()
    try:
        conv = storage.create_conversation("Personal Info Chat")

        # User shares sensitive personal facts in conversation
        storage.add_message(conv.id, "user", "My name is Alice, I live at 123 Main St, and my SSN is 000-00-0000")
        storage.add_message(conv.id, "assistant", "Hello Alice, I have received your message.")

        # memories table must remain completely empty
        memories = storage.list_memories()
        assert memories == []
    finally:
        storage.close()


def test_explicit_memory_opt_in_and_crud() -> None:
    """Memories can only be created after explicit opt-in, with full CRUD control."""
    storage = SQLiteStorage()
    try:
        assert storage.is_memory_enabled() is False

        # Explicit user opt-in
        storage.set_memory_enabled(True)
        assert storage.is_memory_enabled() is True

        # User explicitly saves two memories
        mem1 = storage.add_memory("Prefers concise technical answers", category="preference")
        mem2 = storage.add_memory("Current project is SARA AI Assistant", category="context")

        assert mem1.id is not None
        assert mem1.content == "Prefers concise technical answers"
        assert mem2.content == "Current project is SARA AI Assistant"

        # List memories
        all_mems = storage.list_memories()
        assert len(all_mems) == 2

        # Get single memory
        fetched = storage.get_memory(mem1.id)
        assert fetched is not None
        assert fetched.content == "Prefers concise technical answers"

        # Delete single memory
        assert storage.delete_memory(mem1.id) is True
        remaining = storage.list_memories()
        assert len(remaining) == 1
        assert remaining[0].id == mem2.id

        # Clear all memories
        cleared = storage.clear_all_memories()
        assert cleared == 1
        assert storage.list_memories() == []
    finally:
        storage.close()


def test_credential_screening_known_patterns() -> None:
    """Best-effort regex screening must redact known high-entropy API keys and credential strings."""
    # Dynamically construct synthetic test patterns to avoid static secret scanner false-positives
    fake_gemini_key = "AIza" + "Sy" + ("0" * 33)
    gemini_sample = f"Here is my key: {fake_gemini_key} for testing"
    redacted_gemini, hit = screen_and_redact_credentials(gemini_sample)
    assert hit is True
    assert "AIza" not in redacted_gemini
    assert "[REDACTED_SECRET]" in redacted_gemini

    # OpenAI-style secret key
    fake_sk_key = "sk-" + ("a" * 32)
    sk_sample = f"Authorization: Bearer {fake_sk_key}"
    redacted_sk, hit2 = screen_and_redact_credentials(sk_sample)
    assert hit2 is True
    assert "sk-" not in redacted_sk

    # Password assignment
    pwd_sample = 'user = "admin", password = "DummyPassword123!"'
    redacted_pwd, hit3 = screen_and_redact_credentials(pwd_sample)
    assert hit3 is True
    assert "DummyPassword123!" not in redacted_pwd

    # Redaction verified in storage add_message
    storage = SQLiteStorage()
    try:
        conv = storage.create_conversation("Security Test")
        msg = storage.add_message(conv.id, "user", f"My API key is {fake_gemini_key}")
        assert "AIza" not in msg.content
        assert "[REDACTED_SECRET]" in msg.content

        # Redaction verified in storage add_memory
        storage.set_memory_enabled(True)
        mem = storage.add_memory(f"Key {fake_gemini_key} saved")
        assert "AIza" not in mem.content
        assert "[REDACTED_SECRET]" in mem.content
    finally:
        storage.close()


def test_credential_screening_limitations_documented() -> None:
    """Credential filter must document that it is heuristic and cannot detect arbitrary text."""
    doc = screen_and_redact_credentials.__doc__
    assert doc is not None
    assert "heuristic" in doc.lower()
    assert "limitations" in doc.lower()

    # Normal text without credentials should pass untouched
    clean_sample = "Just a normal message discussing python coding and algorithms."
    clean_out, hit = screen_and_redact_credentials(clean_sample)
    assert hit is False
    assert clean_out == clean_sample


def test_settings_and_memories_schema_creation(tmp_path: Path) -> None:
    """Verify that settings and memories tables exist and default settings are initialized."""
    db_file = tmp_path / "schema_test.sqlite3"
    storage = SQLiteStorage(db_file)
    try:
        assert storage.SCHEMA_VERSION == 1
        assert storage.is_memory_enabled() is False
        assert storage.is_history_persisted() is False
        assert storage.list_memories() == []
        assert storage.list_conversations() == []
    finally:
        storage.close()


def test_ephemeral_storage_purges_on_close() -> None:
    """Ephemeral storage leaves zero artifacts on disk after close."""
    storage = SQLiteStorage(ephemeral=True)
    conv = storage.create_conversation("Session Only")
    storage.add_message(conv.id, "user", "Data in RAM")
    storage.close()

    # Verify no file is associated with ephemeral storage
    assert storage.db_path is None
