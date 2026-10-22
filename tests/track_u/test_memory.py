"""Unit tests for Track U SQLite conversation memory."""

from __future__ import annotations

from pathlib import Path
import sqlite3

import pytest

from sara.memory.storage import SQLiteStorage


def test_sqlite_storage_schema_version(tmp_path: Path) -> None:
    db_file = tmp_path / "test_schema.sqlite3"
    with SQLiteStorage(db_file) as storage:
        cursor = storage._conn.cursor()
        cursor.execute("PRAGMA user_version;")
        version = cursor.fetchone()[0]
        assert version == 1


def test_create_and_get_conversation(tmp_path: Path) -> None:
    db_file = tmp_path / "test_conv.sqlite3"
    with SQLiteStorage(db_file) as storage:
        conv = storage.create_conversation("My Project Discussion")
        assert conv.id is not None
        assert conv.title == "My Project Discussion"
        assert conv.created_at == conv.updated_at

        retrieved = storage.get_conversation(conv.id)
        assert retrieved is not None
        assert retrieved.id == conv.id
        assert retrieved.title == "My Project Discussion"


def test_list_conversations_ordered(tmp_path: Path) -> None:
    db_file = tmp_path / "test_list.sqlite3"
    with SQLiteStorage(db_file) as storage:
        c1 = storage.create_conversation("Chat 1")
        c2 = storage.create_conversation("Chat 2")

        # Adding a message to c1 updates its timestamp
        storage.add_message(c1.id, "user", "Activity in c1")

        convs = storage.list_conversations()
        assert len(convs) == 2
        # c1 should now be at the top because it was updated most recently
        assert convs[0].id == c1.id
        assert convs[1].id == c2.id


def test_update_conversation_title(tmp_path: Path) -> None:
    db_file = tmp_path / "test_title.sqlite3"
    with SQLiteStorage(db_file) as storage:
        conv = storage.create_conversation("Old Title")
        success = storage.update_conversation_title(conv.id, "Renamed Title")
        assert success is True

        updated = storage.get_conversation(conv.id)
        assert updated is not None
        assert updated.title == "Renamed Title"


def test_add_and_get_messages(tmp_path: Path) -> None:
    db_file = tmp_path / "test_msgs.sqlite3"
    with SQLiteStorage(db_file) as storage:
        conv = storage.create_conversation("Dialogue")
        m1 = storage.add_message(conv.id, "user", "What is SARA?")
        m2 = storage.add_message(conv.id, "assistant", "SARA is an assistant.")

        messages = storage.get_messages(conv.id)
        assert len(messages) == 2
        assert messages[0].id == m1.id
        assert messages[0].role == "user"
        assert messages[0].content == "What is SARA?"
        assert messages[1].id == m2.id
        assert messages[1].role == "assistant"
        assert messages[1].content == "SARA is an assistant."


def test_add_message_nonexistent_conversation_raises(tmp_path: Path) -> None:
    db_file = tmp_path / "test_err.sqlite3"
    with SQLiteStorage(db_file) as storage:
        with pytest.raises(ValueError, match="does not exist"):
            storage.add_message("nonexistent-id", "user", "Hello")


def test_delete_conversation_cascades_messages(tmp_path: Path) -> None:
    db_file = tmp_path / "test_del.sqlite3"
    with SQLiteStorage(db_file) as storage:
        conv = storage.create_conversation("To be deleted")
        storage.add_message(conv.id, "user", "Message to disappear")

        deleted = storage.delete_conversation(conv.id)
        assert deleted is True

        assert storage.get_conversation(conv.id) is None
        assert storage.get_messages(conv.id) == []


def test_storage_persistence_across_instances(tmp_path: Path) -> None:
    db_file = tmp_path / "test_persist.sqlite3"
    with SQLiteStorage(db_file) as storage:
        conv = storage.create_conversation("Persistent Chat")
        storage.add_message(conv.id, "user", "Saved text")

    # Reopen same database file with fresh instance
    with SQLiteStorage(db_file) as reopened:
        retrieved = reopened.get_conversation(conv.id)
        assert retrieved is not None
        assert retrieved.title == "Persistent Chat"

        messages = reopened.get_messages(conv.id)
        assert len(messages) == 1
        assert messages[0].content == "Saved text"
