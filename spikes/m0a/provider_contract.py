"""Offline provider contract used by M0A mock tests.

Concrete Gemini SDK exception mapping is deferred until the official SDK is
verified under EXTERNAL M0A. This module performs one injected call only and
never retries or creates a network client.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any


class InvalidKeyError(Exception):
    pass


class QuotaExhaustedError(Exception):
    pass


class ProviderTimeoutError(Exception):
    pass


class ProviderNetworkError(Exception):
    pass


class UnsupportedModelError(Exception):
    pass


class ProviderFailure(RuntimeError):
    def __init__(self, kind: str) -> None:
        super().__init__(kind)
        self.kind = kind


_MAPPED_ERRORS = (
    (InvalidKeyError, "invalid_key"),
    (QuotaExhaustedError, "quota_exhausted"),
    (ProviderTimeoutError, "timeout"),
    (ProviderNetworkError, "network_failure"),
    (UnsupportedModelError, "unsupported_model"),
)


def call_once(
    transport: Callable[[Any], Any],
    request: Any,
) -> Any:
    """Call an injected mock transport once and normalize its test failures."""
    try:
        response = transport(request)
    except Exception as exc:
        for error_type, kind in _MAPPED_ERRORS:
            if isinstance(exc, error_type):
                raise ProviderFailure(kind) from exc
        raise
    if response is None or response == "" or response == [] or response == {}:
        raise ProviderFailure("empty_response")
    return response
