"""Offline validation of the M0A google-genai Models API mapping.

Every SDK HTTP request is intercepted by httpx.MockTransport. The test-only
guard counts each intercepted dispatch in a temporary AttemptCounter and
blocks any second dispatch for the same planned request before it reaches the
mock's downstream handler.
"""

from __future__ import annotations

import base64
import json
import time
from pathlib import Path
from typing import Any, Callable

import httpx
import pytest
from google import genai
from google.genai import types

from spikes.m0a.request_counter import AttemptCounter, CounterError, MAX_ATTEMPTS


MOCK_API_KEY = "test-only-not-a-real-key"


class ExtraDispatchBlocked(RuntimeError):
    """A second SDK dispatch for one planned request was rejected."""


class CountingMockTransport(httpx.BaseTransport):
    """Count and gate SDK dispatches before the mock endpoint sees them."""

    def __init__(
        self,
        counter: AttemptCounter,
        responder: Callable[[httpx.Request], httpx.Response],
    ) -> None:
        self.counter = counter
        self.intercepted = 0
        self.forwarded = 0
        self.blocked = 0
        self.downstream_requests: list[httpx.Request] = []
        self._mock = httpx.MockTransport(self._respond)
        self._responder = responder

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        self.intercepted += 1
        self.counter.increment_before_attempt()
        if self.intercepted > 1:
            self.blocked += 1
            raise ExtraDispatchBlocked(
                "additional dispatch blocked before mock/network dispatch"
            )
        self.forwarded += 1
        return self._mock.handle_request(request)

    def _respond(self, request: httpx.Request) -> httpx.Response:
        self.downstream_requests.append(request)
        return self._responder(request)

    def close(self) -> None:
        self._mock.close()


def _write_counter(path: Path, attempts: int = 0) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"schema_version": 1, "attempts": attempts}),
        encoding="utf-8",
    )


def _json_response(payload: dict[str, Any], status: int = 200) -> httpx.Response:
    return httpx.Response(status, json=payload)


def _text_payload(text: str = "mock response") -> dict[str, Any]:
    return {
        "candidates": [
            {
                "content": {"role": "model", "parts": [{"text": text}]},
                "finishReason": "STOP",
                "index": 0,
            }
        ]
    }


def _audio_payload(audio: bytes = b"synthetic-wav-audio") -> dict[str, Any]:
    return {
        "candidates": [
            {
                "content": {
                    "role": "model",
                    "parts": [
                        {
                            "inlineData": {
                                "mimeType": "audio/wav",
                                "data": base64.b64encode(audio).decode("ascii"),
                            }
                        }
                    ],
                },
                "finishReason": "STOP",
                "index": 0,
            }
        ]
    }


def _client(transport: CountingMockTransport) -> genai.Client:
    http_options = types.HttpOptions(
        retry_options=types.HttpRetryOptions(attempts=1),
        client_args={"transport": transport},
    )
    return genai.Client(api_key=MOCK_API_KEY, http_options=http_options)


def _run_nonstream(
    counter_path: Path,
    responder: Callable[[httpx.Request], httpx.Response],
    invoke: Callable[[genai.Client], Any],
) -> tuple[Any, int, int, list[httpx.Request]]:
    _write_counter(counter_path)
    with AttemptCounter(counter_path) as counter:
        transport = CountingMockTransport(counter, responder)
        client = _client(transport)
        try:
            result = invoke(client)
        finally:
            client.close()
        return result, counter.attempts, transport.intercepted, transport.downstream_requests


def _no_continuation(**kwargs: Any) -> types.GenerateContentConfig:
    return types.GenerateContentConfig(
        automatic_continuation=False,
        **kwargs,
    )


def test_generate_content_serializes_text_and_extracts_text(tmp_path: Path) -> None:
    request_body: dict[str, Any] = {}

    def responder(request: httpx.Request) -> httpx.Response:
        request_body.update(json.loads(request.content))
        assert request.url.path.endswith("/models/gemini-3.8-flash:generateContent")
        return _json_response(_text_payload("synthetic text reply"))

    response, attempts, intercepted, downstream = _run_nonstream(
        tmp_path / "counter.json",
        responder,
        lambda client: client.models.generate_content(
            model="gemini-3.8-flash",
            contents="synthetic question",
            config=_no_continuation(),
        ),
    )

    assert request_body["contents"][0]["parts"][0]["text"] == "synthetic question"
    assert response.text == "synthetic text reply"
    assert (attempts, intercepted, len(downstream)) == (1, 1, 1)


