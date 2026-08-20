# Fleet learnings (general, control-bearing classes)


### unknown-artifact-type-in-frontmatter
- **Signature:** unknown-artifact-type-in-frontmatter
- **Control:** docs-graph.py validate rejects any frontmatter 'type' not in the TYPES enum; run it after adding a graph node. (automated control)
- **Boundary:** Applies to any new .md graph node; type must be one of the known TYPES.
- **Confidence:** v
- **From:** drm-0002 / p1

### PACK-E · An ambiguous proper noun resolved inside my own frame
- **Signature:** PACK-E · An ambiguous proper noun resolved inside my own frame
- **Control:** Derive a falsifiable control for this class and observe it failing on the un-fixed shape (CI6); move status -> controlled. (automated control)
- **Boundary:** Applies wherever the class's signature recurs; a control is not a control until observed failing.
- **Confidence:** i
- **From:** drm-0003 / p3

### PACK-D · An array parameter arrives as one comma-joined string when the script is invoked as an exec
- **Signature:** PACK-D · An array parameter arrives as one comma-joined string when the script is invoked as an executable
- **Control:** Derive a falsifiable control for this class and observe it failing on the un-fixed shape (CI6); move status -> controlled. (automated control)
- **Boundary:** Applies wherever the class's signature recurs; a control is not a control until observed failing.
- **Confidence:** i
- **From:** drm-0003 / p4

### PACK-C · An assertion encodes a transient magnitude assumption
- **Signature:** PACK-C · An assertion encodes a transient magnitude assumption
- **Control:** Derive a falsifiable control for this class and observe it failing on the un-fixed shape (CI6); move status -> controlled. (automated control)
- **Boundary:** Applies wherever the class's signature recurs; a control is not a control until observed failing.
- **Confidence:** i
- **From:** drm-0003 / p5

### PACK-H · A fix to a hosted surface reported "done" from the working tree, not verified on the live s
- **Signature:** PACK-H · A fix to a hosted surface reported "done" from the working tree, not verified on the live surface
- **Control:** Derive a falsifiable control for this class and observe it failing on the un-fixed shape (CI6); move status -> controlled. (automated control)
- **Boundary:** Applies wherever the class's signature recurs; a control is not a control until observed failing.
- **Confidence:** i
- **From:** drm-0003 / p2
