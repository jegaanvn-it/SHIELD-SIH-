"""Headless and unit tests for SARA Track U UI logic.

These tests run without calling mainloop() and use strictly temporary test databases.
"""

from __future__ import annotations

import os
from pathlib import Path
import tkinter as tk

import pytest

from sara.memory.storage import SQLiteStorage
from sara.providers.echo import EchoProvider
from sara.ui.app import SaraApp, default_database_path


def test_default_database_path_structure() -> None:
    db_path = default_database_path()
    assert db_path.name == "conversations.sqlite3"
    assert "track_u" in db_path.parts
    assert "Sara" in db_path.parts


def test_ui_initialization_and_send_message_headless(tmp_path: Path) -> None:
    db_file = tmp_path / "test_ui.sqlite3"
    storage = SQLiteStorage(db_file)
    provider = EchoProvider()

    root = tk.Tk()
    root.withdraw()  # Ensure window is never visible on screen

    try:
        app = SaraApp(root, storage, provider)

        # Initial state should have created one default conversation
        assert app.current_conversation_id is not None
        conv = storage.get_conversation(app.current_conversation_id)
        assert conv is not None
        assert conv.title == "New Chat"

        # Simulate user typing and sending a message
        app.input_entry.insert(0, "Testing Track U UI")
        app.send_message()

        # Input should be cleared
        assert app.input_entry.get() == ""

        # Storage should contain both user message and assistant echo
        messages = storage.get_messages(app.current_conversation_id)
        assert len(messages) == 2
        assert messages[0].role == "user"
        assert messages[0].content == "Testing Track U UI"
        assert messages[1].role == "assistant"
        assert messages[1].content == "Sara (echo): Testing Track U UI"

        # Conversation title should update from initial message
        updated_conv = storage.get_conversation(app.current_conversation_id)
        assert updated_conv is not None
        assert "Testing Track U UI" in updated_conv.title

        # Create another conversation
        app.create_new_conversation()
        assert len(storage.list_conversations()) == 2
    finally:
        storage.close()
        root.destroy()
