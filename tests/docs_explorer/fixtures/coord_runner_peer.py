"""Offline ACP peer for real-process launcher composition tests; never a provider claim."""
import json
import os
from pathlib import Path
import sys
import subprocess
import time

mode = sys.argv[1] if len(sys.argv) > 1 else "ok"
additional_roots = None
if mode in ("startup-retry", "dirty-startup-retry"):
    marker = Path(__file__).parent / "startup-attempt"
    attempts = int(marker.read_text()) if marker.exists() else 0
    marker.write_text(str(attempts + 1))
    if attempts == 0:
        if mode == "dirty-startup-retry":
            Path("unexpected-change").write_text("inspect before retry")
        raise SystemExit(1)


def send(message):
    print(json.dumps(message), flush=True)


for line in sys.stdin:
    message = json.loads(line)
    if message.get("event") == "user":
        marker = Path("prompt-count")
        count = int(marker.read_text()) + 1 if marker.exists() else 1
        marker.write_text(str(count))
        send({"event": "init", "conversation_id": "fixture-session"})
        if mode == "agy-error":
            send({"event": "step_update", "step_update": {"conversation_id": "fixture-session",
                "state": "ERROR", "step_type": "tool", "tool_info": {"error": {
                    "type": "TOOL_ERROR", "message": "permission check failed for write_file SECRET_DO_NOT_LOG"}}}})
        send({"event": "result", "result": {"conversation_id": "fixture-session", "status": "SUCCESS",
            "denied_actions": [{"action": "write_file", "display_name": "SECRET_DO_NOT_LOG"}]}})
        continue
    method = message.get("method")
    if mode == "extensions":
        send({"jsonrpc": "2.0", "method": "_auth/status_update", "params": {"authStatus": "SECRET_DO_NOT_LOG"}})
    if method == "initialize":
        result = {"protocolVersion": 1, "agentCapabilities": {},
                  "agentInfo": {"name": "offline-peer", "version": "1"}}
        if mode == "file-roots":
            result["agentInfo"]["name"] = "@agentclientprotocol/codex-acp"
            result["agentCapabilities"] = {"sessionCapabilities": {"additionalDirectories": {}}}
    elif method == "session/new":
        assert message["params"]["cwd"] == str(Path.cwd())
        additional_roots = message["params"].get("additionalDirectories")
        result = {"sessionId": "fixture-session"}
    elif method == "session/prompt":
        Path("prompt-started").write_text(str(os.getpid()), encoding="utf-8")
        if mode == "post-dispatch-eof":
            raise SystemExit(1)
        if mode == "permission":
            send({"jsonrpc": "2.0", "id": "permission-1", "method": "session/request_permission", "params": {
                "sessionId": "fixture-session", "toolCall": {"title": "SECRET harmless fixture receipt"},
                "options": [{"optionId": "yes", "kind": "allow_once", "name": "Allow once"},
                            {"optionId": "no", "kind": "reject_once", "name": "Reject"}]}})
            response = json.loads(sys.stdin.readline())
            assert response["id"] == "permission-1"
            if response["result"]["outcome"].get("optionId") != "yes":
                send({"jsonrpc": "2.0", "id": message["id"], "result": {"stopReason": "end_turn"}})
                continue
        if mode == "hang":
            time.sleep(30)
        if mode == "delay":
            time.sleep(0.8)
        send({"jsonrpc": "2.0", "method": "session/update", "params": {
            "sessionId": "fixture-session", "update": {"sessionUpdate": "agent_message_chunk",
                "content": {"type": "text", "text": "SECRET_DO_NOT_LOG"}}}})
        if mode != "missing":
            path = Path("receipt.json")
            turns = json.loads(path.read_text(encoding="utf-8"))["turns"] if path.exists() else 0
            path.write_text(json.dumps({"session": os.environ["AGENT_SESSION"],
                "host": os.environ["AGENT_HOST"], "wi": os.environ["AGENT_WI"],
                "cwd": str(Path.cwd()), "turns": turns + 1,
                "additional_roots": additional_roots}), encoding="utf-8")
            if mode == "commit":
                subprocess.run(["git", "add", "receipt.json"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                subprocess.run(["git", "commit", "-qm", "worker receipt"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        result = {"stopReason": "end_turn"}
    elif method == "session/cancel":
        continue
    else:
        result = {}
    if "id" in message:
        send({"jsonrpc": "2.0", "id": message["id"], "result": result})
