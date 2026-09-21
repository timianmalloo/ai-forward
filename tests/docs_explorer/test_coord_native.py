import importlib.util
from pathlib import Path
import time
import unittest
from unittest import mock
from coord_native_peer import NativeMetadataPeer

SOURCE = Path(__file__).resolve().parents[2] / "pack/scripts/coord_native.py"
spec = importlib.util.spec_from_file_location("coord_native", SOURCE)
native = importlib.util.module_from_spec(spec)
spec.loader.exec_module(native)


class NativeMetadataTests(unittest.TestCase):
    def peer(self, mode="ok"):
        peer = NativeMetadataPeer(Path.cwd(), mode)
        self.addCleanup(peer.close)
        return peer

    def test_reads_exact_thread_metadata_without_prompt_or_subscription(self):
        peer = self.peer()
        result = native.thread_metadata(peer.path, "thread-exact")
        self.assertEqual({"id": "thread-exact", "cwd": str(Path.cwd())}, result)
        self.assertEqual(["initialize", "initialized", "thread/read"], [m["method"] for m in peer.messages])

    def test_hostile_protocol_and_foreign_identity_fail_closed(self):
        for mode in ("handshake", "identity", "no-direct", "oversize", "fragment"):
            with self.subTest(mode=mode):
                peer = self.peer(mode)
                with self.assertRaises(ValueError):
                    native.thread_metadata(peer.path, "thread-exact", timeout=.5)

    def test_silent_backend_obeys_deadline_and_cancellation(self):
        for cancelled in (False, True):
            with self.subTest(cancelled=cancelled):
                peer = self.peer("stall")
                started = time.monotonic()
                with self.assertRaises(TimeoutError):
                    native.thread_metadata(peer.path, "thread-exact", timeout=.15, cancelled=lambda: cancelled)
                self.assertLess(time.monotonic() - started, .5)

    def test_cancellation_during_final_native_read_cannot_authorize_queue(self):
        peer = self.peer()
        original = native.socket.socket
        state = {"cancelled": False}
        class CancellingSocket:
            def __init__(self, *args, **kwargs):
                self.socket = original(*args, **kwargs)
            def __getattr__(self, name):
                return getattr(self.socket, name)
            def __enter__(self):
                return self
            def __exit__(self, *args):
                self.socket.close()
            def recv(self, count):
                data = self.socket.recv(count)
                if b"canAcceptDirectInput" in data:
                    state["cancelled"] = True
                return data
        with mock.patch.object(native.socket, "socket", CancellingSocket):
            with self.assertRaises(TimeoutError):
                native.thread_metadata(peer.path, "thread-exact", cancelled=lambda: state["cancelled"])
        self.assertTrue(state["cancelled"])
