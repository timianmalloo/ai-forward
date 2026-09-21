#!/usr/bin/env python3
"""Bounded POSIX ACP / Agy session IO. Native harness policy remains authoritative.

This is a lifecycle adapter, not an editor proxy or an approval broker. Only
locally selected operational fields leave this module; wire bodies are discarded.
"""
import json
import math
import os
import re
import selectors
import signal
import subprocess
import time


MAX_INPUT_BYTES = 16 * 1024 * 1024
POLL_SECONDS = 0.1
CLEANUP_SECONDS = 4.0


class _Failure(Exception):
    def __init__(self, code, outcome="failed"):
        super().__init__(code)
        self.code = code
        self.outcome = outcome


def _identifier(value):
    return isinstance(value, str) and re.fullmatch(r"[A-Za-z0-9._:/+-]{1,256}", value) is not None


def _signal_group(process, sig):
    # macOS can return EPERM for an unreaped zombie. Reap before signalling,
    # and retry once if exit raced the first poll. Still signal live descendants.
    process.poll()
    for attempt in range(2):
        try:
            os.killpg(process.pid, sig)
            return None
        except ProcessLookupError:
            return None
        except PermissionError:
            if attempt == 0 and process.poll() is not None:
                continue
            return "group_signal_failed"
        except OSError:
            return "group_signal_failed"
    return "group_signal_failed"


