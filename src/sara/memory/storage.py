"""SQLite conversation and privacy-first memory storage for Project SARA."""

from __future__ import annotations

import os
from pathlib import Path
import re
import sqlite3
import uuid

from sara.memory.models import Conversation, Memory, Message, utc_now_iso

# Best-effort screening patterns for high-entropy tokens and credentials
CREDENTIAL_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"AIza[0-9A-Za-z-_]{35}"),  # Google / Gemini API key
    re.compile(r"sk-[0-9A-Za-z]{32,}"),    # OpenAI / Anthropic-style secret key
    re.compile(r"ghp_[0-9A-Za-z]{36}"),    # GitHub personal access token
    re.compile(r"Bearer\s+[a-zA-Z0-9_\-\.]{20,}", re.IGNORECASE),  # Bearer token
    re.compile(r"(?:api_key|password|secret|token)\s*=\s*['\"][^'\"]+['\"]", re.IGNORECASE),
]


def screen_and_redact_credentials(text: str) -> tuple[str, bool]:
    """Best-effort regex screening to redact common high-entropy API keys and credential strings.

    Limitations:
        This filter is heuristic regex pattern matching. It catches well-known standard API
        key prefixes and assignment patterns, but cannot reliably detect arbitrary natural
        language passphrases, custom token formats, or obfuscated secrets without high
        false-positive rates. Users must never input credentials into the assistant.
    """
    redacted = text
    was_redacted = False
    for pattern in CREDENTIAL_PATTERNS:
        if pattern.search(redacted):
            redacted = pattern.sub("[REDACTED_SECRET]", redacted)
            was_redacted = True
    return redacted, was_redacted