def test_generate_content_serializes_tts_and_extracts_audio(tmp_path: Path) -> None:
    request_body: dict[str, Any] = {}
    audio = b"RIFF-synthetic-audio"

    def responder(request: httpx.Request) -> httpx.Response:
        request_body.update(json.loads(request.content))
        assert request.url.path.endswith(
            "/models/gemini-3.8-flash-tts:generateContent"
        )
        return _json_response(_audio_payload(audio))

    response, attempts, intercepted, downstream = _run_nonstream(
        tmp_path / "counter.json",
        responder,
        lambda client: client.models.generate_content(
            model="gemini-3.8-flash-tts",
            contents="synthetic phrase for speech",
            config=_no_continuation(
                response_modalities=["AUDIO"],
                speech_config={
                    "voice_config": {
                        "prebuilt_voice_config": {"voice_name": "Kore"}
                    }
                },
            ),
        ),
    )

    generation = request_body["generationConfig"]
    assert generation["responseModalities"] == ["AUDIO"]
    assert generation["speechConfig"]["voice_config"][
        "prebuilt_voice_config"
    ]["voice_name"] == "Kore"
    assert response.candidates[0].content.parts[0].inline_data.data == audio
    assert (attempts, intercepted, len(downstream)) == (1, 1, 1)


def test_generate_content_serializes_stt_audio_and_extracts_transcript(
    tmp_path: Path,
) -> None:
    request_body: dict[str, Any] = {}
    audio = b"synthetic-talking-audio"

    def responder(request: httpx.Request) -> httpx.Response:
        request_body.update(json.loads(request.content))
        assert request.url.path.endswith(
            "/models/gemini-3.5-transcribe:generateContent"
        )
        return _json_response(_text_payload("synthetic transcript"))

    response, attempts, intercepted, downstream = _run_nonstream(
        tmp_path / "counter.json",
        responder,
        lambda client: client.models.generate_content(
            model="gemini-3.5-transcribe",
            contents=[
                "Transcribe this synthetic audio.",
                types.Part.from_bytes(data=audio, mime_type="audio/wav"),
            ],
            config=_no_continuation(),
        ),
    )

    encoded_audio = request_body["contents"][0]["parts"][1]["inlineData"]
    assert encoded_audio["mime_type"] == "audio/wav"
    assert base64.b64decode(encoded_audio["data"]) == audio
    assert response.text == "synthetic transcript"
    assert (attempts, intercepted, len(downstream)) == (1, 1, 1)


def _sse_response(payloads: list[dict[str, Any]]) -> httpx.Response:
    lines = [f"data: {json.dumps(payload)}\n\n" for payload in payloads]
    return httpx.Response(
        200,
        headers={"content-type": "text/event-stream"},
        stream=httpx.ByteStream("".join(lines).encode("utf-8")),
    )


