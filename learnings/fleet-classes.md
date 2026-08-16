# Fleet learnings (general, control-bearing classes)


### unknown-artifact-type-in-frontmatter
- **Signature:** unknown-artifact-type-in-frontmatter
- **Control:** docs-graph.py validate rejects any frontmatter 'type' not in the TYPES enum; run it after adding a graph node. (automated control)
- **Boundary:** Applies to any new .md graph node; type must be one of the known TYPES.
- **Confidence:** v
- **From:** drm-0002 / p1
