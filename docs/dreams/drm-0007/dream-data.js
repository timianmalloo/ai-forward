window.DREAM_DATA = {
  "id": "drm-0007",
  "date": "2026-08-29",
  "generated": "2026-08-29T17:49:00Z",
  "window": "last 7 days · 29 audit · 16 change · 0 mitigations · 5 markers",
  "counts": {
    "audit": 29,
    "change": 16,
    "mitigations": 0,
    "classes": 18,
    "markers": 5
  },
  "proposals": [
    {
      "kind": "New defect class",
      "group": "REM-enriched cross-repo learning",
      "title": "Cross-agent collaboration contract is spoken, not recorded and claimed",
      "sig": "Two or more agent sessions work one repository, but session registration, file ownership, seam contracts, and derived/append-only merge policy are not recorded before work begins.",
      "scope": "general",
      "confidence": "v",
      "source": "REM-enriched from AI-DE collaboration evidence",
      "evidence": [
        {
          "eid": "ai-de:docs/collaboration/session-contracts.md#L1-L40",
          "note": "Two sessions split Core vs Design accountability; document exists because 'we'll coordinate' is not a coordination mechanism."
        },
        {
          "eid": "ai-de:docs/collaboration/session-contracts.md#L52-L85",
          "note": "File ownership is explicit: Core edits core/projection files; Design edits surfaces, XAML, chrome, mockups; shared paths are rule-bound."
        },
        {
          "eid": "ai-de:docs/collaboration/session-contracts.md#L100-L170",
          "note": "The contract names view-model seams, additive-change rules, small-landing/rebase guidance, no hand-merge for derived files, and session registration."
        },
        {
          "eid": "ai-de:docs/lessons/defect-classes.md#DC-013",
          "note": "Cross-agent recurrence: Core and Design each allocated the same audit id; the fix was union, re-issue one id, regenerate derived views."
        },
        {
          "eid": "ai-de:docs/lessons/defect-classes.md#DC-024",
          "note": "A cleanup removed a live but unregistered worktree; registration plus filesystem liveness became the control."
        },
        {
          "eid": "session-store:4d24d94a-eee0-4d48-a40a-79238103a474#turn3098",
          "note": "GH Copilot design session registered as copilot-design-4d24d94a, accepted the Core contract, claimed design files, and resolved derived/audit conflicts by the contract."
        }
      ],
      "control": {
        "rung": "automated control",
        "text": "Add a multi-session collaboration check: when more than one active worktree/session exists, fail or warn if any session is unregistered, if changed files lack a current coord claim or owner mapping, if no shared session contract exists, or if derived/append-only conflicts are hand-merged rather than regenerated/re-issued. Observe it failing on an unregistered two-session fixture and passing once both sessions register, claim files, and publish the seam contract.",
        "loc": "future pack control: coord collaboration check + docs/collaboration/session-contracts.template.md"
      },
      "boundary": "Applies to concurrent cross-agent repository writes. It does not apply to a single writing session, read-only exploration, or a normal human code review where one actor owns the worktree. It coordinates humans/agents by evidence; it is not a distributed lock unless the edited resource accepts fencing tokens.",
      "id": "p12",
      "score": 0.74
    },
    {
      "kind": "Control upgrade",
      "group": "Control upgrade",
      "title": "Build a control for PACK-N (uncontrolled)",
      "sig": "PACK-N · Staleness inferred from a timestamp rather than from content truth",
      "scope": "general",
      "confidence": "i",
      "source": "deterministic",
      "evidence": [
        {
          "eid": "defect-classes#PACK-N",
          "note": "status: uncontrolled"
        },
        {
          "eid": "al-0074",
          "note": "recent reference"
        }
      ],
      "control": {
        "rung": "automated control",
        "text": "Derive a falsifiable control for this class and observe it failing on the un-fixed shape (CI6); move status -> controlled.",
        "loc": "docs/lessons/defect-classes.md#PACK-N"
      },
      "boundary": "Applies wherever the class's signature recurs; a control is not a control until observed failing.",
      "id": "p4",
      "score": 0.69
    },
    {
      "kind": "Control upgrade",
      "group": "Control upgrade",
      "title": "Build a control for PACK-Q (partially-controlled)",
      "sig": "PACK-Q · An adapter written to a contract's *documented* shape, never to a *recorded* one",
      "scope": "general",
      "confidence": "i",
      "source": "deterministic",
      "evidence": [
        {
          "eid": "defect-classes#PACK-Q",
          "note": "status: partially-controlled"
        },
        {
          "eid": "al-01M0SXP5CTNHVMSB94DDFNR8NV",
          "note": "recent reference"
        },
        {
          "eid": "al-01M0SYZMNKF3N8MNGYDCVDJ0HE",
          "note": "recent reference"
        },
        {
          "eid": "cl-01M0SXPXKHE6M8CS75GBXRJM7B",
          "note": "recent reference"
        },
        {
          "eid": "cl-01M0SYZMSJVYYVXHA1NMF5WP0W",
          "note": "recent reference"
        }
      ],
      "control": {
        "rung": "automated control",
        "text": "Derive a falsifiable control for this class and observe it failing on the un-fixed shape (CI6); move status -> controlled.",
        "loc": "docs/lessons/defect-classes.md#PACK-Q"
      },
      "boundary": "Applies wherever the class's signature recurs; a control is not a control until observed failing.",
      "id": "p2",
      "score": 0.68
    },
    {
      "kind": "Control upgrade",
      "group": "Control upgrade",
      "title": "Build a control for PACK-C (partially-controlled)",
      "sig": "PACK-C · An assertion encodes a transient magnitude assumption",
      "scope": "general",
      "confidence": "i",
      "source": "deterministic",
      "evidence": [
        {
          "eid": "defect-classes#PACK-C",
          "note": "status: partially-controlled"
        },
        {
          "eid": "al-0072",
          "note": "recent reference"
        },
        {
          "eid": "al-01M0ZY4TJ1481EC9YXYAQTT6SF",
          "note": "recent reference"
        },
        {
          "eid": "al-01M0ZZG1AX98PF148STV0R7G44",
          "note": "recent reference"
        },
        {
          "eid": "al-01M105QJ0GTXKRMDET1F2X4QFD",
          "note": "recent reference"
        }
      ],
      "control": {
        "rung": "automated control",
        "text": "Derive a falsifiable control for this class and observe it failing on the un-fixed shape (CI6); move status -> controlled.",
        "loc": "docs/lessons/defect-classes.md#PACK-C"
      },
      "boundary": "Applies wherever the class's signature recurs; a control is not a control until observed failing.",
      "id": "p8",
      "score": 0.68
    },
    {
      "kind": "Control upgrade",
      "group": "Control upgrade",
      "title": "PACK-O: 13/28 substantive turns (46%) recorded no goal-state (done_when)",
      "sig": "PACK-O front-matter presence + scope-drift review",
      "scope": "general",
      "confidence": "v",
      "source": "deterministic",
      "evidence": [
        {
          "eid": "al-0072",
          "note": "forensicreview-ai-forward-rev42 - no done_when recorded (front matter skipped)"
        },
        {
          "eid": "al-0073",
          "note": "forensicreview-rev42-correction - no done_when recorded (front matter skipped)"
        },
        {
          "eid": "al-0074",
          "note": "backlog-clear-and-worktree-discipline - no done_when recorded (front matter skipped)"
        },
        {
          "eid": "al-0075",
          "note": "apply-two-step-front-matter - no done_when recorded (front matter skipped)"
        },
        {
          "eid": "al-0076",
          "note": "collectknowledge-agent-autopilot-controls - no done_when recorded (front matter skipped)"
        },
        {
          "eid": "al-0080",
          "note": "design-coord-federation-phase3 - no done_when recorded (front matter skipped)"
        },
        {
          "eid": "al-0081",
          "note": "implement-coord-phase3-derived-slice - no done_when recorded (front matter skipped)"
        },
        {
          "eid": "al-0082",
          "note": "implement-coord-phase3-allocator - no done_when recorded (front matter skipped)"
        },
        {
          "eid": "al-0077",
          "note": "done_when='audit-log records goal/done_when; /dream flags PACK-O presen' -> summary='Added --goal/--done-when + AL5b logging clause; dream PACK-O miner (build_propos'"
        },
        {
          "eid": "al-0079",
          "note": "done_when='graph clean (0 defects), portal groups+highlights the 5 new ' -> summary='Full graph sweep clean (0 defects/orphans/stale); added portal 'Discipline & opt'"
        },
        {
          "eid": "al-01M0XY4AS4MKJJCWX39VAXMMBD",
          "note": "done_when='docs/knowledge/native-client-ui-design exists, graph derivat' -> summary='Established native-client UI evidence base for WPF, WinUI, Avalonia, macOS, GNOM'"
        },
        {
          "eid": "al-01M0Y0TS4DED7ZM7Z8590HNF1X",
          "note": "done_when='docs/specs/native-app-ui-skill-extension.md exists, cites th' -> summary='Produced native app UI skill extension spec covering medium declaration, native '"
        }
      ],
      "control": {
        "rung": "automated control",
        "text": "Presence (mechanical): every substantive turn records done_when (CT19); a missing one skipped the front matter. Satisfaction: review each done_when->summary pair where the summary exceeds the goal (scope drift, PACK-O). The audit done_when field + this miner ARE the rung-2 control (CI6).",
        "loc": "docs/lessons/defect-classes.md#PACK-O"
      },
      "boundary": "Presence is mechanical; 'summary exceeds goal' is surfaced for human review, not auto-judged. Trivial/conversational turns are exempt from logging (AL5b).",
      "id": "p11",
      "score": 0.68
    },
    {
      "kind": "Doc update",
      "group": "Doc / knowledge update",
      "title": "Harvest 4 simplify: marker(s) - each is a bounded shortcut with an upgrade trigger",
      "sig": "simplify marker harvest",
      "scope": "repo-local",
      "confidence": "v",
      "source": "deterministic",
      "evidence": [
        {
          "eid": "pack/knowledge/solution-selection-ladder.md#L44",
          "note": "global lock, ok at current write volume — go per-account if throughput becomes the bottleneck"
        },
        {
          "eid": "pack/knowledge/solution-selection-ladder.md#L45",
          "note": "O(n²) match, fine for n<1k batches — index it when batch size grows"
        },
        {
          "eid": "pack/scripts/coord-core.py#L1306",
          "note": "occupancy is the newest session-start with no matching session-end,"
        },
        {
          "eid": "web/pack-index.js#L308",
          "note": "global lock, ok at current write volume — go per-account if throughput becomes the bottleneck # simplify: o(n²) match, fine for n<1k batches — index it when batch size grows ``` the token is **`simpli"
        }
      ],
      "control": {
        "rung": "knowledge doc",
        "text": "Review each simplify: marker against its upgrade trigger; a triggered one is debt due (L6).",
        "loc": "solution-selection-ladder.md L6 / no-guessing NG9"
      },
      "boundary": "Markers in this repo only; harvested at consolidation time.",
      "id": "p10",
      "score": 0.65
    },
    {
      "kind": "Control upgrade",
      "group": "Control upgrade",
      "title": "Build a control for PACK-P (partially-controlled)",
      "sig": "PACK-P · A check reports its verdict over a corpus it never established was non-empty",
      "scope": "general",
      "confidence": "i",
      "source": "deterministic",
      "evidence": [
        {
          "eid": "defect-classes#PACK-P",
          "note": "status: partially-controlled"
        },
        {
          "eid": "al-0081",
          "note": "recent reference"
        },
        {
          "eid": "al-0082",
          "note": "recent reference"
        }
      ],
      "control": {
        "rung": "automated control",
        "text": "Derive a falsifiable control for this class and observe it failing on the un-fixed shape (CI6); move status -> controlled.",
        "loc": "docs/lessons/defect-classes.md#PACK-P"
      },
      "boundary": "Applies wherever the class's signature recurs; a control is not a control until observed failing.",
      "id": "p3",
      "score": 0.56
    },
    {
      "kind": "Control upgrade",
      "group": "Control upgrade",
      "title": "Build a control for PACK-D (partially-controlled)",
      "sig": "PACK-D · An array parameter arrives as one comma-joined string when the script is invoked as an executable",
      "scope": "general",
      "confidence": "i",
      "source": "deterministic",
      "evidence": [
        {
          "eid": "defect-classes#PACK-D",
          "note": "status: partially-controlled"
        },
        {
          "eid": "al-0074",
          "note": "recent reference"
        },
        {
          "eid": "al-01M0R8XN8AGFRB2ZYZ2TQN7DN0",
          "note": "recent reference"
        }
      ],
      "control": {
        "rung": "automated control",
        "text": "Derive a falsifiable control for this class and observe it failing on the un-fixed shape (CI6); move status -> controlled.",
        "loc": "docs/lessons/defect-classes.md#PACK-D"
      },
      "boundary": "Applies wherever the class's signature recurs; a control is not a control until observed failing.",
      "id": "p7",
      "score": 0.56
    },
    {
      "kind": "Control upgrade",
      "group": "Control upgrade",
      "title": "Build a control for SHELL-A (partially-controlled)",
      "sig": "SHELL-A · Content routed through a shell construct that performs substitution on it",
      "scope": "general",
      "confidence": "i",
      "source": "deterministic",
      "evidence": [
        {
          "eid": "defect-classes#SHELL-A",
          "note": "status: partially-controlled"
        },
        {
          "eid": "cl-0026",
          "note": "recent reference"
        }
      ],
      "control": {
        "rung": "automated control",
        "text": "Derive a falsifiable control for this class and observe it failing on the un-fixed shape (CI6); move status -> controlled.",
        "loc": "docs/lessons/defect-classes.md#SHELL-A"
      },
      "boundary": "Applies wherever the class's signature recurs; a control is not a control until observed failing.",
      "id": "p1",
      "score": 0.45
    },
    {
      "kind": "Doc update",
      "group": "Doc / knowledge update",
      "title": "Harvest 1 assume: marker(s) - each is an unverified belief with a stated trigger",
      "sig": "assume marker harvest",
      "scope": "repo-local",
      "confidence": "v",
      "source": "deterministic",
      "evidence": [
        {
          "eid": "pack/knowledge/no-guessing-protocol.md#L53",
          "note": "the provider returns ISO-8601 in UTC. Seen in one sample payload, NOT stated in"
        }
      ],
      "control": {
        "rung": "knowledge doc",
        "text": "Review each assume: marker; a triggered one is a bug already written down (NG9). Verify or convert to a control.",
        "loc": "solution-selection-ladder.md L6 / no-guessing NG9"
      },
      "boundary": "Markers in this repo only; harvested at consolidation time.",
      "id": "p9",
      "score": 0.45
    },
    {
      "kind": "Control upgrade",
      "group": "Control upgrade",
      "title": "Build a control for PACK-H (partially-controlled)",
      "sig": "PACK-H · A fix to a hosted surface reported \"done\" from the working tree, not verified on the live surface",
      "scope": "general",
      "confidence": "i",
      "source": "deterministic",
      "evidence": [
        {
          "eid": "defect-classes#PACK-H",
          "note": "status: partially-controlled"
        }
      ],
      "control": {
        "rung": "automated control",
        "text": "Derive a falsifiable control for this class and observe it failing on the un-fixed shape (CI6); move status -> controlled.",
        "loc": "docs/lessons/defect-classes.md#PACK-H"
      },
      "boundary": "Applies wherever the class's signature recurs; a control is not a control until observed failing.",
      "id": "p5",
      "score": 0.34
    },
    {
      "kind": "Control upgrade",
      "group": "Control upgrade",
      "title": "Build a control for PACK-E (partially-controlled)",
      "sig": "PACK-E · An ambiguous proper noun resolved inside my own frame",
      "scope": "general",
      "confidence": "i",
      "source": "deterministic",
      "evidence": [
        {
          "eid": "defect-classes#PACK-E",
          "note": "status: partially-controlled"
        }
      ],
      "control": {
        "rung": "automated control",
        "text": "Derive a falsifiable control for this class and observe it failing on the un-fixed shape (CI6); move status -> controlled.",
        "loc": "docs/lessons/defect-classes.md#PACK-E"
      },
      "boundary": "Applies wherever the class's signature recurs; a control is not a control until observed failing.",
      "id": "p6",
      "score": 0.34
    }
  ],
  "diary": {
    "added": 1,
    "merged": 0,
    "superseded": 0,
    "excluded": 0
  }
};
