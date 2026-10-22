"""Fail-closed persistent counter for the M0A Gemini attempt budget."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


MAX_ATTEMPTS = 30


class CounterError(RuntimeError):
    """The persistent attempt counter cannot be trusted or locked."""


class AttemptCounter:
    """Hold an interprocess lock while reading/updating the counter.

    This module deliberately never creates or resets the counter. FILES M0A
    initializes the one persistent file; every later process must fail closed
    if that file is absent, unreadable, malformed, or already locked.
    """

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._handle: Any = None
        self._locked = False
        self._attempts: int | None = None

    def __enter__(self) -> "AttemptCounter":
        if os.name != "nt":
            raise CounterError("M0A API runner requires native Windows locking.")
        if not self.path.is_file():
            raise CounterError("Persistent counter is missing; refusing to initialize it.")
        try:
            self._handle = self.path.open("r+b", buffering=0)
            import msvcrt

            self._handle.seek(0)
            msvcrt.locking(self._handle.fileno(), msvcrt.LK_NBLCK, 1)
            self._locked = True
            self._attempts = self._read_attempts()
            return self
        except Exception as exc:
            self._release()
            if isinstance(exc, CounterError):
                raise
            raise CounterError("Counter could not be opened, read, or locked.") from exc

    def _read_attempts(self) -> int:
        assert self._handle is not None
        try:
            self._handle.seek(0)
            raw = self._handle.read()
            state = json.loads(raw.decode("utf-8"))
        except Exception as exc:
            raise CounterError("Counter is unreadable or malformed.") from exc
        if not isinstance(state, dict) or state.get("schema_version") != 1:
            raise CounterError("Counter schema is invalid.")
        attempts = state.get("attempts")
        if type(attempts) is not int or not 0 <= attempts <= MAX_ATTEMPTS:
            raise CounterError("Counter attempt value is invalid.")
        return attempts

    @property
    def attempts(self) -> int:
        if self._attempts is None:
            raise CounterError("Counter is not open and locked.")
        return self._attempts

    def increment_before_attempt(self) -> int:
        """Persist the next attempt before a caller can issue a request."""
        if self._handle is None or not self._locked or self._attempts is None:
            raise CounterError("Counter is not open and locked.")
        if self._attempts >= MAX_ATTEMPTS:
            raise CounterError("The 30-attempt hard cap is exhausted.")
        next_attempt = self._attempts + 1
        payload = (
            json.dumps(
                {"schema_version": 1, "attempts": next_attempt},
                sort_keys=True,
                separators=(",", ":"),
            )
            + "\n"
        ).encode("utf-8")
        try:
            self._handle.seek(0)
            self._handle.write(payload)
            self._handle.truncate()
            self._handle.flush()
            os.fsync(self._handle.fileno())
        except Exception as exc:
            raise CounterError("Counter update failed; do not issue a request.") from exc
        self._attempts = next_attempt
        return next_attempt

    def _release(self) -> None:
        if self._handle is None:
            return
        if self._locked:
            try:
                import msvcrt

                self._handle.seek(0)
                msvcrt.locking(self._handle.fileno(), msvcrt.LK_UNLCK, 1)
            except Exception:
                # Closing the handle releases the OS lock. The next open still
                # validates the persistent counter and fails closed if needed.
                pass
        try:
            self._handle.close()
        finally:
            self._handle = None
            self._locked = False

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
        self._release()
