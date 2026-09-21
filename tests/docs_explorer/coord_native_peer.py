"""Local protocol peer paired with the measured Codex metadata contract."""
import base64
import hashlib
import json
from pathlib import Path
import socket
import tempfile
import threading


class NativeMetadataPeer:
    def __init__(self, cwd, mode="ok"):
        self.temp = tempfile.TemporaryDirectory(prefix="coord-ws-", dir="/tmp")
        self.path = Path(self.temp.name).resolve() / "native.sock"
        self.cwd, self.mode = str(cwd), mode
        self.messages, self.errors = [], []
        self.stop = threading.Event()
        self.server = socket.socket(socket.AF_UNIX)
        self.server.bind(str(self.path))
        self.server.listen()
        self.server.settimeout(.1)
        self.thread = threading.Thread(target=self.serve, daemon=True)
        self.thread.start()

    def close(self):
        self.stop.set()
        self.thread.join(timeout=3)
        self.server.close()
        self.temp.cleanup()

    def serve(self):
        while not self.stop.is_set():
            try:
                client, _ = self.server.accept()
            except socket.timeout:
                continue
            try:
                with client:
                    client.settimeout(2)
                    self.connection(client)
            except (OSError, ValueError, AssertionError) as exc:
                self.errors.append(type(exc).__name__)

    @staticmethod
    def read(client, count):
        result = b""
        while len(result) < count:
            part = client.recv(count - len(result))
            if not part:
                raise ValueError("closed")
            result += part
        return result

    def connection(self, client):
        header = b""
        while not header.endswith(b"\r\n\r\n"):
            header += self.read(client, 1)
        fields = dict(line.split(": ", 1) for line in header.decode().split("\r\n")[1:] if line)
        key = fields["Sec-WebSocket-Key"]
        accept = base64.b64encode(hashlib.sha1((key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode()).digest()).decode()
        if self.mode == "handshake":
            accept = "wrong"
        client.sendall(("HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n"
                        "Sec-WebSocket-Accept: " + accept + "\r\n\r\n").encode())
        if self.mode == "stall":
            self.stop.wait(2)
            return
        for _ in range(3):
            prefix = self.read(client, 2)
            assert prefix[0] == 129 and prefix[1] & 128
            length = prefix[1] & 127
            if length == 126:
                length = int.from_bytes(self.read(client, 2), "big")
            mask = self.read(client, 4)
            payload = self.read(client, length)
            message = json.loads(bytes(v ^ mask[i % 4] for i, v in enumerate(payload)))
            self.messages.append(message)
            if message["method"] == "initialized":
                continue
            if message["method"] == "initialize":
                result = {"userAgent": "offline-native-peer"}
            else:
                assert message["method"] == "thread/read"
                assert message["params"]["includeTurns"] is False
                result = {"thread": {"id": message["params"]["threadId"], "cwd": self.cwd,
                                     "canAcceptDirectInput": self.mode != "no-direct"}}
                if self.mode == "identity":
                    result["thread"]["id"] = "another"
            data = json.dumps({"id": message["id"], "result": result}).encode()
            if self.mode == "oversize":
                client.sendall(bytes((129, 127)) + (2 ** 30).to_bytes(8, "big"))
                return
            if self.mode == "fragment":
                client.sendall(bytes((1, len(data))) + data)
                return
            prefix = bytes((129, len(data))) if len(data) < 126 else bytes((129, 126)) + len(data).to_bytes(2, "big")
            client.sendall(prefix + data)
