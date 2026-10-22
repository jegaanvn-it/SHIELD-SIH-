import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

from spikes.m0a.request_counter import AttemptCounter, CounterError, MAX_ATTEMPTS


class AttemptCounterTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.path = Path(self.temp_dir.name) / "counter.json"

    def tearDown(self):
        self.temp_dir.cleanup()

    def write_counter(self, attempts=0):
        self.path.write_text(
            json.dumps({"schema_version": 1, "attempts": attempts}),
            encoding="utf-8",
        )

    def test_missing_counter_fails_closed_without_creating_it(self):
        with self.assertRaises(CounterError):
            with AttemptCounter(self.path):
                pass
        self.assertFalse(self.path.exists())

    def test_corrupt_counter_fails_closed(self):
        self.path.write_text("{", encoding="utf-8")
        with self.assertRaises(CounterError):
            with AttemptCounter(self.path):
                pass

    def test_unreadable_counter_fails_closed_without_recreating_it(self):
        self.write_counter()
        original_open = Path.open

        def deny_counter_open(path, *args, **kwargs):
            if path == self.path:
                raise PermissionError("synthetic unreadable counter")
            return original_open(path, *args, **kwargs)

        with mock.patch.object(Path, "open", deny_counter_open):
            with self.assertRaises(CounterError):
                with AttemptCounter(self.path):
                    self.fail("unreadable counter must not enter the guarded run")
        self.assertTrue(self.path.is_file())

    @unittest.skipUnless(os.name == "nt", "M0A counter locking is native-Windows only")
    def test_lock_contention_fails_closed_for_second_runner(self):
        import msvcrt

        self.write_counter()
        with AttemptCounter(self.path) as active_runner:
            with mock.patch.object(
                msvcrt,
                "locking",
                side_effect=OSError("synthetic lock contention"),
            ):
                with self.assertRaises(CounterError):
                    with AttemptCounter(self.path):
                        self.fail("a second runner must not acquire the counter lock")
            self.assertEqual(active_runner.attempts, 0)

    @unittest.skipUnless(os.name == "nt", "M0A counter locking is native-Windows only")
    def test_real_child_process_lock_contention_fails_closed(self):
        self.write_counter()
        ready = Path(self.temp_dir.name) / "holder-ready"
        release = Path(self.temp_dir.name) / "holder-release"
        child_code = """
import sys
import time
from pathlib import Path
from spikes.m0a.request_counter import AttemptCounter

counter, ready, release = map(Path, sys.argv[1:4])
with AttemptCounter(counter):
    ready.write_text("locked", encoding="utf-8")
    deadline = time.monotonic() + 20
    while not release.exists() and time.monotonic() < deadline:
        time.sleep(0.01)
"""
        child = subprocess.Popen(
            [sys.executable, "-c", child_code, str(self.path), str(ready), str(release)],
            cwd=Path(__file__).resolve().parents[3],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        try:
            deadline = time.monotonic() + 10
            while not ready.exists() and child.poll() is None and time.monotonic() < deadline:
                time.sleep(0.01)
            self.assertTrue(ready.exists(), "child did not acquire the counter lock")
            with self.assertRaises(CounterError):
                with AttemptCounter(self.path):
                    self.fail("parent must not enter while child owns the OS lock")
        finally:
            release.write_text("release", encoding="utf-8")
            try:
                child.wait(timeout=10)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait(timeout=5)
        state = json.loads(self.path.read_text(encoding="utf-8"))
        self.assertEqual(state["attempts"], 0)

    def test_increment_is_persisted(self):
        self.write_counter()
        with AttemptCounter(self.path) as counter:
            self.assertEqual(counter.increment_before_attempt(), 1)
        state = json.loads(self.path.read_text(encoding="utf-8"))
        self.assertEqual(state["attempts"], 1)

    def test_hard_cap_fails_closed(self):
        self.write_counter(MAX_ATTEMPTS)
        with AttemptCounter(self.path) as counter:
            with self.assertRaises(CounterError):
                counter.increment_before_attempt()
        state = json.loads(self.path.read_text(encoding="utf-8"))
        self.assertEqual(state["attempts"], MAX_ATTEMPTS)


if __name__ == "__main__":
    unittest.main()