class SQLiteStorage:
    """Thread-safe SQLite storage for conversations and memory with schema versioning and privacy defaults."""

    SCHEMA_VERSION = 1

    def __init__(
        self,
        db_path: str | Path | None = None,
        ephemeral: bool | None = None,
    ) -> None:
        """Initialize storage. Defaults to ephemeral in-memory unless db_path is explicitly provided."""
        if ephemeral is True or (ephemeral is None and db_path is None):
            self.ephemeral = True
            self.db_path: Path | None = None
            self._conn = sqlite3.connect(":memory:", check_same_thread=False)
        else:
            self.ephemeral = False
            self.db_path = Path(db_path).resolve()  # type: ignore[arg-type]
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)

        self._conn.row_factory = sqlite3.Row
        self._apply_pragmas()
        self._run_migrations()

    def _apply_pragmas(self) -> None:
        """Apply required SQLite runtime PRAGMAs."""
        cursor = self._conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;")
        cursor.execute("PRAGMA busy_timeout = 5000;")
        self._conn.commit()

    def _run_migrations(self) -> None:
        """Run database schema migrations checking PRAGMA user_version."""
        cursor = self._conn.cursor()
        cursor.execute("PRAGMA user_version;")
        row = cursor.fetchone()
        current_version = row[0] if row else 0

        if current_version < 1:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
                );
                """
            )
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_messages_conversation_id
                ON messages(conversation_id, id);
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                """
            )
            # Default settings: memory_enabled=0 (OFF), persist_history=0 (OFF)
            now = utc_now_iso()
            cursor.execute(
                """
                INSERT OR IGNORE INTO settings (key, value, updated_at)
                VALUES ('memory_enabled', '0', ?), ('persist_history', '0', ?);
                """,
                (now, now),
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content TEXT NOT NULL,
                    category TEXT NOT NULL DEFAULT 'general',
                    source_conversation_id TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (source_conversation_id) REFERENCES conversations(id) ON DELETE SET NULL
                );
                """
            )
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_memories_created
                ON memories(created_at DESC);
                """
            )
            cursor.execute(f"PRAGMA user_version = {self.SCHEMA_VERSION};")
            self._conn.commit()

    def get_setting(self, key: str, default: str = "") -> str:
        """Retrieve a stored setting value by key."""
        cursor = self._conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key = ?;", (key,))
        row = cursor.fetchone()
        return str(row["value"]) if row else default

    def set_setting(self, key: str, value: str) -> None:
        """Store or update a setting value."""
        now = utc_now_iso()
        cursor = self._conn.cursor()
        cursor.execute(
            """
            INSERT INTO settings (key, value, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at;
            """,
            (key, value, now),
        )
        self._conn.commit()

    def is_memory_enabled(self) -> bool:
        """Check whether cross-session long-term memory is enabled (default False)."""
        return self.get_setting("memory_enabled", "0") == "1"

    def set_memory_enabled(self, enabled: bool) -> None:
        """Explicitly enable or disable cross-session long-term memory."""
        self.set_setting("memory_enabled", "1" if enabled else "0")

    def is_history_persisted(self) -> bool:
        """Check whether local conversation history persistence is enabled (default False)."""
        return self.get_setting("persist_history", "0") == "1"

    def set_history_persisted(self, persisted: bool) -> None:
        """Explicitly enable or disable local conversation history persistence."""
        self.set_setting("persist_history", "1" if persisted else "0")

    def create_conversation(
        self,
        title: str = "New Chat",
        conversation_id: str | None = None,
    ) -> Conversation:
        """Create and store a new conversation thread."""
        conv_id = conversation_id or str(uuid.uuid4())
        now = utc_now_iso()
        cursor = self._conn.cursor()
        cursor.execute(
            """
            INSERT INTO conversations (id, title, created_at, updated_at)
            VALUES (?, ?, ?, ?);
            """,
            (conv_id, title.strip() or "New Chat", now, now),
        )
        self._conn.commit()
        return Conversation(id=conv_id, title=title, created_at=now, updated_at=now)

    def get_conversation(self, conversation_id: str) -> Conversation | None:
        """Retrieve a conversation by its unique ID."""
        cursor = self._conn.cursor()
        cursor.execute(
            "SELECT id, title, created_at, updated_at FROM conversations WHERE id = ?;",
            (conversation_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None
        return Conversation(
            id=row["id"],
            title=row["title"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def list_conversations(self) -> list[Conversation]:
        """List all conversations ordered by most recently updated."""
        cursor = self._conn.cursor()
        cursor.execute(
            """
            SELECT id, title, created_at, updated_at
            FROM conversations
            ORDER BY updated_at DESC;
            """
        )
        return [
            Conversation(
                id=row["id"],
                title=row["title"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )
            for row in cursor.fetchall()
        ]

    def update_conversation_title(self, conversation_id: str, new_title: str) -> bool:
        """Update the title of an existing conversation."""
        now = utc_now_iso()
        cursor = self._conn.cursor()
        cursor.execute(
            """
            UPDATE conversations
            SET title = ?, updated_at = ?
            WHERE id = ?;
            """,
            (new_title.strip() or "Untitled", now, conversation_id),
        )
        self._conn.commit()
        return cursor.rowcount > 0

    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation and all its associated messages."""
        cursor = self._conn.cursor()
        cursor.execute(
            "DELETE FROM conversations WHERE id = ?;",
            (conversation_id,),
        )
        self._conn.commit()
        return cursor.rowcount > 0

    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
    ) -> Message:
        """Add a message to a conversation after credential screening and update updated_at."""
        now = utc_now_iso()
        cursor = self._conn.cursor()

        # Ensure conversation exists
        cursor.execute(
            "SELECT id FROM conversations WHERE id = ?;",
            (conversation_id,),
        )
        if not cursor.fetchone():
            raise ValueError(f"Conversation with id '{conversation_id}' does not exist.")

        sanitized_content, _ = screen_and_redact_credentials(content)

        cursor.execute(
            """
            INSERT INTO messages (conversation_id, role, content, created_at)
            VALUES (?, ?, ?, ?);
            """,
            (conversation_id, role.strip().lower(), sanitized_content, now),
        )
        msg_id = cursor.lastrowid

        # Update conversation timestamp
        cursor.execute(
            "UPDATE conversations SET updated_at = ? WHERE id = ?;",
            (now, conversation_id),
        )
        self._conn.commit()

        return Message(
            id=msg_id,
            conversation_id=conversation_id,
            role=role.strip().lower(),
            content=sanitized_content,
            created_at=now,
        )

    def get_messages(self, conversation_id: str) -> list[Message]:
        """Retrieve all messages in a conversation ordered chronologically."""
        cursor = self._conn.cursor()
        cursor.execute(
            """
            SELECT id, conversation_id, role, content, created_at
            FROM messages
            WHERE conversation_id = ?
            ORDER BY id ASC;
            """,
            (conversation_id,),
        )
        return [
            Message(
                id=row["id"],
                conversation_id=row["conversation_id"],
                role=row["role"],
                content=row["content"],
                created_at=row["created_at"],
            )
            for row in cursor.fetchall()
        ]

    def add_memory(
        self,
        content: str,
        category: str = "general",
        source_conversation_id: str | None = None,
    ) -> Memory:
        """Store a user-approved long-term memory. Fails closed if memory is disabled."""
        if not self.is_memory_enabled():
            raise PermissionError(
                "Long-term memory is disabled. User must explicitly enable memory before saving memories."
            )

        sanitized_content, _ = screen_and_redact_credentials(content.strip())
        if not sanitized_content:
            raise ValueError("Memory content cannot be empty.")

        now = utc_now_iso()
        cursor = self._conn.cursor()
        cursor.execute(
            """
            INSERT INTO memories (content, category, source_conversation_id, created_at)
            VALUES (?, ?, ?, ?);
            """,
            (sanitized_content, category.strip() or "general", source_conversation_id, now),
        )
        mem_id = cursor.lastrowid
        self._conn.commit()

        return Memory(
            id=mem_id,
            content=sanitized_content,
            category=category.strip() or "general",
            source_conversation_id=source_conversation_id,
            created_at=now,
        )

    def list_memories(self, limit: int = 100) -> list[Memory]:
        """List stored long-term memories in reverse chronological order."""
        cursor = self._conn.cursor()
        cursor.execute(
            """
            SELECT id, content, category, source_conversation_id, created_at
            FROM memories
            ORDER BY created_at DESC, id DESC
            LIMIT ?;
            """,
            (limit,),
        )
        return [
            Memory(
                id=row["id"],
                content=row["content"],
                category=row["category"],
                source_conversation_id=row["source_conversation_id"],
                created_at=row["created_at"],
            )
            for row in cursor.fetchall()
        ]

    def get_memory(self, memory_id: int) -> Memory | None:
        """Retrieve a single long-term memory by its ID."""
        cursor = self._conn.cursor()
        cursor.execute(
            "SELECT id, content, category, source_conversation_id, created_at FROM memories WHERE id = ?;",
            (memory_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None
        return Memory(
            id=row["id"],
            content=row["content"],
            category=row["category"],
            source_conversation_id=row["source_conversation_id"],
            created_at=row["created_at"],
        )

    def delete_memory(self, memory_id: int) -> bool:
        """Delete an individual long-term memory by ID."""
        cursor = self._conn.cursor()
        cursor.execute("DELETE FROM memories WHERE id = ?;", (memory_id,))
        self._conn.commit()
        return cursor.rowcount > 0

    def clear_all_memories(self) -> int:
        """Purge all long-term memories from storage."""
        cursor = self._conn.cursor()
        cursor.execute("DELETE FROM memories;")
        count = cursor.rowcount
        self._conn.commit()
        return count

    def clear_all_conversations(self) -> int:
        """Purge all conversations and cascaded messages."""
        cursor = self._conn.cursor()
        cursor.execute("DELETE FROM conversations;")
        count = cursor.rowcount
        self._conn.commit()
        return count

    def close(self) -> None:
        """Close the underlying SQLite connection."""
        if self._conn:
            self._conn.close()

    def __enter__(self) -> SQLiteStorage:
        return self

    def __exit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        self.close()