class _Wire:
    """One bounded input frame and output buffer; no transcript or message queue."""

    def __init__(self, deadline, output_limit, cancelled, result):
        self.process = None
        self.deadline = deadline
        self.output_limit = output_limit
        self.cancelled = cancelled
        self.result = result
        self.selector = selectors.DefaultSelector()
        self.incoming = bytearray()
        self.outgoing = bytearray()
        self.stdout_eof = False

    def attach(self, process):
        self.process = process
        for stream, label in ((process.stdout, "stdout"), (process.stderr, "stderr")):
            os.set_blocking(stream.fileno(), False)
            self.selector.register(stream, selectors.EVENT_READ, label)
        os.set_blocking(process.stdin.fileno(), False)

    def check(self):
        if time.monotonic() >= self.deadline:
            raise _Failure("deadline_exceeded")
        try:
            cancelled = self.cancelled()
        except Exception:
            raise _Failure("callback_failed") from None
        if cancelled:
            raise _Failure("cancelled", "cancelled")

    def queue(self, message):
        payload = (json.dumps(message, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")
        if len(payload) + len(self.outgoing) > MAX_INPUT_BYTES:
            raise _Failure("input_limit_exceeded")
        if not self.outgoing:
            self.selector.register(self.process.stdin, selectors.EVENT_WRITE, "stdin")
        self.outgoing.extend(payload)

    def pump(self, timeout):
        for key, _ in self.selector.select(timeout):
            if key.data == "stdin":
                try:
                    count = os.write(key.fd, memoryview(self.outgoing)[:65536])
                except BlockingIOError:
                    continue
                except BrokenPipeError:
                    raise _Failure("early_eof") from None
                del self.outgoing[:count]
                if not self.outgoing:
                    self.selector.unregister(key.fileobj)
                continue
            remaining = self.output_limit - self.result["stdout_bytes"] - self.result["stderr_bytes"]
            if remaining < 0:
                raise _Failure("output_limit_exceeded")
            try:
                data = os.read(key.fd, min(65536, max(1, remaining + 1)))
            except BlockingIOError:
                continue
            if not data:
                self.selector.unregister(key.fileobj)
                if key.data == "stdout":
                    self.stdout_eof = True
                continue
            self.result[key.data + "_bytes"] += len(data)
            if len(data) > remaining:
                raise _Failure("output_limit_exceeded")
            if key.data == "stdout":
                self.incoming.extend(data)

    def receive(self):
        while True:
            self.check()
            newline = self.incoming.find(b"\n")
            if newline >= 0:
                line = bytes(self.incoming[:newline])
                del self.incoming[:newline + 1]
                try:
                    value = json.loads(line.decode("utf-8"))
                except (ValueError, UnicodeError, RecursionError):
                    raise _Failure("protocol_error") from None
                if not isinstance(value, dict):
                    raise _Failure("protocol_error")
                return value
            if self.stdout_eof:
                raise _Failure("protocol_error" if self.incoming else "early_eof")
            self.pump(min(POLL_SECONDS, max(0, self.deadline - time.monotonic())))

    def flush_input(self):
        while self.outgoing:
            self.check()
            self.pump(min(POLL_SECONDS, max(0, self.deadline - time.monotonic())))

    def cleanup(self, session_id, graceful):
        """Always kill our group, even if the direct child has already exited."""
        if self.process is None:
            self.selector.close()
            return None
        cleanup_end = min(time.monotonic() + CLEANUP_SECONDS, self.deadline + CLEANUP_SECONDS)
        error = None
        if graceful and session_id and not self.outgoing:
            try:
                self.queue({"jsonrpc": "2.0", "method": "session/cancel", "params": {"sessionId": session_id}})
                grace_end = min(cleanup_end, time.monotonic() + .2)
                while time.monotonic() < grace_end:
                    self.pump(min(.05, max(0, grace_end - time.monotonic())))
            except (OSError, _Failure):
                pass  # Best effort; group termination below is unconditional.
        error = _signal_group(self.process, signal.SIGTERM)
        try:
            self.process.wait(timeout=max(0, min(.2, cleanup_end - time.monotonic())))
        except subprocess.TimeoutExpired:
            pass
        error = _signal_group(self.process, signal.SIGKILL) or error
        try:
            self.process.wait(timeout=max(0, cleanup_end - time.monotonic()))
        except subprocess.TimeoutExpired:
            error = "process_reap_failed"
        finally:
            self.selector.close()
            for stream in (self.process.stdin, self.process.stdout, self.process.stderr):
                stream.close()
        return error


class _Session:
    def __init__(self, wire, result, emit, before_prompt):
        self.wire = wire
        self.result = result
        self.emit = emit
        self.before_prompt = before_prompt
        self.sequence = 0
        self.turn = 0
        self.last_progress = float("-inf")
        self.creating_session_id = None
        self.creating_updates = 0
        self.grok_reload_compat = False

    def event(self, event, **fields):
        try:
            self.emit({"event": event, **fields})
        except Exception:
            raise _Failure("callback_failed") from None

    def admit(self):
        self.wire.check()
        try:
            admitted = self.before_prompt(max(0, self.wire.deadline - time.monotonic()))
        except Exception:
            raise _Failure("callback_failed") from None
        self.wire.check()  # A slow admission check is charged to this attempt.
        if not admitted:
            raise _Failure("dispatch_refused", "cancelled")
        self.turn += 1
        self.event("prompt_started", turn=self.turn)

    def progress(self, count=1):
        self.result["progress_updates"] += count
        now = time.monotonic()
        if now - self.last_progress >= 1:
            self.last_progress = now
            self.event("progress", turn=self.turn, progress_updates=self.result["progress_updates"])

    def permission(self, message):
        params = message.get("params")
        if (not self.result["session_id"] or not isinstance(params, dict)
                or params.get("sessionId") != self.result["session_id"]):
            raise _Failure("protocol_error")
        options = params.get("options", [])
        if not isinstance(options, list):
            raise _Failure("protocol_error")
        selected = next((option.get("optionId") for option in options if isinstance(option, dict)
                         and option.get("kind") == "reject_once" and isinstance(option.get("optionId"), str)), None)
        outcome = {"outcome": "selected", "optionId": selected} if selected is not None else {"outcome": "cancelled"}
        self.wire.queue({"jsonrpc": "2.0", "id": message["id"], "result": {"outcome": outcome}})
        self.result["permission_requests"] += 1
        self.event("permission_denied", permission_requests=self.result["permission_requests"],
                   action_id="permission-" + str(self.result["permission_requests"]))

    def rpc(self, method, params):
        self.sequence += 1
        request_id = self.sequence
        self.wire.queue({"jsonrpc": "2.0", "id": request_id, "method": method, "params": params})
        while True:
            message = self.wire.receive()
            if message.get("jsonrpc") != "2.0":
                raise _Failure("protocol_error")
            if "method" in message:
                if (not isinstance(message["method"], str) or "result" in message or "error" in message
                        or ("params" in message and not isinstance(message["params"], (dict, list)))):
                    raise _Failure("protocol_error")
                if "id" in message:
                    if type(message["id"]) not in (str, int):
                        raise _Failure("protocol_error")
                    if message["method"] == "session/request_permission":
                        self.permission(message)
                    else:
                        self.wire.queue({"jsonrpc": "2.0", "id": message["id"], "error": {
                            "code": -32601, "message": "Method not supported"}})
                elif message["method"] == "session/update":
                    update = message.get("params")
                    if (not isinstance(update, dict) or not isinstance(update.get("update"), dict)
                            or not _identifier(update.get("sessionId"))
                            or not _identifier(update["update"].get("sessionUpdate"))):
                        raise _Failure("protocol_error")
                    if method == "session/new" and self.result["session_id"] is None:
                        # Grok 1.0.34 emits updates before the creation response.
                        # Retain identity/count only; the response grants authority.
                        if self.creating_session_id not in (None, update["sessionId"]):
                            raise _Failure("protocol_error")
                        self.creating_session_id = update["sessionId"]
                        self.creating_updates += 1
                    elif self.result["session_id"] and update["sessionId"] == self.result["session_id"]:
                        self.progress()
                    else:
                        raise _Failure("protocol_error")
                elif message["method"].startswith("_"):
                    # ACP v1 extension notifications are optional, one-way data.
                    # Count without retaining names/payloads or emitting per-item events;
                    # the same wire deadline and byte limit still bound every receive.
                    self.result["extension_notifications"] += 1
                else:
                    raise _Failure("protocol_error")
                continue
            # Grok 1.0.34 injects its own skills watcher acknowledgement into ACP.
            # This exact, measured exception never completes our pending request.
            if (self.grok_reload_compat and method == "session/prompt" and self.result["session_id"]
                    and message == {"jsonrpc": "2.0", "id": "skills-reload", "result": {"result": {"reloaded": 1}}}
                    and type(message["result"]["result"]["reloaded"]) is int):
                self.result["compatibility_responses"] += 1
                continue
            if type(message.get("id")) is not int or message["id"] != request_id:
                raise _Failure("protocol_error")
            if "error" in message:
                error = message["error"]
                if not isinstance(error, dict) or type(error.get("code")) is not int:
                    raise _Failure("protocol_error")
                if error["code"] == -32000:  # ACP schema: authentication required.
                    raise _Failure("authentication_required", "blocked")
                raise _Failure("authentication_failed" if method == "authenticate" else "remote_error")
            if not isinstance(message.get("result"), dict):
                raise _Failure("protocol_error")
            return message["result"]

    def acp(self, cwd, prompts):
        info = self.rpc("initialize", {"protocolVersion": 1, "clientCapabilities": {},
                                      "clientInfo": {"name": "ai-forward-coordination", "version": "1"}})
        if type(info.get("protocolVersion")) is not int or info["protocolVersion"] != 1:
            raise _Failure("protocol_error")
        agent = info.get("agentInfo", {})
        version = agent.get("version") if isinstance(agent, dict) else None
        self.result["reported_version"] = version if _identifier(version) else None
        if self.result["reported_version"]:
            self.result["reported_version_source"] = "agentInfo.version"
        metadata = info.get("_meta", {})
        if isinstance(metadata, dict) and metadata.get("grokShell") is True:
            if self.result["reported_version"] is None and _identifier(metadata.get("agentVersion")):
                self.result["reported_version"] = metadata["agentVersion"]
                self.result["reported_version_source"] = "grok._meta.agentVersion"
            self.grok_reload_compat = (metadata.get("agentVersion") == "1.0.34"
                                       and self.result["reported_version"] == "1.0.34")
        auth = info.get("authMethods", [])
        if not isinstance(auth, list):
            raise _Failure("protocol_error")
        if any(isinstance(item, dict) and item.get("id") == "cached_token" for item in auth):
            self.rpc("authenticate", {"methodId": "cached_token", "_meta": {"headless": True}})
        created = self.rpc("session/new", {"cwd": os.fspath(cwd), "mcpServers": []})
        if (not _identifier(created.get("sessionId"))
                or self.creating_session_id not in (None, created["sessionId"])):
            raise _Failure("protocol_error")
        self.result["session_id"] = created["sessionId"]
        self.event("session_created")
        if self.creating_updates:
            self.progress(self.creating_updates)
        self.creating_session_id = None
        self.creating_updates = 0
        for prompt in prompts:
            if self.result["permission_requests"]:
                raise _Failure("permission_denied", "blocked")
            self.admit()
            response = self.rpc("session/prompt", {"sessionId": self.result["session_id"],
                                                    "prompt": [{"type": "text", "text": prompt}]})
            if self.result["permission_requests"]:
                raise _Failure("permission_denied", "blocked")
            if response.get("stopReason") != "end_turn":
                raise _Failure("incomplete")
            self.result["turns_completed"] += 1
            self.event("turn_completed", turn=self.turn)

    def native_denial(self, count):
        self.result["native_denials"] += count
        self.event("native_permission_denied", native_denials=self.result["native_denials"],
                   action_id="native-denial-" + str(self.result["native_denials"]))
        raise _Failure("permission_denied", "blocked")

    def agy(self, prompts):
        # Observed Agy 1.2.7 wire: init.conversation_id; result.result.status.
        for prompt in prompts:
            if self.turn:
                # Native results have no observed per-turn id. Reject output
                # already waiting at the boundary; it cannot answer an unsent
                # prompt. This is sequencing, not malicious-provider protection.
                self.wire.check()
                self.wire.pump(0)
                if self.wire.incoming:
                    raise _Failure("protocol_error")
            self.admit()
            self.wire.queue({"event": "user", "message": {"content": prompt}})
            self.wire.flush_input()
            while True:
                message = self.wire.receive()
                if message.get("event") == "init":
                    session_id = message.get("conversation_id")
                    if not _identifier(session_id) or self.result["session_id"] not in (None, session_id):
                        raise _Failure("protocol_error")
                    self.result["session_id"] = session_id
                    self.event("session_created")
                elif message.get("event") == "step_update":
                    step = message.get("step_update")
                    if (not isinstance(step, dict) or ("conversation_id" in step
                            and (not self.result["session_id"] or step["conversation_id"] != self.result["session_id"]))):
                        raise _Failure("protocol_error")
                    self.progress()
                    if step.get("state") == "ERROR":
                        if not self.result["session_id"] or step.get("conversation_id") != self.result["session_id"]:
                            raise _Failure("protocol_error")
                        info = step.get("tool_info", {})
                        if not isinstance(info, dict) or not isinstance(info.get("error", {}), dict):
                            raise _Failure("protocol_error")
                        error = info.get("error", {})
                        detail = error.get("message", "")
                        # This narrow signature is from Agy 1.2.7's native TOOL_ERROR,
                        # not assistant prose. Other error steps also stop dispatch.
                        if (step.get("step_type") == "tool" and error.get("type") == "TOOL_ERROR"
                                and isinstance(detail, str) and detail.startswith("permission check failed for ")):
                            self.native_denial(1)
                        raise _Failure("native_tool_error")
                elif message.get("event") == "result":
                    response = message.get("result")
                    if (not isinstance(response, dict) or not self.result["session_id"]
                            or response.get("conversation_id") != self.result["session_id"]):
                        raise _Failure("protocol_error")
                    denied = response.get("denied_actions", [])
                    if (not isinstance(denied, list) or any(not isinstance(item, dict)
                            or not _identifier(item.get("action")) for item in denied)):
                        raise _Failure("protocol_error")
                    if denied:
                        self.native_denial(len(denied))
                    if response.get("status") != "SUCCESS":
                        raise _Failure("incomplete")
                    self.result["turns_completed"] += 1
                    self.event("turn_completed", turn=self.turn)
                    break
                else:
                    raise _Failure("protocol_error")


def run_session(transport, argv, cwd, env, prompts, deadline_seconds, output_limit,
                emit, cancelled, before_prompt=None):
    """Run admitted turns in one owned process group; return metadata, never bodies.

    Callbacks are caller-owned, fast/bounded functions. Admission is charged to the
    same attempt deadline. The caller must bind native permissions and trust before
    launch. No capabilities or instructions are inferred from a successful result.
    """
    started = time.monotonic()
    result = {"outcome": "failed", "code": "invalid_input", "session_id": None,
              "turns_completed": 0, "stdout_bytes": 0, "stderr_bytes": 0,
              "duration_seconds": 0.0, "permission_requests": 0,
              "cleanup_error": None, "reported_version": None, "progress_updates": 0,
              "reported_version_source": None, "compatibility_responses": 0}
    result.update(extension_notifications=0, native_denials=0)
    wire = None
    try:
        if os.name != "posix":
            raise _Failure("unsupported_platform", "blocked")
        if (transport not in ("acp", "agy") or not isinstance(argv, (list, tuple)) or not argv
                or any(not isinstance(arg, str) or "\0" in arg for arg in argv)
                or not isinstance(prompts, (list, tuple)) or not 1 <= len(prompts) <= 8
                or any(not isinstance(prompt, str) or not prompt for prompt in prompts)
                or type(deadline_seconds) not in (int, float) or not math.isfinite(deadline_seconds)
                or not 0 < deadline_seconds <= 3600 or type(output_limit) is not int
                or not 0 < output_limit <= MAX_INPUT_BYTES):
            raise _Failure("invalid_input", "blocked")
        if any(len(prompt) > MAX_INPUT_BYTES for prompt in prompts):
            raise _Failure("input_limit_exceeded", "blocked")
        deadline = started + deadline_seconds
        wire = _Wire(deadline, output_limit, cancelled, result)
        wire.check()
        try:
            process = subprocess.Popen(argv, cwd=cwd, env=env, stdin=subprocess.PIPE,
                                       stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                       bufsize=0, start_new_session=True)
        except (OSError, ValueError, TypeError):
            raise _Failure("spawn_failed") from None
        wire.attach(process)
        session = _Session(wire, result, emit, before_prompt or (lambda remaining: True))
        if transport == "acp":
            session.acp(cwd, prompts)
        else:
            session.agy(prompts)
        wire.check()
        result.update(outcome="complete", code="complete")
    except _Failure as failure:
        result.update(outcome=failure.outcome, code=failure.code)
    except (OSError, ValueError, UnicodeError, RecursionError):
        result.update(outcome="failed", code="io_error")
    finally:
        if wire is not None:
            result["cleanup_error"] = wire.cleanup(result["session_id"], transport == "acp" and result["code"] != "complete")
        # A rejected request cannot become success or a less informative timeout.
        if result["permission_requests"] or result["native_denials"]:
            result.update(outcome="blocked", code="permission_denied")
        if result["cleanup_error"] and result["outcome"] == "complete":
            result.update(outcome="failed", code="cleanup_failed")
        result["duration_seconds"] = round(time.monotonic() - started, 6)
    return result
