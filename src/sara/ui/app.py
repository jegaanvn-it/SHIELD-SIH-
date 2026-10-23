"""Tkinter chat interface for SARA desktop application with asynchronous AI support."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import queue
import sys
import threading
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
from typing import Any

from sara.config import get_gemini_api_key, get_gemini_model
from sara.memory.models import Conversation, Message
from sara.memory.storage import SQLiteStorage
from sara.providers.base import BaseProvider
from sara.providers.echo import EchoProvider
from sara.providers.gemini import GeminiProvider, GeminiProviderError


class SaraApp:
    """Tkinter graphical chat application for Project SARA with thread-safe async execution."""

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
        self._in_flight: bool = False
        self._current_worker: threading.Thread | None = None
        self._shutdown_event = threading.Event()
        self._last_failed_prompt: tuple[str, str] | None = None
        self._response_queue: queue.Queue[tuple[str, str, str | None, str | None]] = queue.Queue()
        self._poll_id: str | None = None

        self._setup_window()
        self._create_widgets()
        self._load_conversations_on_start()
        self._start_queue_poll()

    def _setup_window(self) -> None:
        self.root.title("SARA — Personal AI Assistant")
        self.root.geometry("900x640")
        self.root.minsize(680, 500)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _create_widgets(self) -> None:
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

        # Provider indicator badge
        provider_name = "Gemini AI" if isinstance(self.provider, GeminiProvider) else "Echo Mode"
        self.provider_badge = ttk.Label(
            self.sidebar_frame,
            text=f"Brain: {provider_name}",
            font=("Segoe UI", 9, "italic"),
            foreground="#555555",
        )
        self.provider_badge.pack(fill=tk.X, pady=(4, 2))

        # Storage mode badge
        storage_mode = "Ephemeral (RAM)" if getattr(self.storage, "ephemeral", False) else "Persistent (Disk)"
        self.storage_badge = ttk.Label(
            self.sidebar_frame,
            text=f"Storage: {storage_mode}",
            font=("Segoe UI", 9, "italic"),
            foreground="#555555",
        )
        self.storage_badge.pack(fill=tk.X, pady=(0, 4))

        # Delete conversation button
        self.del_chat_btn = ttk.Button(
            self.sidebar_frame,
            text="🗑 Delete Chat",
            command=self.delete_current_conversation,
        )
        self.del_chat_btn.pack(fill=tk.X, pady=(4, 0))

        # Privacy & Memory settings button
        self.privacy_btn = ttk.Button(
            self.sidebar_frame,
            text="🔒 Privacy & Memory",
            command=self.open_privacy_dialog,
        )
        self.privacy_btn.pack(fill=tk.X, pady=(4, 0))

        # Right chat area frame
        self.chat_frame = ttk.Frame(self.paned, padding=10)
        self.paned.add(self.chat_frame, weight=4)

        # Chat header frame
        self.header_frame = ttk.Frame(self.chat_frame)
        self.header_frame.pack(fill=tk.X, pady=(0, 6))

        self.header_label = ttk.Label(
            self.header_frame,
            text="Select or start a conversation",
            font=("Segoe UI", 12, "bold"),
        )
        self.header_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.status_label = ttk.Label(
            self.header_frame,
            text="",
            font=("Segoe UI", 9, "italic"),
            foreground="#0078d4",
        )
        self.status_label.pack(side=tk.RIGHT, padx=5)

        # Chat message display (Text widget + Scrollbar)
        self.display_frame = ttk.Frame(self.chat_frame)
        self.display_frame.pack(fill=tk.BOTH, expand=True)

        self.chat_text = tk.Text(
            self.display_frame,
            wrap=tk.WORD,
            font=("Segoe UI", 10),
            state=tk.DISABLED,
            bg="#fdfdfd",
            padx=12,
            pady=12,
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
        self.chat_text.tag_configure("error_label", foreground="#d83b01", font=("Segoe UI", 10, "bold"))
        self.chat_text.tag_configure("time_label", foreground="#767676", font=("Segoe UI", 8))
        self.chat_text.tag_configure("msg_body", font=("Segoe UI", 10))
        self.chat_text.tag_configure("error_body", foreground="#a80000", font=("Segoe UI", 9, "italic"))

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

        self.retry_button = ttk.Button(
            self.input_frame,
            text="↻ Retry",
            command=self.retry_last_failed,
        )
        # Initially hidden until an error occurs
        # self.retry_button.pack(side=tk.RIGHT, padx=(0, 4))

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

        # Hide retry button unless this conversation has a pending failed prompt
        if self._last_failed_prompt and self._last_failed_prompt[0] == conversation_id:
            self.retry_button.pack(side=tk.RIGHT, padx=(0, 4))
        else:
            self.retry_button.pack_forget()

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

        if self._last_failed_prompt and self._last_failed_prompt[0] == self.current_conversation_id:
            self._last_failed_prompt = None

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
        sender_name = "You" if is_user else "SARA"

        self.chat_text.insert(tk.END, f"{sender_name}  ", label_tag)
        time_display = msg.created_at[11:16] if len(msg.created_at) >= 16 else ""
        if time_display:
            self.chat_text.insert(tk.END, f"{time_display}\n", "time_label")
        else:
            self.chat_text.insert(tk.END, "\n")
        self.chat_text.insert(tk.END, f"{msg.content}\n\n", "msg_body")

    def _append_error_notice_to_view(self, error_text: str) -> None:
        """Display an inline error card in the chat log without saving it as an assistant message."""
        self.chat_text.insert(tk.END, "⚠️ SARA Notice  \n", "error_label")
        self.chat_text.insert(tk.END, f"{error_text}\n\n", "error_body")

    def _set_input_state(self, is_active: bool, status_msg: str = "") -> None:
        """Update input widgets and in-flight status flag safely on the main thread."""
        self._in_flight = not is_active
        state = tk.NORMAL if is_active else tk.DISABLED
        self.send_button.config(state=state)
        self.input_entry.config(state=state)
        self.status_label.config(text=status_msg)

    def send_message(self) -> None:
        """Initiate asynchronous generation for user input."""
        if self._in_flight:
            return

        text = self.input_entry.get().strip()
        if not text:
            return

        if not self.current_conversation_id:
            self.create_new_conversation()

        assert self.current_conversation_id is not None
        conv_id = self.current_conversation_id

        # 1. Store and display user message on main thread
        user_msg = self.storage.add_message(conv_id, "user", text)
        self.chat_text.config(state=tk.NORMAL)
        self._append_message_to_view(user_msg)
        self.chat_text.config(state=tk.DISABLED)
        self.chat_text.see(tk.END)

        # Clear input field and remove retry button
        self.input_entry.delete(0, tk.END)
        self.retry_button.pack_forget()
        self._last_failed_prompt = None

        # Update title if it's the first message of a default-named chat
        conv = self.storage.get_conversation(conv_id)
        if conv and conv.title == "New Chat":
            new_title = text[:30] + ("…" if len(text) > 30 else "")
            self.storage.update_conversation_title(conv_id, new_title)
            self.header_label.config(text=new_title)
            self.refresh_conversation_list()
            for idx, c in enumerate(self._conversations_cache):
                if c.id == conv_id:
                    self.conv_listbox.selection_set(idx)
                    break

        # For EchoProvider (deterministic local echo), execute synchronously on main thread
        # This preserves instant offline responsiveness and Track U headless testing
        if isinstance(self.provider, EchoProvider):
            try:
                response_text = self.provider.generate_response(text)
                assistant_msg = self.storage.add_message(conv_id, "assistant", response_text)
                self.chat_text.config(state=tk.NORMAL)
                self._append_message_to_view(assistant_msg)
                self.chat_text.config(state=tk.DISABLED)
                self.chat_text.see(tk.END)
            except Exception as exc:
                self.chat_text.config(state=tk.NORMAL)
                self._append_error_notice_to_view(str(exc))
                self.chat_text.config(state=tk.DISABLED)
                self.chat_text.see(tk.END)
            return

        # Extract bounded history on main thread (safe from SQLite thread boundary)
        history_msgs = self.storage.get_messages(conv_id)
        history = [
            {"role": m.role, "content": m.content}
            for m in history_msgs[:-1]  # Exclude the prompt just added
        ]

        # 2. Lock UI and display in-flight status
        self._set_input_state(is_active=False, status_msg="SARA is thinking…")

        # 3. Spawn background worker thread
        worker = threading.Thread(
            target=self._worker_generate_response,
            args=(conv_id, text, history),
            daemon=True,
            name=f"SaraWorker-{conv_id[:8]}",
        )
        self._current_worker = worker
        worker.start()

    def retry_last_failed(self) -> None:
        """Retry sending the last failed prompt without creating duplicate user messages."""
        if self._in_flight or not self._last_failed_prompt:
            return

        conv_id, prompt_text = self._last_failed_prompt
        if self.current_conversation_id != conv_id:
            return

        self.retry_button.pack_forget()
        self._last_failed_prompt = None

        # Extract context history
        history_msgs = self.storage.get_messages(conv_id)
        history = [
            {"role": m.role, "content": m.content}
            for m in history_msgs[:-1]
        ]

        self._set_input_state(is_active=False, status_msg="SARA is retrying…")
        worker = threading.Thread(
            target=self._worker_generate_response,
            args=(conv_id, prompt_text, history),
            daemon=True,
            name=f"SaraRetryWorker-{conv_id[:8]}",
        )
        self._current_worker = worker
        worker.start()

    def _worker_generate_response(
        self,
        request_conv_id: str,
        prompt: str,
        history: list[dict[str, str]],
    ) -> None:
        """Background thread worker: executes API call with zero SQLite or Tkinter interaction."""
        response_text: str | None = None
        error_msg: str | None = None

        try:
            response_text = self.provider.generate_response(prompt, history=history)
        except Exception as exc:
            error_msg = str(exc)

        # Enqueue response tuple for main-thread consumption without touching Tkinter widgets
        if not self._shutdown_event.is_set():
            self._response_queue.put((request_conv_id, prompt, response_text, error_msg))

    def _start_queue_poll(self) -> None:
        """Poll the response queue periodically on the main thread."""
        if not self._shutdown_event.is_set():
            self.drain_queue()
            try:
                self._poll_id = self.root.after(30, self._start_queue_poll)
            except Exception:
                pass

    def drain_queue(self) -> None:
        """Process all queued responses on the main Tkinter thread."""
        while not self._shutdown_event.is_set():
            try:
                item = self._response_queue.get_nowait()
            except queue.Empty:
                break
            request_conv_id, prompt, response_text, error_msg = item
            self._on_generation_complete(request_conv_id, prompt, response_text, error_msg)

    def _on_generation_complete(
        self,
        request_conv_id: str,
        prompt: str,
        response_text: str | None,
        error_msg: str | None,
    ) -> None:
        """Main thread callback: safely update SQLite and GUI with generation outcome."""
        if self._shutdown_event.is_set():
            return

        # Restore input UI controls
        self._set_input_state(is_active=True, status_msg="")
        self.input_entry.focus_set()

        # Handle API or Network Error
        if error_msg or not response_text:
            err = error_msg or "SARA received an empty response from the provider."
            self._last_failed_prompt = (request_conv_id, prompt)

            # If user is still viewing the conversation where error occurred:
            if self.current_conversation_id == request_conv_id:
                self.chat_text.config(state=tk.NORMAL)
                self._append_error_notice_to_view(err)
                self.chat_text.config(state=tk.DISABLED)
                self.chat_text.see(tk.END)
                self.retry_button.pack(side=tk.RIGHT, padx=(0, 4))
            return

        # Handle Success: persist assistant response on MAIN thread
        assistant_msg = self.storage.add_message(request_conv_id, "assistant", response_text)

        # Check if user is still on the originating conversation
        if self.current_conversation_id == request_conv_id:
            self.chat_text.config(state=tk.NORMAL)
            self._append_message_to_view(assistant_msg)
            self.chat_text.config(state=tk.DISABLED)
            self.chat_text.see(tk.END)
        else:
            # User switched conversation! Do NOT render in current view.
            # Refresh sidebar so timestamp and preview are up to date.
            self.refresh_conversation_list()
            # Restore selection highlight on active conversation
            for idx, c in enumerate(self._conversations_cache):
                if c.id == self.current_conversation_id:
                    self.conv_listbox.selection_set(idx)
                    break

    def open_privacy_dialog(self) -> None:
        """Display the Privacy, Ephemeral Storage, and Long-Term Memory controls dialog."""
        dialog = tk.Toplevel(self.root)
        dialog.title("SARA — Privacy & Memory Management")
        dialog.geometry("620x560")
        dialog.minsize(500, 460)
        dialog.transient(self.root)
        dialog.grab_set()

        frame = ttk.Frame(dialog, padding=16)
        frame.pack(fill=tk.BOTH, expand=True)

        # Header
        ttk.Label(
            frame,
            text="🔒 Privacy & Storage Controls",
            font=("Segoe UI", 13, "bold"),
        ).pack(anchor=tk.W, pady=(0, 6))

        # Disclosure note
        disclosure_box = tk.Text(
            frame,
            wrap=tk.WORD,
            height=5,
            font=("Segoe UI", 9),
            bg="#f4f4f4",
            relief=tk.FLAT,
            padx=8,
            pady=8,
        )
        disclosure_box.insert(
            tk.END,
            "• Ephemeral Default: Conversation history is held strictly in RAM by default and is wiped when SARA exits.\n"
            "• Network Boundary: When you send a message, that message and recent turns leave your PC over HTTPS to Google Gemini. Local controls do not purge provider-side logs.\n"
            "• Credential Shield: Best-effort regex redacts common API keys before storage, but cannot detect arbitrary passwords. Never enter sensitive credentials."
        )
        disclosure_box.config(state=tk.DISABLED)
        disclosure_box.pack(fill=tk.X, pady=(0, 10))

        # Status indicators
        status_frame = ttk.LabelFrame(frame, text="Current Configuration", padding=10)
        status_frame.pack(fill=tk.X, pady=(0, 10))

        ephemeral_text = "Ephemeral (In-Memory Only, Zero Disk Trace)" if getattr(self.storage, "ephemeral", False) else "Persistent (Local SQLite Disk)"
        ttk.Label(status_frame, text=f"Local Storage Mode: {ephemeral_text}", font=("Segoe UI", 9, "bold")).pack(anchor=tk.W, pady=2)

        mem_status_text = "Enabled (User Opt-in)" if self.storage.is_memory_enabled() else "Disabled (Default OFF — Zero Auto-Extraction)"
        mem_label = ttk.Label(status_frame, text=f"Long-Term Memory: {mem_status_text}", font=("Segoe UI", 9))
        mem_label.pack(anchor=tk.W, pady=2)

        # Memory controls frame
        mem_frame = ttk.LabelFrame(frame, text="Long-Term Memories (Explicit Only)", padding=10)
        mem_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Toggle memory button
        def toggle_memory() -> None:
            currently_enabled = self.storage.is_memory_enabled()
            if not currently_enabled:
                if messagebox.askyesno(
                    "Enable Memory",
                    "Enable cross-session memory?\n\nSARA will only store memories when you explicitly create them. Personal details are never automatically collected.",
                    parent=dialog,
                ):
                    self.storage.set_memory_enabled(True)
            else:
                self.storage.set_memory_enabled(False)
            new_status = "Enabled (User Opt-in)" if self.storage.is_memory_enabled() else "Disabled (Default OFF — Zero Auto-Extraction)"
            mem_label.config(text=f"Long-Term Memory: {new_status}")
            refresh_mem_list()

        toggle_btn = ttk.Button(mem_frame, text="Toggle Memory Setting", command=toggle_memory)
        toggle_btn.pack(anchor=tk.W, pady=(0, 6))

        # Memory listbox
        list_container = ttk.Frame(mem_frame)
        list_container.pack(fill=tk.BOTH, expand=True)

        mem_listbox = tk.Listbox(list_container, font=("Segoe UI", 9), activestyle="none")
        mem_scroll = ttk.Scrollbar(list_container, orient=tk.VERTICAL, command=mem_listbox.yview)
        mem_listbox.configure(yscrollcommand=mem_scroll.set)
        mem_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        mem_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        mem_cache: list[Any] = []

        def refresh_mem_list() -> None:
            nonlocal mem_cache
            mem_listbox.delete(0, tk.END)
            mem_cache = self.storage.list_memories()
            if not mem_cache:
                mem_listbox.insert(tk.END, "(No memories stored)")
                return
            for m in mem_cache:
                snippet = m.content[:60] + ("…" if len(m.content) > 60 else "")
                mem_listbox.insert(tk.END, f"[{m.created_at[:10]}] {snippet}")

        refresh_mem_list()

        # Memory Action buttons
        btn_row = ttk.Frame(mem_frame)
        btn_row.pack(fill=tk.X, pady=(6, 0))

        def add_custom_memory() -> None:
            if not self.storage.is_memory_enabled():
                messagebox.showwarning("Memory Disabled", "Please enable long-term memory first.", parent=dialog)
                return
            fact = simpledialog.askstring("Add Memory", "Enter user-approved fact or preference to remember:", parent=dialog)
            if fact and fact.strip():
                try:
                    self.storage.add_memory(fact.strip())
                    refresh_mem_list()
                except Exception as exc:
                    messagebox.showerror("Error", str(exc), parent=dialog)

        def delete_selected_memory() -> None:
            sel = mem_listbox.curselection()
            if not sel or not mem_cache:
                return
            mem_item = mem_cache[sel[0]]
            if mem_item.id is not None:
                self.storage.delete_memory(mem_item.id)
                refresh_mem_list()

        def clear_all_mems() -> None:
            if messagebox.askyesno("Clear All", "Delete all long-term memories?", parent=dialog):
                self.storage.clear_all_memories()
                refresh_mem_list()

        ttk.Button(btn_row, text="➕ Add Memory", command=add_custom_memory).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Button(btn_row, text="🗑 Delete Selected", command=delete_selected_memory).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Button(btn_row, text="🔥 Clear All", command=clear_all_mems).pack(side=tk.RIGHT)

        # Dialog close button
        ttk.Button(frame, text="Close", command=dialog.destroy).pack(anchor=tk.E, pady=(8, 0))

    def _on_close(self) -> None:
        """Gracefully handle window close during active requests."""
        self._shutdown_event.set()
        if self._poll_id:
            try:
                self.root.after_cancel(self._poll_id)
            except Exception:
                pass
            self._poll_id = None
        if self._current_worker and self._current_worker.is_alive():
            self._current_worker.join(timeout=0.3)
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


def create_default_provider() -> BaseProvider:
    """Instantiate GeminiProvider if GEMINI_API_KEY is present; fallback to EchoProvider."""
    api_key = get_gemini_api_key()
    if api_key:
        return GeminiProvider(api_key=api_key, model=get_gemini_model())
    return EchoProvider()


def main(argv: list[str] | None = None) -> None:
    """CLI entrypoint for launching SARA application."""
    parser = argparse.ArgumentParser(description="SARA Personal AI Assistant")
    parser.add_argument(
        "--database",
        type=str,
        default=None,
        help="Path to SQLite database file (activates disk persistence)",
    )
    parser.add_argument(
        "--persist",
        action="store_true",
        default=False,
        help="Enable persistent local disk storage (default: ephemeral in-memory)",
    )
    parser.add_argument(
        "--provider",
        type=str,
        choices=["auto", "gemini", "echo"],
        default="auto",
        help="AI provider to use (default: auto)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Gemini model ID override (e.g., gemini-2.5-flash)",
    )
    args = parser.parse_args(argv)

    if args.database:
        storage = SQLiteStorage(Path(args.database), ephemeral=False)
    elif args.persist:
        storage = SQLiteStorage(default_database_path(), ephemeral=False)
    else:
        # Default: Session-only ephemeral in-memory mode (zero disk trace)
        storage = SQLiteStorage(ephemeral=True)

    # Provider selection
    if args.provider == "echo":
        provider: BaseProvider = EchoProvider()
    elif args.provider == "gemini":
        provider = GeminiProvider(model=args.model)
    else:
        # Auto mode
        provider = create_default_provider()
        if args.model and isinstance(provider, GeminiProvider):
            provider.model = args.model

    root = tk.Tk()
    app = SaraApp(root, storage, provider)
    root.mainloop()


if __name__ == "__main__":
    main()
