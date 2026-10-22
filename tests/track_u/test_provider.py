"""Unit tests for the Track U echo provider."""

from __future__ import annotations

import pytest

from sara.providers.base import BaseProvider
from sara.providers.echo import EchoProvider


def test_echo_provider_is_instance_of_base() -> None:
    provider = EchoProvider()
    assert isinstance(provider, BaseProvider)


def test_echo_provider_standard_prompt() -> None:
    provider = EchoProvider()
    result = provider.generate_response("Hello SARA")
    assert result == "Sara (echo): Hello SARA"


def test_echo_provider_custom_prefix() -> None:
    provider = EchoProvider(prefix="[TEST] ")
    result = provider.generate_response("Test message")
    assert result == "[TEST] Test message"


def test_echo_provider_empty_prompt() -> None:
    provider = EchoProvider()
    result = provider.generate_response("   ")
    assert "empty message" in result
