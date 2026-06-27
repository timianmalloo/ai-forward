// Derived from docs/audit/*.jsonl by scripts/audit-log.py — DO NOT hand-edit (the JSONL logs are the source of truth; see audit-and-change-log.md).
window.AUDIT_DATA = {
  "project": "AI-Forward",
  "generated": "2026-06-27T14:47:39Z",
  "audit": [
    {
      "id": "al-0001",
      "shortname": "extend-audit-changelog",
      "datetime": "2026-06-27T14:47:38Z",
      "session": "2dbe541d-87e5-4245-aa92-235c598de500",
      "prompt": "Extend the project directives, skills and documentation: (1) create an append-only audit log (shortname, datetime, session, prompt, summary + enriched fields) that every skill writes to, integrated into the knowledge graph and built on session history; (2) an interactive HTML viewer + CLI skill over it (search by session/datetime/keyword, timeline default, expandable, copy-prompt; CLI: last N, redo, search); (3) a change log capturing meaningful design decisions (collectknowledge/define-architecture/design/migrate capture prompt+summary; capture git commits/pushes before+after); (4) extend the viewer to toggle full history vs meaningful changes.",
      "summary": "Built the Audit & Change Log system for the pack: audit-log.py (append/change/list/search/get/render/git-context/suggest/import), the audit-explorer viewer (searchable timeline, copy-prompt, full-history/changes toggle), the audit-and-change-log.md standard, the /auditlog CLI skill + prompt + eval, the docs/audit graph hub node; integrated the Audit Mandate into all 13 skills and the Change Mandate into the 4 design-shaping skills; reconciled all counts (skills 13->14, knowledge 22->23, templates 16->17, scripts 4->5).",
      "kind": "skill",
      "skill": "extendaibundle",
      "tool": "Copilot CLI",
      "actor": null,
      "artifacts": [
        "pack/scripts/audit-log.py",
        "pack/templates/audit-explorer.template.html",
        "pack/knowledge/audit-and-change-log.md",
        "pack/commands/auditlog/SKILL.md"
      ],
      "tags": [
        "audit",
        "change-log",
        "viewer",
        "cli"
      ],
      "outcome": "success",
      "git": {
        "sha": "51fc0b7b83eab5a6469a950c9a95638443ed0b2e",
        "short": "51fc0b7b8",
        "branch": "main",
        "pushed": true
      }
    }
  ],
  "changes": [
    {
      "id": "cl-0001",
      "datetime": "2026-06-27T14:47:39Z",
      "session": "2dbe541d-87e5-4245-aa92-235c598de500",
      "kind": "decision",
      "skill": "extendaibundle",
      "title": "Add the Audit & Change Log system to the pack",
      "prompt": "Extend the project directives, skills and documentation: (1) create an append-only audit log (shortname, datetime, session, prompt, summary + enriched fields) that every skill writes to, integrated into the knowledge graph and built on session history; (2) an interactive HTML viewer + CLI skill over it (search by session/datetime/keyword, timeline default, expandable, copy-prompt; CLI: last N, redo, search); (3) a change log capturing meaningful design decisions (collectknowledge/define-architecture/design/migrate capture prompt+summary; capture git commits/pushes before+after); (4) extend the viewer to toggle full history vs meaningful changes.",
      "summary": "A durable, committed audit log (every meaningful prompt/skill/script) + curated change log (design decisions, with git before/after), a self-contained searchable timeline viewer (full-history/changes toggle) + the /auditlog CLI, integrated into all 13 skills (Audit Mandate) and the 4 design-shaping skills (Change Mandate) and registered in the knowledge graph (docs/audit/audit-log.md).",
      "rationale": "A session's reasoning is the most valuable thing it produces and the first thing lost when the session ends; a committed history makes work compound across sessions instead of evaporating.",
      "artifacts": [
        "pack/knowledge/audit-and-change-log.md",
        "pack/scripts/audit-log.py",
        "docs/audit/audit-log.md"
      ],
      "tags": [
        "pack-capability"
      ],
      "git": {
        "before": "51fc0b7b83eab5a6469a950c9a95638443ed0b2e",
        "after": "51fc0b7b83eab5a6469a950c9a95638443ed0b2e",
        "branch": "main",
        "pushed": true,
        "commits": []
      }
    }
  ]
};
