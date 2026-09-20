"""Offline ACP peer for real-process launcher composition tests; never a provider claim."""
import json
import os
from pathlib import Path
import sys
import subprocess
import time

mode = sys.argv[1] if len(sys.argv) > 1 else "ok"


def send(message):
    print(json.dumps(message), flush=True)


for line in sys.stdin:
    message = json.loads(line)
    method = message.get("method")
    if method == "initialize":
        result = {"protocolVersion": 1, "agentCapabilities": {},
                  "agentInfo": {"name": "offline-peer", "version": "1"}}
    elif method == "session/new":
        assert message["params"]["cwd"] == str(Path.cwd())
        result = {"sessionId": "fixture-session"}
    elif method == "session/prompt":
        Path("prompt-started").write_text(str(os.getpid()), encoding="utf-8")
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
                "cwd": str(Path.cwd()), "turns": turns + 1}), encoding="utf-8")
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
