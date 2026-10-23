"""Google Gemini AI provider implementation for Project SARA."""

from __future__ import annotations

import logging
import os
from typing import Any

from google import genai
from google.genai import types
from google.genai.errors import APIError

from sara.config import (
    DEFAULT_GEMINI_MODEL,
    MAX_CONTEXT_MESSAGES,
    MAX_MESSAGE_CHARS,
    SARA_SYSTEM_INSTRUCTION,
    get_gemini_api_key,
    get_gemini_model,
)
from sara.providers.base import BaseProvider

logger = logging.getLogger(__name__)


class GeminiProviderError(Exception):
    """Base exception for Gemini provider failures."""


class GeminiAPIKeyMissingError(GeminiProviderError):
    """Raised when GEMINI_API_KEY is missing or empty."""


class GeminiModelNotFoundError(GeminiProviderError):
    """Raised when the requested model ID is retired or invalid."""


class GeminiQuotaExceededError(GeminiProviderError):
    """Raised when the API rate limit or project quota is exhausted."""


class GeminiAuthenticationError(GeminiProviderError):
    """Raised when the provided API key is rejected by Google."""


class GeminiProvider(BaseProvider):
    """Production provider integrating the official Google Gen AI SDK."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        system_instruction: str | None = None,
        client: Any = None,
    ) -> None:
        self._api_key = api_key if api_key is not None else get_gemini_api_key()
        self.model = model if model is not None else get_gemini_model()
        self.system_instruction = (
            system_instruction
            if system_instruction is not None
            else SARA_SYSTEM_INSTRUCTION
        )
        self._client = client

    @property
    def has_api_key(self) -> bool:
        """Check presence of an API key without disclosing value."""
        return bool(self._api_key and self._api_key.strip())

    def _get_client(self) -> Any:
        """Obtain or initialize the official Google GenAI client."""
        if self._client is not None:
            return self._client
        if not self.has_api_key:
            raise GeminiAPIKeyMissingError(
                "GEMINI_API_KEY environment variable is not configured. "
                "To chat with Gemini, set your API key in PowerShell: $env:GEMINI_API_KEY = 'your_key'. "
                "Or launch SARA in offline testing mode using: python -m sara.ui.app --provider echo"
            )
        self._client = genai.Client(api_key=self._api_key)
        return self._client

    def _build_contents(
        self,
        prompt: str,
        history: list[dict[str, str]] | None,
    ) -> list[types.Content]:
        """Sanitize and format bounded conversation history into SDK types.Content."""
        raw_items: list[tuple[str, str]] = []

        if history:
            # Slice only the most recent N messages
            bounded_history = history[-MAX_CONTEXT_MESSAGES:]
            for msg in bounded_history:
                role = msg.get("role", "").strip().lower()
                content = msg.get("content", "").strip()
                if not content:
                    continue

                # Map SARA memory roles to Gemini SDK roles
                mapped_role = "user" if role == "user" else "model"

                # Truncate overly long messages for context safety
                if len(content) > MAX_MESSAGE_CHARS:
                    content = (
                        content[:MAX_MESSAGE_CHARS]
                        + "\n[...content truncated for context budget]"
                    )

                raw_items.append((mapped_role, content))

        # Append the new prompt as the final user turn
        cleaned_prompt = prompt.strip()
        if len(cleaned_prompt) > MAX_MESSAGE_CHARS:
            cleaned_prompt = (
                cleaned_prompt[:MAX_MESSAGE_CHARS]
                + "\n[...content truncated for context budget]"
            )
        raw_items.append(("user", cleaned_prompt))

        # Enforce strict alternation: merge consecutive turns from the same role
        sanitized_turns: list[tuple[str, str]] = []
        for role, text in raw_items:
            if sanitized_turns and sanitized_turns[-1][0] == role:
                prev_role, prev_text = sanitized_turns[-1]
                sanitized_turns[-1] = (prev_role, f"{prev_text}\n\n{text}")
            else:
                sanitized_turns.append((role, text))

        # Convert to SDK types.Content objects
        contents: list[types.Content] = []
        for role, text in sanitized_turns:
            contents.append(
                types.Content(
                    role=role,
                    parts=[types.Part.from_text(text=text)],
                )
            )

        return contents

    def generate_response(
        self,
        prompt: str,
        history: list[dict[str, str]] | None = None,
        **kwargs: Any,
    ) -> str:
        """Send prompt and bounded history to Gemini API and return text response."""
        cleaned_prompt = prompt.strip()
        if not cleaned_prompt:
            return "Please provide a non-empty message for SARA."

        client = self._get_client()
        contents = self._build_contents(cleaned_prompt, history)
        config = types.GenerateContentConfig(
            system_instruction=self.system_instruction,
            temperature=0.7,
        )

        try:
            response = client.models.generate_content(
                model=self.model,
                contents=contents,
                config=config,
            )
            text = response.text if response and response.text else ""
            if not text:
                return "SARA received an empty response from Gemini."
            return text.strip()

        except APIError as exc:
            status_code = getattr(exc, "code", None)
            error_message = str(exc)

            if status_code in (401, 403) or "API_KEY_INVALID" in error_message:
                raise GeminiAuthenticationError(
                    "Authentication failed. Please verify your GEMINI_API_KEY is valid."
                ) from exc
            elif status_code == 404 or "NOT_FOUND" in error_message:
                raise GeminiModelNotFoundError(
                    f"The requested Gemini model ('{self.model}') was not found or is no longer available. "
                    "Please verify the GEMINI_MODEL environment variable or leave it unset to use the default."
                ) from exc
            elif status_code == 429 or "RESOURCE_EXHAUSTED" in error_message:
                raise GeminiQuotaExceededError(
                    "Gemini rate limit or quota exceeded. Please wait a moment before trying again."
                ) from exc
            elif status_code in (500, 503) or "UNAVAILABLE" in error_message:
                raise GeminiProviderError(
                    "The Gemini service is temporarily unavailable. Please try again shortly."
                ) from exc
            else:
                raise GeminiProviderError(
                    f"Gemini API returned an error (code {status_code}). Please try again."
                ) from exc

        except TimeoutError as exc:
            raise GeminiProviderError(
                "Connection to Gemini timed out. Please check your internet connection."
            ) from exc

        except GeminiProviderError:
            raise

        except Exception as exc:
            exc_name = type(exc).__name__
            if "Timeout" in exc_name:
                raise GeminiProviderError(
                    "Connection to Gemini timed out. Please check your internet connection."
                ) from exc
            raise GeminiProviderError(
                "An unexpected network or service error occurred while communicating with Gemini."
            ) from exc
