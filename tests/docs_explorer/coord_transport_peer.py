"""Real stdio protocol peer for bounded coordination transport failure tests."""
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import threading
import time

MODE = sys.argv[1]
ROOT = Path(sys.argv[2])
SECRET = "SECRET-MODEL-TOOL-ARGUMENT"


def send(value):
    print(json.dumps(value), flush=True)


def receive():
    line = sys.stdin.readline()
    if not line:
        raise SystemExit(0)
    value = json.loads(line)
    with (ROOT / "requests.jsonl").open("a") as stream:
        stream.write(json.dumps(value) + "\n")
    return value


def flood(fd):
    while True:
        os.write(fd, b"x" * 4096)


if MODE == "stderr_flood":
    flood(2)
if MODE == "stdout_flood":
    flood(1)
if MODE == "both_flood":
    threading.Thread(target=flood, args=(2,), daemon=True).start()
    flood(1)
if MODE == "malformed":
    print("{broken", flush=True)
    time.sleep(30)
if MODE == "invalid_utf8":
    os.write(1, b"\xff\n")
    time.sleep(30)
if MODE == "partial_eof":
    os.write(1, b'{"unfinished":')
    raise SystemExit(0)
if MODE == "unknown":
    send({"unrecognized": SECRET})
    time.sleep(30)
if MODE == "early_eof":
    raise SystemExit(0)
if MODE == "blocked_stdin":
    time.sleep(30)
if MODE in ("descendant", "exited_parent", "complete_descendant"):
    child = subprocess.Popen([sys.executable, __file__, "grandchild", str(ROOT)],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    (ROOT / "child.pid").write_text(str(child.pid))
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
    ready_deadline = time.monotonic() + 2
    while not (ROOT / "child.ready").exists() and time.monotonic() < ready_deadline:
        time.sleep(.005)
    if MODE == "exited_parent":
        raise SystemExit(0)
if MODE == "grandchild":
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
    (ROOT / "child.ready").touch()
    time.sleep(30)
    raise SystemExit(0)

turn = 0
while True:
    msg = receive()
    if msg.get("event") == "user":
        turn += 1
        if MODE == "hang":
            continue
        if turn == 1:
            send({"event": "init", "conversation_id": "agy-fixture", "init": {"cwd": SECRET}})
        send({"event": "step_update", "step_update": {"response": SECRET}})
        result = {"event": "result", "result": {
            "conversation_id": "agy-fixture", "status": "FAILURE" if MODE == "agy_failure" else "SUCCESS",
            "response": SECRET}}
        if MODE == "agy_duplicate":
            # One atomic write makes the unsolicited second completion buffered
            # before another prompt can have reached this real subprocess.
            os.write(1, (json.dumps(result) + "\n" + json.dumps(result) + "\n").encode())
            time.sleep(30)
        else:
            send(result)
        continue
    method = msg.get("method")
    if method == "initialize":
        methods = ([{"id": "cached_token"}] if MODE == "auth" else
                   [{"id": "interactive"}] if MODE == "auth_required" else [])
        result = {"protocolVersion": 1, "authMethods": methods, "agentInfo": {"version": "1.2.3"}}
    elif method == "authenticate":
        result = {}
    elif method == "session/new":
        if MODE == "auth_required":
            send({"jsonrpc": "2.0", "id": msg["id"], "error": {"code": -32000, "message": SECRET}})
            continue
        result = {"sessionId": "acp-fixture"}
    elif method == "session/cancel":
        (ROOT / "cancel.received").touch()
        continue
    elif method == "session/prompt":
        turn += 1
        if MODE in ("hang", "descendant"):
            continue
        if MODE == "slow_turn":
            time.sleep(.15)
        if MODE == "progress_flood":
            for _ in range(100):
                send({"jsonrpc": "2.0", "method": "session/update", "params": {
                    "sessionId": "acp-fixture", "update": {"sessionUpdate": "agent_message_chunk", "content": {"text": SECRET}}}})
        send({"jsonrpc": "2.0", "method": "session/update", "params": {
            "sessionId": "acp-fixture", "update": {"sessionUpdate": "agent_message_chunk", "content": {"text": SECRET}}}})
        if MODE in ("permission", "permission_no_reject"):
            options = [{"kind": "allow_always", "optionId": "allow"}]
            if MODE == "permission":
                options.append({"kind": "reject_once", "optionId": "reject"})
            send({"jsonrpc": "2.0", "id": "permission-request", "method": "session/request_permission", "params": {
                "sessionId": "acp-fixture", "options": options, "toolCall": {"rawInput": SECRET}}})
            receive()
        if MODE == "unknown_request":
            send({"jsonrpc": "2.0", "id": "unknown-request", "method": "fs/read_text_file", "params": {"path": SECRET}})
            receive()
        if MODE == "wrong_id":
            send({"jsonrpc": "2.0", "id": 99999, "result": {"stopReason": "end_turn"}})
            continue
        result = {"stopReason": "max_tokens" if MODE == "max_tokens" else "end_turn"}
    else:
        continue
    send({"jsonrpc": "2.0", "id": msg["id"], "result": result})
