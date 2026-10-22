"""SQLite conversation storage implementation for Project SARA."""

from __future__ import annotations

import os
from pathlib import Path
import sqlite3
import uuid

from sara.memory.models import Conversation, Message, utc_now_iso


class SQLiteStorage:
    """Thread-safe SQLite storage for conversations and message history with schema versioning."""

    SCHEMA_VERSION = 1

    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path).resolve()
        # Ensure parent directory exists
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
            cursor.execute(f"PRAGMA user_version = {self.SCHEMA_VERSION};")
            self._conn.commit()

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
        """Add a message to a conversation and update conversation updated_at."""
        now = utc_now_iso()
        cursor = self._conn.cursor()

        # Ensure conversation exists
        cursor.execute(
            "SELECT id FROM conversations WHERE id = ?;",
            (conversation_id,),
        )
        if not cursor.fetchone():
            raise ValueError(f"Conversation with id '{conversation_id}' does not exist.")

        cursor.execute(
            """
            INSERT INTO messages (conversation_id, role, content, created_at)
            VALUES (?, ?, ?, ?);
            """,
            (conversation_id, role.strip().lower(), content, now),
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
            content=content,
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

    def close(self) -> None:
        """Close the underlying SQLite connection."""
        if self._conn:
            self._conn.close()

    def __enter__(self) -> SQLiteStorage:
        return self

    def __exit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        self.close()
