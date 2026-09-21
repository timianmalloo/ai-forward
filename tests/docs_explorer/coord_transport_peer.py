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
RECORDED = json.loads(Path(__file__).with_name("fixtures").joinpath("coord_native_envelopes.json").read_text())


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
        if turn == 1 and MODE != "agy_preinit_error":
            send({"event": "init", "conversation_id": "agy-fixture", "init": {"cwd": SECRET}})
        if MODE in ("agy_permission_step", "agy_error_step", "agy_foreign_step", "agy_missing_error_id", "agy_preinit_error"):
            step = RECORDED["agy_permission_step"]
            if MODE == "agy_error_step":
                step["step_update"]["tool_info"]["error"]["message"] = "unrelated SECRET tool failure"
            if MODE == "agy_foreign_step":
                step["step_update"]["conversation_id"] = "another-session"
            if MODE in ("agy_missing_error_id", "agy_preinit_error"):
                step["step_update"].pop("conversation_id")
            send(step)
        send({"event": "step_update", "step_update": {"response": SECRET}})
        result = {"event": "result", "result": {
            "conversation_id": "agy-fixture", "status": "FAILURE" if MODE == "agy_failure" else "SUCCESS",
            "response": SECRET}}
        if MODE == "agy_denied":
            result = RECORDED["agy_denied_result"]
        if MODE == "agy_empty_denials":
            result["result"]["denied_actions"] = []
        if MODE.startswith("agy_malformed_denials_"):
            result["result"]["denied_actions"] = [None, {}, [None], [{}], [{"action": 1}]][int(MODE.rsplit("_", 1)[1])]
        if MODE == "agy_duplicate":
            # One atomic write makes the unsolicited second completion buffered
            # before another prompt can have reached this real subprocess.
            os.write(1, (json.dumps(result) + "\n" + json.dumps(result) + "\n").encode())
            time.sleep(30)
        else:
            send(result)
        continue
    method = msg.get("method")
    if MODE.startswith("watcher_") and method == ("session/new" if MODE == "watcher_early" else "session/prompt"):
        reload_response = RECORDED["grok_reload"]
        if MODE == "watcher_extra":
            reload_response["extra"] = SECRET
        elif MODE == "watcher_inner_extra":
            reload_response["result"]["result"]["extra"] = SECRET
        elif MODE == "watcher_bool":
            reload_response["result"]["result"]["reloaded"] = True
        elif MODE == "watcher_float":
            reload_response["result"]["result"]["reloaded"] = 1.0
        elif MODE == "watcher_other_id":
            reload_response["id"] = "foreign-response"
        elif MODE == "watcher_bad_result":
            reload_response["result"] = []
        send(reload_response)
        if MODE == "watcher_hang":
            continue
        if MODE == "watcher_flood":
            while True:
                send(reload_response)
    if MODE.startswith("grok_") and method == {
            "grok_initialize": "initialize", "grok_authenticate": "authenticate"}.get(MODE, "session/new"):
        if MODE.startswith("grok_permission_"):
            permission_params = {"options": [{"kind": "reject_once", "optionId": "reject"}]}
            if MODE != "grok_permission_missing":
                permission_params["sessionId"] = "acp-fixture" if MODE == "grok_permission_candidate" else None
            send({"jsonrpc": "2.0", "id": "early-permission", "method": "session/request_permission", "params": permission_params})
            receive()
        for notification in RECORDED["grok_bootstrap"][:-1]:
            send(notification)
        early = RECORDED["grok_bootstrap"][-1]
        if MODE == "grok_missing_id":
            early["params"].pop("sessionId")
        elif MODE == "grok_empty_id":
            early["params"]["sessionId"] = ""
        elif MODE == "grok_long_id":
            early["params"]["sessionId"] = "x" * 257
        elif MODE == "grok_bad_update":
            early["params"]["update"] = []
        elif MODE == "grok_missing_discriminator":
            early["params"]["update"].pop("sessionUpdate")
        elif MODE == "grok_bad_discriminator":
            early["params"]["update"]["sessionUpdate"] = None
        send(early)
        if MODE == "grok_multiple":
            send(early)
            send(early)
        if MODE == "grok_changed":
            early["params"]["sessionId"] = "foreign-session"
            send(early)
        if MODE == "grok_flood":
            while True:
                send(early)
        if MODE == "grok_hang":
            time.sleep(30)
        if MODE == "grok_eof":
            raise SystemExit(0)
        if MODE == "grok_error":
            send({"jsonrpc": "2.0", "id": msg["id"], "error": {"code": -32603, "message": SECRET}})
            continue
    if MODE == "extensions":
        for notification in RECORDED["extensions"]:
            send(notification)
    if MODE == "extension_params":
        for params in ([], {}):
            send({"jsonrpc": "2.0", "method": "_optional", "params": params})
        send({"jsonrpc": "2.0", "method": "_optional"})
    if MODE == "extension_flood":
        while True:
            send(RECORDED["extensions"][0])
    if MODE.startswith("bad_extension_"):
        notification = RECORDED["extensions"][0]
        case = MODE.removeprefix("bad_extension_")
        if case == "params":
            notification["params"] = "SECRET"
        elif case == "null":
            notification["params"] = None
        elif case == "result":
            notification["result"] = {"sessionId": "fake"}
        elif case == "error":
            notification["error"] = {"code": -1}
        elif case == "id":
            notification["id"] = None
        elif case == "standard":
            notification["method"] = "unrecognized/standard"
        send(notification)
    if method == "initialize":
        methods = ([{"id": "cached_token"}] if MODE == "auth" or MODE.startswith("grok_") else
                   [{"id": "interactive"}] if MODE == "auth_required" else [])
        result = {"protocolVersion": 1, "authMethods": methods, "agentInfo": {"version": "1.2.3"}}
        if MODE.startswith("load_"):
            result["agentCapabilities"] = {"loadSession": True}
            if MODE == "load_no_capability":
                result.pop("agentCapabilities")
            elif MODE == "load_false_capability":
                result["agentCapabilities"]["loadSession"] = False
            elif MODE == "load_truthy_capability":
                result["agentCapabilities"]["loadSession"] = 1
        if MODE.startswith("roots_"):
            result["agentInfo"]["name"] = "@agentclientprotocol/codex-acp"
            result["agentCapabilities"] = {"sessionCapabilities": {"additionalDirectories": {}}}
            if MODE == "roots_no_capability":
                result["agentCapabilities"] = {}
        if MODE.startswith("watcher_"):
            result.pop("agentInfo")
            result["_meta"] = {"grokShell": True, "agentVersion": "1.0.34"}
            if MODE == "watcher_other_version":
                result["_meta"]["agentVersion"] = "1.0.35"
            elif MODE == "watcher_no_shell":
                result["_meta"].pop("grokShell")
            elif MODE == "watcher_string_shell":
                result["_meta"]["grokShell"] = "true"
            elif MODE == "watcher_agentinfo_only":
                result.pop("_meta")
                result["agentInfo"] = {"version": "1.0.34"}
    elif method == "authenticate":
        result = {}
    elif method == "session/load":
        if MODE == "load_hang":
            continue
        if MODE == "load_permission":
            send({"jsonrpc": "2.0", "id": "early-permission", "method": "session/request_permission",
                  "params": {"sessionId": "acp-fixture", "toolCall": {},
                             "options": [{"optionId": "once", "kind": "allow_once"}]}})
            receive()
        # Recorded Grok live load replays history before returning its response.
        send({"jsonrpc": "2.0", "method": "session/update", "params": {
            "sessionId": "foreign" if MODE == "load_foreign_update" else "acp-fixture",
            "update": {"sessionUpdate": "agent_message_chunk", "content": {"type": "text", "text": SECRET}}}})
        if MODE == "load_error":
            send({"jsonrpc": "2.0", "id": msg["id"], "error": {"code": -32603, "message": SECRET}})
            continue
        result = {} if MODE == "load_omitted" else {"sessionId": "acp-fixture"}
        if MODE == "load_mismatch":
            result["sessionId"] = "foreign"
        elif MODE == "load_null":
            result["sessionId"] = None
        elif MODE.startswith("load_meta"):
            result = {"_meta": {"sessionId": "foreign" if MODE == "load_meta_mismatch" else "acp-fixture"}}
        elif MODE.startswith("load_cwd_"):
            cwd = str(ROOT) if MODE == "load_cwd_matching" else "/foreign" if MODE == "load_cwd_foreign" else None
            if MODE == "load_cwd_no_identity":
                cwd = str(ROOT)
            detail = {"cwd": cwd}
            if MODE != "load_cwd_no_identity":
                detail["sessionId"] = "acp-fixture"
            result = {"_meta": {"sessionId": "acp-fixture", "x.ai/sessionDetail": detail}}
    elif method == "session/new":
        if MODE == "auth_required":
            send({"jsonrpc": "2.0", "id": msg["id"], "error": {"code": -32000, "message": SECRET}})
            continue
        result = {"sessionId": "acp-fixture"}
        if MODE.startswith("mode_"):
            result["modes"] = {"currentModeId": "agent", "availableModes": [{"id": "read-only", "name": "Ask for approval"}]}
            if MODE == "mode_unknown":
                result["modes"]["availableModes"] = [{"id": "agent"}]
            elif MODE == "mode_duplicate":
                result["modes"]["availableModes"] *= 2
            elif MODE == "mode_malformed":
                result["modes"]["availableModes"] = {"id": "read-only"}
        if MODE == "grok_mismatch":
            result["sessionId"] = "foreign-session"
    elif method == "session/set_mode":
        if MODE == "mode_error":
            send({"jsonrpc": "2.0", "id": msg["id"], "error": {"code": -32603, "message": SECRET}})
            continue
        result = {}
    elif method == "session/cancel":
        (ROOT / "cancel.received").touch()
        continue
    elif method == "session/prompt":
        turn += 1
        if MODE in ("hang", "descendant", "load_prompt_hang"):
            continue
        if MODE == "slow_turn":
            time.sleep(.15)
        if MODE == "progress_flood":
            for _ in range(100):
                send({"jsonrpc": "2.0", "method": "session/update", "params": {
                    "sessionId": "acp-fixture", "update": {"sessionUpdate": "agent_message_chunk", "content": {"text": SECRET}}}})
        send({"jsonrpc": "2.0", "method": "session/update", "params": {
            "sessionId": "acp-fixture", "update": {"sessionUpdate": "agent_message_chunk", "content": {"text": SECRET}}}})
        if MODE in ("permission", "permission_no_reject", "roots_permission") or MODE.startswith("runtime_permission"):
            options = [{"kind": "allow_always", "optionId": "allow"}]
            if MODE in ("permission", "roots_permission") or MODE.startswith("runtime_permission"):
                options.append({"kind": "reject_once", "optionId": "reject"})
            if MODE.startswith("runtime_permission"):
                options.append({"kind": "allow_once", "optionId": "once"})
            if MODE == "runtime_permission_duplicate":
                options.append({"kind": "allow_once", "optionId": "reject"})
            send({"jsonrpc": "2.0", "id": "permission-request", "method": "session/request_permission", "params": {
                "sessionId": "acp-fixture", "options": options, "toolCall": {"rawInput": SECRET}}})
            if MODE == "runtime_permission_flood":
                flood(2)
            receive()
        if MODE in ("unknown_request", "extension_request"):
            send({"jsonrpc": "2.0", "id": "unknown-request", "method": "_custom/request" if MODE == "extension_request" else "fs/read_text_file", "params": {"path": SECRET}})
            receive()
        if MODE == "foreign_update":
            send({"jsonrpc": "2.0", "method": "session/update", "params": {"sessionId": "other-session", "update": {"sessionUpdate": "agent_message_chunk"}}})
        if MODE == "wrong_id":
            send({"jsonrpc": "2.0", "id": 99999, "result": {"stopReason": "end_turn"}})
            continue
        result = {"stopReason": "max_tokens" if MODE == "max_tokens" else "end_turn"}
    else:
        continue
    send({"jsonrpc": "2.0", "id": msg["id"], "result": result})
