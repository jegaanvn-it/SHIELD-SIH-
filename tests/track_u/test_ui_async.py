"""Headless unit tests for asynchronous UI safety, thread boundaries, and conversation isolation."""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path
import threading
import time
import tkinter as tk
from typing import Any

import pytest

from sara.memory.storage import SQLiteStorage
from sara.providers.base import BaseProvider
from sara.ui.app import SaraApp


class ControllableAsyncProvider(BaseProvider):
    """Test provider that can pause execution until explicitly released."""

    def __init__(self, response: str = "Test answer", error: Exception | None = None) -> None:
        self.response = response
        self.error = error
        self.called_event = threading.Event()
        self.release_event = threading.Event()
        self.call_count = 0

    def generate_response(self, prompt: str, history: list[dict[str, str]] | None = None, **kwargs: Any) -> str:
        self.call_count += 1
        self.called_event.set()
        self.release_event.wait(timeout=2.0)
        if self.error:
            raise self.error
        return self.response


@pytest.fixture(scope="module")
def shared_tk_root() -> Generator[tk.Tk, None, None]:
    """Shared headless Tk instance for the module to avoid Tcl re-init corruption on Windows."""
    root = tk.Tk()
    root.withdraw()
    yield root
    try:
        root.destroy()
    except Exception:
        pass


@pytest.fixture(autouse=True)
def clean_tk_root(shared_tk_root: tk.Tk) -> Generator[tk.Tk, None, None]:
    """Ensure children widgets are cleared before and after each test."""
    for child in shared_tk_root.winfo_children():
        child.destroy()
    yield shared_tk_root
    for child in shared_tk_root.winfo_children():
        child.destroy()


def test_ui_async_conversation_switch_safety(clean_tk_root: tk.Tk, tmp_path: Path) -> None:
    db_file = tmp_path / "test_switch.sqlite3"
    storage = SQLiteStorage(db_file)
    provider = ControllableAsyncProvider(response="Answer for Chat 1")

    try:
        app = SaraApp(clean_tk_root, storage, provider)
        conv1_id = app.current_conversation_id
        assert conv1_id is not None

        # User types in Chat 1
        app.input_entry.insert(0, "Question in Chat 1")

        # Create Chat 2 before background generation completes
        conv2 = storage.create_conversation("Chat 2")
        app.refresh_conversation_list()

        # Trigger send on Chat 1 (spawns background worker)
        app.send_message()
        assert provider.called_event.wait(timeout=1.0)

        # User switches to Chat 2 while generation is in flight
        app.select_conversation(conv2.id)
        assert app.current_conversation_id == conv2.id

        # Release background worker
        provider.release_event.set()
        if app._current_worker:
            app._current_worker.join(timeout=1.0)

        # Drain the thread-safe queue on main thread
        app.drain_queue()

        # Chat 2 screen must NOT contain Chat 1's answer!
        chat2_text = app.chat_text.get("1.0", tk.END)
        assert "Answer for Chat 1" not in chat2_text

        # SQLite for Chat 1 MUST contain the answer!
        c1_messages = storage.get_messages(conv1_id)
        assert len(c1_messages) == 2
        assert c1_messages[0].content == "Question in Chat 1"
        assert c1_messages[1].content == "Answer for Chat 1"

        # When user switches back to Chat 1, both messages appear
        app.select_conversation(conv1_id)
        c1_screen_text = app.chat_text.get("1.0", tk.END)
        assert "Question in Chat 1" in c1_screen_text
        assert "Answer for Chat 1" in c1_screen_text
    finally:
        app._shutdown_event.set()
        if app._poll_id:
            try:
                clean_tk_root.after_cancel(app._poll_id)
            except Exception:
                pass
        storage.close()


def test_ui_failed_request_and_retry_deduplication(clean_tk_root: tk.Tk, tmp_path: Path) -> None:
    db_file = tmp_path / "test_retry.sqlite3"
    storage = SQLiteStorage(db_file)
    failing_provider = ControllableAsyncProvider(error=RuntimeError("Simulated network timeout"))
    failing_provider.release_event.set()

    try:
        app = SaraApp(clean_tk_root, storage, failing_provider)
        conv_id = app.current_conversation_id
        assert conv_id is not None

        app.input_entry.insert(0, "Retryable message")
        app.send_message()

        if app._current_worker:
            app._current_worker.join(timeout=1.0)
        app.drain_queue()

        # Screen should display error notice
        screen_text = app.chat_text.get("1.0", tk.END)
        assert "Simulated network timeout" in screen_text
        assert app._last_failed_prompt == (conv_id, "Retryable message")

        # Now fix provider and click Retry
        success_provider = ControllableAsyncProvider(response="Successful retry response")
        success_provider.release_event.set()
        app.provider = success_provider

        app.retry_last_failed()
        if app._current_worker:
            app._current_worker.join(timeout=1.0)
        app.drain_queue()

        # Verify SQLite has exactly 1 user message and 1 assistant message (no duplicates!)
        messages = storage.get_messages(conv_id)
        assert len(messages) == 2
        assert messages[0].role == "user"
        assert messages[0].content == "Retryable message"
        assert messages[1].role == "assistant"
        assert messages[1].content == "Successful retry response"
    finally:
        app._shutdown_event.set()
        if app._poll_id:
            try:
                clean_tk_root.after_cancel(app._poll_id)
            except Exception:
                pass
        storage.close()


def test_ui_shutdown_in_flight_safety(clean_tk_root: tk.Tk, tmp_path: Path) -> None:
    db_file = tmp_path / "test_shutdown.sqlite3"
    storage = SQLiteStorage(db_file)
    provider = ControllableAsyncProvider(response="Late answer")

    try:
        app = SaraApp(clean_tk_root, storage, provider)
        conv_id = app.current_conversation_id
        assert conv_id is not None

        app.input_entry.insert(0, "Pending prompt")
        app.send_message()
        assert provider.called_event.wait(timeout=1.0)

        # Trigger shutdown while worker is "in flight"
        app._shutdown_event.set()
        assert app._shutdown_event.is_set()

        # Release worker; it should finish safely without queuing or raising
        provider.release_event.set()
        if app._current_worker:
            app._current_worker.join(timeout=1.0)

        # Late queue drain or callback must safely do nothing
        app.drain_queue()
    finally:
        app._shutdown_event.set()
        if app._poll_id:
            try:
                clean_tk_root.after_cancel(app._poll_id)
            except Exception:
                pass
        storage.close()
