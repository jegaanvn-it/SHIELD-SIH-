"""Local SDK integration tests for the production counter-aware transport."""

from __future__ import annotations

import base64
import json
from pathlib import Path
from typing import Any

import httpx
import pytest
from google import genai
from google.genai import types

from spikes.m0a.counted_transport import CountedTransport, UnexpectedSDKDispatch
from spikes.m0a.request_counter import AttemptCounter, CounterError, MAX_ATTEMPTS
from spikes.m0a.run_api_budgeted import dispatch_planned_request


MOCK_API_KEY = "test-only-not-a-real-key"


def _write_counter(path: Path, attempts: int = 0) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"schema_version": 1, "attempts": attempts}), encoding="utf-8"
    )


def _generation_config(**kwargs: Any) -> types.GenerateContentConfig:
    return types.GenerateContentConfig(automatic_continuation=False, **kwargs)


def _json_response(payload: dict[str, Any], status: int = 200) -> httpx.Response:
    return httpx.Response(status, json=payload)


def _text_payload() -> dict[str, Any]:
    return {
        "candidates": [{
            "content": {"role": "model", "parts": [{"text": "mock reply"}]},
            "finishReason": "STOP",
            "index": 0,
        }]
    }


def _audio_payload(audio: bytes) -> dict[str, Any]:
    return {
        "candidates": [{
            "content": {"role": "model", "parts": [{
                "inlineData": {
                    "mimeType": "audio/wav",
                    "data": base64.b64encode(audio).decode("ascii"),
                }
            }]},
            "finishReason": "STOP",
            "index": 0,
        }]
    }


def _sse(payload: dict[str, Any]) -> httpx.Response:
    body = f"data: {json.dumps(payload)}\n\n".encode("utf-8")
    return httpx.Response(
        200,
        headers={"content-type": "text/event-stream"},
        stream=httpx.ByteStream(body),
    )


def _client(transport: CountedTransport) -> genai.Client:
    return genai.Client(
        api_key=MOCK_API_KEY,
        http_options=types.HttpOptions(
            retry_options=types.HttpRetryOptions(attempts=1),
            client_args={"transport": transport},
        ),
    )


def test_runner_nonstream_dispatch_counts_before_mock_forward(tmp_path: Path) -> None:
    counter_path = tmp_path / "counter.json"
    _write_counter(counter_path)
    downstream: list[httpx.Request] = []

    def respond(request: httpx.Request) -> httpx.Response:
        downstream.append(request)
        assert request.url.path.endswith("/models/mock-text:generateContent")
        return _json_response(_text_payload())

    with AttemptCounter(counter_path) as counter:
        counted = CountedTransport(counter, httpx.MockTransport(respond))
        client = _client(counted)
        try:
            result = dispatch_planned_request(
                client,
                counted,
                "API-LAT",
                model="mock-text",
                contents="synthetic prompt",
                config=_generation_config(),
            )
        finally:
            client.close()

        assert result.text == "mock reply"
        assert (counter.attempts, counted.intercepted, counted.forwarded) == (1, 1, 1)
        assert len(downstream) == 1


def test_runner_stream_dispatch_counts_and_yields_audio(tmp_path: Path) -> None:
    counter_path = tmp_path / "counter.json"
    _write_counter(counter_path)
    audio = b"synthetic-stream-audio"
    downstream: list[httpx.Request] = []

    def respond(request: httpx.Request) -> httpx.Response:
        downstream.append(request)
        assert request.url.path.endswith("/models/mock-tts:streamGenerateContent")
        return _sse(_audio_payload(audio))

    with AttemptCounter(counter_path) as counter:
        counted = CountedTransport(counter, httpx.MockTransport(respond))
        client = _client(counted)
        try:
            chunks = list(dispatch_planned_request(
                client,
                counted,
                "API-LAT-TTS",
                model="mock-tts",
                contents="synthetic sentence",
                config=_generation_config(response_modalities=["AUDIO"]),
            ))
        finally:
            client.close()

        extracted = [
            part.inline_data.data
            for chunk in chunks
            for part in chunk.parts
            if part.inline_data is not None
        ]
        assert extracted == [audio]
        assert (counter.attempts, counted.intercepted, counted.forwarded) == (1, 1, 1)
        assert len(downstream) == 1


@pytest.mark.parametrize("status", [429, 503])
def test_runner_retry_eligible_status_is_one_intercepted_attempt(
    tmp_path: Path, status: int
) -> None:
    counter_path = tmp_path / "counter.json"
    _write_counter(counter_path)
    downstream: list[httpx.Request] = []

    def respond(request: httpx.Request) -> httpx.Response:
        downstream.append(request)
        return httpx.Response(status, json={"error": {"code": status}})

    with AttemptCounter(counter_path) as counter:
        counted = CountedTransport(counter, httpx.MockTransport(respond))
        client = _client(counted)
        try:
            with pytest.raises(Exception):
                dispatch_planned_request(
                    client,
                    counted,
                    "API-LAT",
                    model="mock-text",
                    contents="synthetic retry probe",
                    config=_generation_config(),
                )
        finally:
            client.close()
        assert (counter.attempts, counted.intercepted, counted.forwarded) == (1, 1, 1)
        assert len(downstream) == 1


def test_runner_blocks_and_counts_sdk_followup_before_second_forward(
    tmp_path: Path,
) -> None:
    counter_path = tmp_path / "counter.json"
    _write_counter(counter_path)
    downstream: list[httpx.Request] = []
    request = httpx.Request("POST", "https://mock.invalid/generateContent")

    with AttemptCounter(counter_path) as counter:
        counted = CountedTransport(
            counter,
            httpx.MockTransport(
                lambda req: (downstream.append(req) or httpx.Response(200))
            ),
        )
        with counted.request_scope():
            assert counted.handle_request(request).status_code == 200
            with pytest.raises(UnexpectedSDKDispatch):
                counted.handle_request(request)
        assert (counter.attempts, counted.intercepted, counted.forwarded, counted.blocked) == (
            2, 2, 1, 1
        )
        assert len(downstream) == 1


def test_runner_counter_cap_blocks_before_mock_forward(tmp_path: Path) -> None:
    counter_path = tmp_path / "counter.json"
    _write_counter(counter_path, MAX_ATTEMPTS)
    downstream: list[httpx.Request] = []

    with AttemptCounter(counter_path) as counter:
        counted = CountedTransport(
            counter,
            httpx.MockTransport(
                lambda req: (downstream.append(req) or httpx.Response(200))
            ),
        )
        client = _client(counted)
        try:
            with pytest.raises(CounterError):
                dispatch_planned_request(
                    client,
                    counted,
                    "API-LAT",
                    model="mock-text",
                    contents="synthetic cap probe",
                    config=_generation_config(),
                )
        finally:
            client.close()
        assert (counter.attempts, counted.intercepted, counted.forwarded) == (
            MAX_ATTEMPTS, 1, 0
        )
        assert downstream == []
