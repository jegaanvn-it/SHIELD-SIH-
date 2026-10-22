"""M0A request-plan dry run.

API execution is intentionally unavailable in this FILES-only preparation:
official SDK/model research and API M0A authorization are still required.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__:
    from .counted_transport import CountedTransport
    from .request_counter import AttemptCounter, CounterError, MAX_ATTEMPTS
else:
    from counted_transport import CountedTransport
    from request_counter import AttemptCounter, CounterError, MAX_ATTEMPTS


PLAN = (
    ("API-00", 1),
    ("API-LAT", 3),
    ("API-LID", 6),
    ("API-TTS", 6),
    ("API-STT", 6),
    ("API-TLX", 2),
    ("API-LAT-TTS", 1),
)
PLANNED_ATTEMPTS = sum(count for _, count in PLAN)
RESERVE_ATTEMPTS = 5


def dispatch_planned_request(
    client: object,
    transport: CountedTransport,
    group: str,
    **request: object,
) -> object:
    """Dispatch one planned SDK call through the counter-aware transport.

    The streaming iterator keeps its request scope active while the SDK makes
    the request and yields response chunks. The CLI intentionally remains
    dry-run-only; this adapter is exercised only with local mock transports.
    """
    models = getattr(client, "models")
    if group == "API-LAT-TTS":
        def stream_in_scope():
            with transport.request_scope():
                yield from models.generate_content_stream(**request)

        return stream_in_scope()

    with transport.request_scope():
        return models.generate_content(**request)


def counter_path() -> Path:
    workspace = Path(__file__).resolve().parents[2]
    return workspace / "artifacts" / "m0a" / "request_counter.json"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--execute", action="store_true")
    args = parser.parse_args(argv)
    if args.execute:
        print(
            "API execution is not enabled in this FILES-only preparation; "
            "no request was made.",
            file=sys.stderr,
        )
        return 2
    try:
        with AttemptCounter(counter_path()) as counter:
            print("M0A plan (dry run; no network):")
            for group, count in PLAN:
                print(f"{group}: {count}")
            print(f"planned={PLANNED_ATTEMPTS}")
            print(f"used={counter.attempts}")
            print(f"reserve={RESERVE_ATTEMPTS}")
            print(f"hard_cap={MAX_ATTEMPTS}")
            print(f"remaining={MAX_ATTEMPTS - counter.attempts}")
    except CounterError as exc:
        print(f"Counter check failed closed: {exc}", file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
