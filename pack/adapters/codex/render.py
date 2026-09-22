"""One deterministic Codex projection for dogfood sync and consumer installation."""
import argparse
import copy
import json
from pathlib import Path
import re


def split_frontmatter(text):
    match = re.match(r"\A---\n(.*?)\n---\n", text, re.S)
    if not match:
        raise ValueError("expected YAML frontmatter")
    return match.group(1), text[match.end():]


def field(front, name):
    match = re.search(r"^" + re.escape(name) + r":\s*(.+)$", front, re.M)
    if not match:
        raise ValueError("missing persona " + name)
    return match.group(1).strip().strip("\"'")


def skill_text(text, guidance):
    front, body = split_frontmatter(text)
    return "---\n" + front + "\n---\n\n" + guidance.rstrip() + "\n\n" + body.lstrip()


def agent_text(text, guidance):
    front, body = split_frontmatter(text)
    name = field(front, "name")
    if not re.fullmatch(r"[a-z0-9][a-z0-9_-]*", name):
        raise ValueError("unsafe persona name: " + name)
    knowledge = re.search(r"^knowledge:\s*\[(.*?)\]", front, re.M)
    lens = ""
    if knowledge:
        docs = [x.strip().strip("\"'") for x in knowledge.group(1).split(",")]
        lens = "\nKnowledge lens (read when relevant): " + ", ".join(
            ".claude/knowledge/" + item + ".md" for item in docs) + ".\n"
    values = {"name": name, "description": field(front, "description"),
              "developer_instructions": guidance.rstrip() + "\n" + lens + "\n" + body.lstrip()}
    # JSON basic strings are TOML basic strings for this textual input. Escaped
    # newlines keep arbitrary persona prose out of TOML syntax and table names.
    return name, "".join(key + " = " + json.dumps(value, ensure_ascii=False) + "\n"
                         for key, value in values.items())


def projections(pack):
    """Destination -> (canonical relative source, generated text)."""
    pack = Path(pack)
    guidance = (pack / "adapters/codex/surface.md").read_text(encoding="utf-8")
    result = {}
    for skill in sorted((pack / "commands").iterdir()):
        if not (skill / "SKILL.md").is_file():
            continue
        for source in sorted(skill.rglob("*")):
            if not source.is_file() or "__pycache__" in source.parts:
                continue
            text = source.read_text(encoding="utf-8")
            if source.name == "SKILL.md":
                text = skill_text(text, guidance)
            dest = ".agents/skills/" + source.relative_to(pack / "commands").as_posix()
            result[dest] = (source.relative_to(pack).as_posix(), text)
    for folder, pattern in (("claude-code", "*.md"), ("copilot", "*_agent.md")):
        for source in sorted((pack / "adapters" / folder / "agents").glob(pattern)):
            name, text = agent_text(source.read_text(encoding="utf-8"), guidance)
            dest = ".codex/agents/" + name + ".toml"
            if dest in result:
                raise ValueError("duplicate Codex persona: " + name)
            result[dest] = (source.relative_to(pack).as_posix(), text)
    result["docs/ai-forward-pack/codex-surface.md"] = ("adapters/codex/surface.md", guidance)
    return result


def merge_hooks(current, snippet):
    """Preserve consumer entries; append exact missing pack definitions once.

    A changed definition is a conflict, not permission to run both versions.
    Handler statusMessage is the explicit pack identity in this adapter.
    """
    if not isinstance(current, dict) or not isinstance(current.get("hooks", {}), dict):
        raise ValueError("Codex hooks must be an object with an object-valued hooks field")
    merged = copy.deepcopy(current)
    hooks = merged.setdefault("hooks", {})
    for event, entries in snippet["hooks"].items():
        have = hooks.setdefault(event, [])
        if not isinstance(have, list):
            raise ValueError("Codex hook event must be an array: " + event)
        for entry in entries:
            if entry in have:
                continue
            ids = {h.get("statusMessage") for h in entry["hooks"] if h.get("statusMessage")}
            for existing in have:
                if not isinstance(existing, dict) or not isinstance(existing.get("hooks", []), list):
                    raise ValueError("invalid Codex hook matcher group: " + event)
                if ids & {h.get("statusMessage") for h in existing.get("hooks", []) if isinstance(h, dict)}:
                    raise ValueError("modified pack hook requires reconciliation: " + event)
            have.append(copy.deepcopy(entry))
    return merged


def sync(root):
    root = Path(root).resolve()
    expected = projections(root / "pack")
    # Only remove stale files inside the two generated namespaces. Never reset
    # .agents or .codex: they also carry user configuration and coordination data.
    for relative in (".agents/skills", ".codex/agents"):
        folder = root / relative
        for path in folder.rglob("*") if folder.exists() else ():
            if path.is_file() and path.relative_to(root).as_posix() not in expected:
                if folder.resolve() not in path.resolve().parents:
                    raise ValueError("refusing stale-file removal outside generated namespace")
                path.unlink()
    for relative, (_, text) in expected.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
    hookfile = root / ".codex/hooks.json"
    current = json.loads(hookfile.read_text(encoding="utf-8")) if hookfile.exists() else {}
    snippet = json.loads((root / "pack/adapters/hooks/codex.hooks.json").read_text(encoding="utf-8"))
    hookfile.write_text(json.dumps(merge_hooks(current, snippet), indent=2) + "\n", encoding="utf-8")
    print("Codex: " + str(len(expected)) + " generated files; hooks merged")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True)
    sync(parser.parse_args().root)
