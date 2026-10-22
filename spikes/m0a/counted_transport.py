"""Fail-closed HTTPX transport for accounting SDK requests in M0A."""

from __future__ import annotations

from contextlib import contextmanager
from threading import Lock
from typing import Iterator

import httpx

from .request_counter import AttemptCounter


class TransportScopeError(RuntimeError):
    """An SDK request occurred outside one planned request scope."""


class UnexpectedSDKDispatch(RuntimeError):
    """The SDK emitted more than one HTTP request for one planned request."""


class CountedTransport(httpx.BaseTransport):
    """Persist each intercepted request before forwarding it to the delegate.

    The caller must hold one ``AttemptCounter`` lock for the complete runner
    invocation. Each planned SDK call must run inside ``request_scope``.
    """

    def __init__(self, counter: AttemptCounter, delegate: httpx.BaseTransport) -> None:
        self._counter = counter
        self._delegate = delegate
        self._scope_active = False
        self._scope_lock = Lock()
        self.intercepted = 0
        self.forwarded = 0
        self.blocked = 0

    @contextmanager
    def request_scope(self) -> Iterator[None]:
        if not self._scope_lock.acquire(blocking=False):
            raise TransportScopeError("Concurrent or nested SDK request scopes are forbidden.")
        self._scope_active = True
        self._scope_intercepted = 0
        try:
            yield
        finally:
            self._scope_active = False
            self._scope_lock.release()

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        if not self._scope_active:
            raise TransportScopeError("SDK dispatch outside a planned request scope was blocked.")

        # Persist before any request can reach the downstream transport.
        self.intercepted += 1
        self._counter.increment_before_attempt()
        self._scope_intercepted += 1
        if self._scope_intercepted > 1:
            self.blocked += 1
            raise UnexpectedSDKDispatch(
                "Additional SDK dispatch counted and blocked before downstream transport."
            )

        self.forwarded += 1
        return self._delegate.handle_request(request)

    def close(self) -> None:
        self._delegate.close()
