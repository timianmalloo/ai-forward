#!/usr/bin/env python3
"""run-evals.py — golden-task assertion runner for the AI-Forward Pack (pack maintenance).

A skill is prompt-code; this is its regression suite. Each case is a JSON file:
  { "id": "...", "skill": "design", "prompt": "<the golden task to give the agent>",
    "setup": [{"path": "...", "content": "..."}],          // optional workspace seed
    "assertions": [ ... ] }                                 // objective post-conditions

Assertion types (all run against --workspace):
  {"type":"file-exists","path":"docs/design/x.md"}
  {"type":"file-absent","path":"src/tmp.cs"}
  {"type":"grep","path":"...","pattern":"<regex>"}          // must match
  {"type":"not-grep","path":"...","pattern":"<regex>"}      // must not match
  {"type":"frontmatter-valid","path":"..."}                 // via scripts/docs-graph.py parser
  {"type":"index-has","id":"design-x"}                      // docs/docs-index.js contains entry
  {"type":"cmd-exit","cmd":["python3","docs/ai-forward-pack/scripts/docs-graph.py","validate"],"exit":0}

Flow per case: (1) `--setup` seeds the workspace; (2) YOU run the skill against it (paste
case["prompt"] into Claude Code / Copilot, or wire --exec to a headless CLI); (3) `--check`
evaluates assertions. CI runs --check over recorded workspaces. Exit 0 = all pass.
"""
import argparse, importlib.util, json, os, re, subprocess, sys

def load_graph_module(workspace):
    for cand in [os.path.join(workspace,"docs","ai-forward-pack","scripts","docs-graph.py"),
                 os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),"scripts","docs-graph.py")]:
        if os.path.exists(cand):
            spec=importlib.util.spec_from_file_location("dg",cand); m=importlib.util.module_from_spec(spec)
            spec.loader.exec_module(m); return m
    return None

def check(case, ws):
    fails=[]
    dg=load_graph_module(ws)
    for a in case.get("assertions",[]):
        t=a["type"]; p=os.path.join(ws,a.get("path","")) if a.get("path") else None
        try:
            if t=="file-exists" and not os.path.exists(p): fails.append(f"file-exists: {a['path']}")
            elif t=="file-absent" and os.path.exists(p): fails.append(f"file-absent: {a['path']}")
            elif t=="grep":
                if not os.path.exists(p) or not re.search(a["pattern"], open(p,encoding="utf-8").read(), re.S):
                    fails.append(f"grep '{a['pattern']}' in {a['path']}")
            elif t=="not-grep":
                if os.path.exists(p) and re.search(a["pattern"], open(p,encoding="utf-8").read(), re.S):
                    fails.append(f"not-grep '{a['pattern']}' in {a['path']}")
            elif t=="frontmatter-valid":
                if not dg: fails.append("frontmatter-valid: docs-graph.py not found"); continue
                fm,err=dg.parse_frontmatter(open(p,encoding="utf-8").read())
                if err: fails.append(f"frontmatter-valid {a['path']}: {err}")
            elif t=="index-has":
                ip=os.path.join(ws,"docs","docs-index.js")
                m=re.search(r"window\.DOCS_INDEX\s*=\s*(\{.*\});?\s*$", open(ip,encoding="utf-8").read(), re.S) if os.path.exists(ip) else None
                ids=[e.get("id") for e in (json.loads(m.group(1))["artifacts"] if m else [])]
                if a["id"] not in ids: fails.append(f"index-has: {a['id']}")
            elif t=="cmd-exit":
                r=subprocess.run(a["cmd"], cwd=ws, capture_output=True)
                if r.returncode!=a.get("exit",0): fails.append(f"cmd-exit {a['cmd']}: got {r.returncode}, want {a.get('exit',0)}")
        except Exception as e: fails.append(f"{t}: error {e}")
    return fails

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--cases", default=os.path.join(os.path.dirname(os.path.abspath(__file__)),"cases"))
    ap.add_argument("--case", default=None, help="single case file")
    ap.add_argument("--workspace", required=True)
    ap.add_argument("--setup", action="store_true", help="seed workspace from case setup, then exit")
    ap.add_argument("--check", action="store_true", help="evaluate assertions")
    args=ap.parse_args()
    files=[args.case] if args.case else sorted(
        os.path.join(args.cases,f) for f in os.listdir(args.cases) if f.endswith(".json"))
    total_fail=0
    for cf in files:
        case=json.load(open(cf,encoding="utf-8"))
        if args.setup:
            for s in case.get("setup",[]):
                p=os.path.join(args.workspace,s["path"]); os.makedirs(os.path.dirname(p),exist_ok=True)
                open(p,"w",encoding="utf-8").write(s["content"])
            print(f"setup: {case['id']} -> {args.workspace}")
            print(f"PROMPT for the agent:\n{case['prompt']}\n")
        if args.check:
            fails=check(case,args.workspace)
            print(f"{'PASS' if not fails else 'FAIL'}  {case['id']}" + ("" if not fails else "\n  - "+"\n  - ".join(fails)))
            total_fail+=len(fails)
    return 1 if total_fail else 0

if __name__=="__main__": sys.exit(main())