def test_generate_content_stream_extracts_audio_and_measures_mock_ttfa(
    tmp_path: Path,
) -> None:
    audio_one = b"first-audio-chunk"
    audio_two = b"second-audio-chunk"

    def responder(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        assert request.url.path.endswith(
            "/models/gemini-3.8-flash-tts:streamGenerateContent"
        )
        assert body["generationConfig"]["responseModalities"] == ["AUDIO"]
        return _sse_response([_audio_payload(audio_one), _audio_payload(audio_two)])

    _write_counter(tmp_path / "counter.json")
    counter_path = tmp_path / "counter.json"
    with AttemptCounter(counter_path) as counter:
        transport = CountingMockTransport(counter, responder)
        client = _client(transport)
        started = time.monotonic()
        try:
            chunks = client.models.generate_content_stream(
                model="gemini-3.8-flash-tts",
                contents="synthetic sentence for streaming TTS",
                config=_no_continuation(response_modalities=["AUDIO"]),
            )
            first_audio_at: float | None = None
            extracted: list[bytes] = []
            for chunk in chunks:
                for part in chunk.parts:
                    if part.inline_data is not None:
                        if first_audio_at is None:
                            first_audio_at = time.monotonic()
                        extracted.append(part.inline_data.data)
        finally:
            client.close()

        assert first_audio_at is not None
        mock_ttfa_seconds = first_audio_at - started
        assert mock_ttfa_seconds >= 0
        assert extracted == [audio_one, audio_two]
        assert (counter.attempts, transport.intercepted, len(transport.downstream_requests)) == (
            1,
            1,
            1,
        )


def _continuation_payload() -> dict[str, Any]:
    return {
        "candidates": [
            {
                "content": {"role": "model", "parts": [{"text": "partial"}]},
                "finishReason": "CONTINUATION",
                "continuationToken": base64.b64encode(b"synthetic-token").decode(
                    "ascii"
                ),
                "index": 0,
            }
        ]
    }


@pytest.mark.parametrize("streaming", [False, True])
def test_automatic_continuation_disabled_emits_no_followup_request(
    tmp_path: Path,
    streaming: bool,
) -> None:
    def responder(_request: httpx.Request) -> httpx.Response:
        if streaming:
            return _sse_response([_continuation_payload()])
        return _json_response(_continuation_payload())

    _write_counter(tmp_path / "counter.json")
    counter_path = tmp_path / "counter.json"
    with AttemptCounter(counter_path) as counter:
        transport = CountingMockTransport(counter, responder)
        client = _client(transport)
        try:
            if streaming:
                list(
                    client.models.generate_content_stream(
                        model="gemini-3.8-flash-tts",
                        contents="synthetic continuation test",
                        config=_no_continuation(response_modalities=["AUDIO"]),
                    )
                )
            else:
                client.models.generate_content(
                    model="gemini-3.8-flash",
                    contents="synthetic continuation test",
                    config=_no_continuation(),
                )
        finally:
            client.close()
        assert (counter.attempts, transport.intercepted, len(transport.downstream_requests)) == (
            1,
            1,
            1,
        )


@pytest.mark.parametrize("streaming", [False, True])
@pytest.mark.parametrize(
    "failure_kind",
    ["http_429", "http_503", "timeout", "connection"],
)
def test_models_methods_fail_once_for_retry_eligible_conditions(
    tmp_path: Path,
    streaming: bool,
    failure_kind: str,
) -> None:
    def responder(request: httpx.Request) -> httpx.Response:
        if failure_kind in {"http_429", "http_503"}:
            status = 429 if failure_kind == "http_429" else 503
            return httpx.Response(
                status,
                json={"error": {"code": status, "message": "synthetic failure"}},
            )
        if failure_kind == "timeout":
            raise httpx.ReadTimeout("synthetic timeout", request=request)
        raise httpx.ConnectError("synthetic connection failure", request=request)

    _write_counter(tmp_path / "counter.json")
    counter_path = tmp_path / "counter.json"
    with AttemptCounter(counter_path) as counter:
        transport = CountingMockTransport(counter, responder)
        client = _client(transport)
        try:
            with pytest.raises(Exception):
                if streaming:
                    list(
                        client.models.generate_content_stream(
                            model="gemini-3.8-flash-tts",
                            contents="synthetic failure test",
                            config=_no_continuation(response_modalities=["AUDIO"]),
                        )
                    )
                else:
                    client.models.generate_content(
                        model="gemini-3.8-flash",
                        contents="synthetic failure test",
                        config=_no_continuation(),
                    )
        finally:
            client.close()
        assert (counter.attempts, transport.intercepted) == (1, 1)
        assert transport.blocked == 0


def test_additional_intercepted_dispatch_is_counted_then_blocked(
    tmp_path: Path,
) -> None:
    _write_counter(tmp_path / "counter.json")
    counter_path = tmp_path / "counter.json"
    with AttemptCounter(counter_path) as counter:
        transport = CountingMockTransport(
            counter,
            lambda _request: _json_response(_text_payload()),
        )
        request = httpx.Request("POST", "https://mock.invalid/generateContent")
        first = transport.handle_request(request)
        assert first.status_code == 200
        with pytest.raises(ExtraDispatchBlocked):
            transport.handle_request(request)
        assert (counter.attempts, transport.intercepted) == (2, 2)
        assert (transport.forwarded, transport.blocked) == (1, 1)
        assert len(transport.downstream_requests) == 1


def test_counter_cap_blocks_transport_before_dispatch(tmp_path: Path) -> None:
    counter_path = tmp_path / "counter.json"
    _write_counter(counter_path, MAX_ATTEMPTS)
    with AttemptCounter(counter_path) as counter:
        transport = CountingMockTransport(
            counter,
            lambda _request: _json_response(_text_payload()),
        )
        client = _client(transport)
        try:
            with pytest.raises(CounterError):
                client.models.generate_content(
                    model="gemini-3.8-flash",
                    contents="synthetic cap test",
                    config=_no_continuation(),
                )
        finally:
            client.close()
        assert (counter.attempts, transport.intercepted, transport.forwarded) == (
            MAX_ATTEMPTS,
            1,
            0,
        )
        assert transport.downstream_requests == []
