"""Offline verification tests for WP-V03: Gemini default provider, Tanglish directives, and privacy boundaries."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock
import pytest

from sara.config import (
    DEFAULT_GEMINI_MODEL,
    DEFAULT_LONG_TERM_MEMORY,
    DEFAULT_PERSIST_HISTORY,
    DEFAULT_PROVIDER,
    MAX_CONTEXT_MESSAGES,
    SARA_SYSTEM_INSTRUCTION,
)
from sara.memory.storage import SQLiteStorage
from sara.providers.echo import EchoProvider
from sara.providers.gemini import (
    GeminiAPIKeyMissingError,
    GeminiProvider,
)
from sara.ui.app import create_default_provider


def test_v03_default_provider_is_gemini() -> None:
    """Default provider must be GeminiProvider, never EchoProvider."""
    assert DEFAULT_PROVIDER == "gemini"
    provider = create_default_provider()
    assert isinstance(provider, GeminiProvider)
    assert not isinstance(provider, EchoProvider)
    assert provider.model == DEFAULT_GEMINI_MODEL


def test_v03_missing_api_key_raises_actionable_error_no_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    """When GEMINI_API_KEY is missing, provider must raise an actionable error without silent Echo fallback."""
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    provider = GeminiProvider(api_key=None)
    assert not provider.has_api_key

    with pytest.raises(GeminiAPIKeyMissingError) as exc_info:
        provider.generate_response("Testing missing key")

    err_text = str(exc_info.value)
    # Actionable guidance must be present
    assert "$env:GEMINI_API_KEY" in err_text
    assert "--provider echo" in err_text


def test_v03_echo_provider_available_when_explicit() -> None:
    """EchoProvider must remain functional and available when explicitly selected."""
    echo = EchoProvider()
    response = echo.generate_response("Offline verification prompt")
    assert "Sara (echo): Offline verification prompt" in response


def test_v03_tanglish_system_instruction_directives() -> None:
    """System prompt must mandate Tanglish Latin-script responses and forbid Tamil Unicode script."""
    instruction = SARA_SYSTEM_INSTRUCTION

    # Must specify Tanglish
    assert "Tanglish" in instruction

    # Must require Latin / English alphabet
    assert "Latin" in instruction or "English" in instruction

    # Must explicitly forbid Tamil script characters
    assert "STRICTLY DO NOT use Tamil script" in instruction or "DO NOT use Tamil script" in instruction


def test_v03_conversation_isolation_and_context_bounds() -> None:
    """GeminiProvider must strictly bound conversation turns to MAX_CONTEXT_MESSAGES."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "Mocked answer"
    mock_client.models.generate_content.return_value = mock_response

    provider = GeminiProvider(
        api_key="mock_test_key",
        model="gemini-2.5-flash",
        client=mock_client,
    )

    # Build 30 history turns
    large_history = [
        {"role": "user" if i % 2 == 0 else "assistant", "content": f"Turn {i}"}
        for i in range(30)
    ]

    provider.generate_response("Latest turn", history=large_history)

    call_args = mock_client.models.generate_content.call_args
    contents = call_args.kwargs["contents"]

    # History turns included must not exceed MAX_CONTEXT_MESSAGES
    assert len(contents) <= MAX_CONTEXT_MESSAGES + 1


def test_v03_privacy_defaults_preserved() -> None:
    """Storage must retain session-only ephemeral RAM mode and long-term memory OFF by default."""
    assert DEFAULT_PERSIST_HISTORY is False
    assert DEFAULT_LONG_TERM_MEMORY is False

    storage = SQLiteStorage()
    try:
        assert storage.ephemeral is True
        assert storage.is_history_persisted() is False
        assert storage.is_memory_enabled() is False

        # Adding a memory while disabled must fail closed
        with pytest.raises(PermissionError):
            storage.add_memory("Should fail because memory is disabled")
    finally:
        storage.close()


def test_v03_gitignore_protects_credentials() -> None:
    """Gitignore must explicitly include SARA API.txt and credential patterns."""
    gitignore_path = Path(".gitignore")
    assert gitignore_path.exists()
    content = gitignore_path.read_text(encoding="utf-8")
    assert "SARA API.txt" in content
    assert "*API*.txt" in content
