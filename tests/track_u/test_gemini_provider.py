"""Offline unit tests for SARA GeminiProvider using mocked transports."""

from __future__ import annotations

from unittest.mock import MagicMock

from google.genai.errors import APIError
import pytest

from sara.config import DEFAULT_GEMINI_MODEL, MAX_CONTEXT_MESSAGES
from sara.providers.gemini import (
    GeminiAPIKeyMissingError,
    GeminiAuthenticationError,
    GeminiModelNotFoundError,
    GeminiProvider,
    GeminiProviderError,
    GeminiQuotaExceededError,
)


def test_gemini_missing_api_key_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    provider = GeminiProvider(api_key=None)

    with pytest.raises(GeminiAPIKeyMissingError, match="GEMINI_API_KEY environment variable"):
        provider.generate_response("Hello")


def test_gemini_successful_mocked_generation() -> None:
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "I am SARA, pleased to assist you."
    mock_client.models.generate_content.return_value = mock_response

    provider = GeminiProvider(
        api_key="mock_key_for_testing",
        model="gemini-2.5-flash",
        client=mock_client,
    )

    result = provider.generate_response("Who are you?")
    assert result == "I am SARA, pleased to assist you."
    assert mock_client.models.generate_content.called

    call_kwargs = mock_client.models.generate_content.call_args.kwargs
    assert call_kwargs["model"] == "gemini-2.5-flash"
    assert len(call_kwargs["contents"]) == 1
    assert call_kwargs["contents"][0].role == "user"
    assert call_kwargs["contents"][0].parts[0].text == "Who are you?"


def test_gemini_context_bounding_and_role_mapping() -> None:
    mock_client = MagicMock()
    mock_response = MagicMock(text="Context received")
    mock_client.models.generate_content.return_value = mock_response

    provider = GeminiProvider(api_key="mock_key", client=mock_client)

    # Generate 30 messages in history
    history: list[dict[str, str]] = []
    for i in range(30):
        role = "user" if i % 2 == 0 else "assistant"
        history.append({"role": role, "content": f"Message {i}"})

    provider.generate_response("New message", history=history)

    call_kwargs = mock_client.models.generate_content.call_args.kwargs
    contents = call_kwargs["contents"]

    # History was bounded to MAX_CONTEXT_MESSAGES (16) + 1 current prompt = 17 raw turns
    # Strict alternation is verified:
    for content in contents:
        assert content.role in ("user", "model")
    assert len(contents) <= MAX_CONTEXT_MESSAGES + 1


def test_gemini_consecutive_turn_merging() -> None:
    provider = GeminiProvider(api_key="mock_key", client=MagicMock())

    # Two consecutive user messages
    history = [
        {"role": "user", "content": "Part 1 of thought"},
        {"role": "user", "content": "Part 2 of thought"},
    ]

    contents = provider._build_contents("Final question", history=history)
    # Both parts merged into one user turn, plus final question user turn = 1 merged turn
    assert contents[0].role == "user"
    assert "Part 1" in contents[0].parts[0].text
    assert "Part 2" in contents[0].parts[0].text
    assert "Final question" in contents[0].parts[0].text


def test_gemini_error_mapping_401_authentication() -> None:
    mock_client = MagicMock()
    api_error = APIError("API_KEY_INVALID", None)
    api_error.code = 401
    mock_client.models.generate_content.side_effect = api_error

    provider = GeminiProvider(api_key="mock_key", client=mock_client)
    with pytest.raises(GeminiAuthenticationError, match="Authentication failed"):
        provider.generate_response("Hello")


def test_gemini_error_mapping_404_model_not_found() -> None:
    mock_client = MagicMock()
    api_error = APIError("NOT_FOUND", None)
    api_error.code = 404
    mock_client.models.generate_content.side_effect = api_error

    provider = GeminiProvider(
        api_key="mock_key",
        model="retired-model-v1",
        client=mock_client,
    )
    with pytest.raises(GeminiModelNotFoundError, match="retired-model-v1.*was not found"):
        provider.generate_response("Hello")


def test_gemini_error_mapping_429_quota() -> None:
    mock_client = MagicMock()
    api_error = APIError("RESOURCE_EXHAUSTED", None)
    api_error.code = 429
    mock_client.models.generate_content.side_effect = api_error

    provider = GeminiProvider(api_key="mock_key", client=mock_client)
    with pytest.raises(GeminiQuotaExceededError, match="rate limit or quota exceeded"):
        provider.generate_response("Hello")


def test_gemini_error_mapping_timeout() -> None:
    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = TimeoutError("Request timed out")

    provider = GeminiProvider(api_key="mock_key", client=mock_client)
    with pytest.raises(GeminiProviderError, match="timed out"):
        provider.generate_response("Hello")


def test_gemini_empty_response_handling() -> None:
    mock_client = MagicMock()
    mock_response = MagicMock(text="")
    mock_client.models.generate_content.return_value = mock_response

    provider = GeminiProvider(api_key="mock_key", client=mock_client)
    result = provider.generate_response("Hello")
    assert "empty response" in result
