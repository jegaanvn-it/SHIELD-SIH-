"""Minimal Tkinter chat interface for SARA Track U prototype."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any

from sara.memory.models import Conversation, Message
from sara.memory.storage import SQLiteStorage
from sara.providers.base import BaseProvider
from sara.providers.echo import EchoProvider


class SaraApp:
    """Tkinter graphical chat application for Project SARA."""

    def __init__(
        self,
        root: tk.Tk,
        storage: SQLiteStorage,
        provider: BaseProvider,
    ) -> None:
        self.root = root
        self.storage = storage
        self.provider = provider

        self.current_conversation_id: str | None = None
        self._conversations_cache: list[Conversation] = []

        self._setup_window()
        self._create_widgets()
        self._load_conversations_on_start()

    def _setup_window(self) -> None:
        self.root.title("SARA — Assistant Prototype (Track U)")
        self.root.geometry("880x620")
        self.root.minsize(640, 480)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _create_widgets(self) -> None:
        # Style configuration
        style = ttk.Style(self.root)
        style.theme_use("clam")

        # Main horizontal paned layout
        self.paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.paned.pack(fill=tk.BOTH, expand=True)

        # Left sidebar frame
        self.sidebar_frame = ttk.Frame(self.paned, width=240, padding=10)
        self.paned.add(self.sidebar_frame, weight=1)

        # Sidebar Title
        self.sidebar_label = ttk.Label(
            self.sidebar_frame,
            text="Conversations",
            font=("Segoe UI", 12, "bold"),
        )
        self.sidebar_label.pack(fill=tk.X, pady=(0, 8))

        # "New Chat" button
        self.new_chat_btn = ttk.Button(
            self.sidebar_frame,
            text="➕ New Chat",
            command=self.create_new_conversation,
        )
        self.new_chat_btn.pack(fill=tk.X, pady=(0, 8))

        # Conversation Listbox with scrollbar
        self.listbox_frame = ttk.Frame(self.sidebar_frame)
        self.listbox_frame.pack(fill=tk.BOTH, expand=True)

        self.conv_listbox = tk.Listbox(
            self.listbox_frame,
            font=("Segoe UI", 10),
            activestyle="none",
            selectbackground="#0078d4",
            selectforeground="white",
            exportselection=False,
        )
        self.conv_scroll = ttk.Scrollbar(
            self.listbox_frame,
            orient=tk.VERTICAL,
            command=self.conv_listbox.yview,
        )
        self.conv_listbox.configure(yscrollcommand=self.conv_scroll.set)
        self.conv_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.conv_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.conv_listbox.bind("<<ListboxSelect>>", self._on_conversation_selected)

        # Delete conversation button
        self.del_chat_btn = ttk.Button(
            self.sidebar_frame,
            text="🗑 Delete Chat",
            command=self.delete_current_conversation,
        )
        self.del_chat_btn.pack(fill=tk.X, pady=(8, 0))

        # Right chat area frame
        self.chat_frame = ttk.Frame(self.paned, padding=10)
        self.paned.add(self.chat_frame, weight=4)

        # Chat header
        self.header_label = ttk.Label(
            self.chat_frame,
            text="Select or start a conversation",
            font=("Segoe UI", 12, "bold"),
        )
        self.header_label.pack(fill=tk.X, pady=(0, 8))

        # Chat message display (Text widget + Scrollbar)
        self.display_frame = ttk.Frame(self.chat_frame)
        self.display_frame.pack(fill=tk.BOTH, expand=True)

        self.chat_text = tk.Text(
            self.display_frame,
            wrap=tk.WORD,
            font=("Segoe UI", 10),
            state=tk.DISABLED,
            bg="#fdfdfd",
            padx=10,
            pady=10,
        )
        self.chat_scroll = ttk.Scrollbar(
            self.display_frame,
            orient=tk.VERTICAL,
            command=self.chat_text.yview,
        )
        self.chat_text.configure(yscrollcommand=self.chat_scroll.set)
        self.chat_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.chat_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Text tags for visual formatting
        self.chat_text.tag_configure("user_label", foreground="#005a9e", font=("Segoe UI", 10, "bold"))
        self.chat_text.tag_configure("assistant_label", foreground="#107c41", font=("Segoe UI", 10, "bold"))
        self.chat_text.tag_configure("time_label", foreground="#666666", font=("Segoe UI", 8))
        self.chat_text.tag_configure("msg_body", font=("Segoe UI", 10))

        # Input controls at bottom
        self.input_frame = ttk.Frame(self.chat_frame, padding=(0, 8, 0, 0))
        self.input_frame.pack(fill=tk.X)

        self.input_entry = ttk.Entry(self.input_frame, font=("Segoe UI", 10))
        self.input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        self.input_entry.bind("<Return>", lambda event: self.send_message())

        self.send_button = ttk.Button(
            self.input_frame,
            text="Send",
            command=self.send_message,
        )
        self.send_button.pack(side=tk.RIGHT)

    def _load_conversations_on_start(self) -> None:
        """Populate the sidebar on startup; create a default conversation if none exist."""
        self.refresh_conversation_list()
        if self._conversations_cache:
            self.select_conversation(self._conversations_cache[0].id)
        else:
            self.create_new_conversation()

    def refresh_conversation_list(self) -> None:
        """Reload conversation list from storage and update listbox."""
        self._conversations_cache = self.storage.list_conversations()
        self.conv_listbox.delete(0, tk.END)
        for conv in self._conversations_cache:
            self.conv_listbox.insert(tk.END, conv.title)

    def select_conversation(self, conversation_id: str) -> None:
        """Switch active conversation and load message history."""
        self.current_conversation_id = conversation_id
        conv = self.storage.get_conversation(conversation_id)
        if not conv:
            return

        self.header_label.config(text=conv.title)

        # Highlight matching index in listbox
        for idx, c in enumerate(self._conversations_cache):
            if c.id == conversation_id:
                self.conv_listbox.selection_clear(0, tk.END)
                self.conv_listbox.selection_set(idx)
                self.conv_listbox.activate(idx)
                break

        # Render message history
        messages = self.storage.get_messages(conversation_id)
        self._render_messages(messages)

    def _on_conversation_selected(self, event: Any) -> None:
        selection = self.conv_listbox.curselection()
        if selection and selection[0] < len(self._conversations_cache):
            selected_conv = self._conversations_cache[selection[0]]
            if selected_conv.id != self.current_conversation_id:
                self.select_conversation(selected_conv.id)

    def create_new_conversation(self) -> None:
        """Create a new conversation, refresh the sidebar, and switch to it."""
        conv = self.storage.create_conversation(title="New Chat")
        self.refresh_conversation_list()
        self.select_conversation(conv.id)
        self.input_entry.focus_set()

    def delete_current_conversation(self) -> None:
        """Delete currently selected conversation after user confirmation."""
        if not self.current_conversation_id:
            return
        if not messagebox.askyesno("Delete Conversation", "Are you sure you want to delete this conversation?"):
            return

        self.storage.delete_conversation(self.current_conversation_id)
        self.current_conversation_id = None
        self._load_conversations_on_start()

    def _render_messages(self, messages: list[Message]) -> None:
        """Clear and redraw message list in chat text area."""
        self.chat_text.config(state=tk.NORMAL)
        self.chat_text.delete("1.0", tk.END)
        for msg in messages:
            self._append_message_to_view(msg)
        self.chat_text.config(state=tk.DISABLED)
        self.chat_text.see(tk.END)

    def _append_message_to_view(self, msg: Message) -> None:
        """Append a single message block to the chat text view."""
        is_user = msg.role.lower() == "user"
        label_tag = "user_label" if is_user else "assistant_label"
        sender_name = "You" if is_user else "Sara (echo)"

        # Sender label
        self.chat_text.insert(tk.END, f"{sender_name}  ", label_tag)
        # Timestamp
        time_display = msg.created_at[11:16] if len(msg.created_at) >= 16 else ""
        if time_display:
            self.chat_text.insert(tk.END, f"{time_display}\n", "time_label")
        else:
            self.chat_text.insert(tk.END, "\n")
        # Content
        self.chat_text.insert(tk.END, f"{msg.content}\n\n", "msg_body")

    def send_message(self) -> None:
        """Process sending the current input prompt to the echo provider."""
        text = self.input_entry.get().strip()
        if not text:
            return
        if not self.current_conversation_id:
            self.create_new_conversation()

        assert self.current_conversation_id is not None
        conv_id = self.current_conversation_id

        # 1. Store and display user message
        user_msg = self.storage.add_message(conv_id, "user", text)
        self.chat_text.config(state=tk.NORMAL)
        self._append_message_to_view(user_msg)

        # Clear input field
        self.input_entry.delete(0, tk.END)

        # Update title if it's the first message of a default-named chat
        conv = self.storage.get_conversation(conv_id)
        if conv and conv.title == "New Chat":
            new_title = text[:30] + ("…" if len(text) > 30 else "")
            self.storage.update_conversation_title(conv_id, new_title)
            self.header_label.config(text=new_title)
            self.refresh_conversation_list()
            # Restore selection highlight
            for idx, c in enumerate(self._conversations_cache):
                if c.id == conv_id:
                    self.conv_listbox.selection_set(idx)
                    break

        # 2. Generate echo provider response
        response_text = self.provider.generate_response(text)

        # 3. Store and display assistant response
        assistant_msg = self.storage.add_message(conv_id, "assistant", response_text)
        self._append_message_to_view(assistant_msg)

        self.chat_text.config(state=tk.DISABLED)
        self.chat_text.see(tk.END)

    def _on_close(self) -> None:
        """Cleanup and close storage on application termination."""
        try:
            self.storage.close()
        finally:
            self.root.destroy()


def default_database_path() -> Path:
    """Resolve the default Track U runtime database location."""
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        base = Path(local_app_data)
    else:
        base = Path.home() / "AppData" / "Local"
    return base / "Sara" / "track_u" / "conversations.sqlite3"


def main(argv: list[str] | None = None) -> None:
    """CLI entrypoint for launching SARA Track U application."""
    parser = argparse.ArgumentParser(description="SARA Track U Prototype UI")
    parser.add_argument(
        "--database",
        type=str,
        default=None,
        help="Path to SQLite database file",
    )
    args = parser.parse_args(argv)

    db_path = Path(args.database) if args.database else default_database_path()
    storage = SQLiteStorage(db_path)
    provider = EchoProvider()

    root = tk.Tk()
    app = SaraApp(root, storage, provider)
    root.mainloop()


if __name__ == "__main__":
    main()
