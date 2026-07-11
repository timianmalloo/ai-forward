"use strict";

const fs = require("node:fs");
const core = require("../../pack/scripts/docs-explorer-core.js");

const request = JSON.parse(fs.readFileSync(0, "utf8"));
const model = core.normalizeProjection({
  project: "Traversal parity",
  rootId: request.rootId,
  artifactTypes: [...new Set(request.artifacts.map((artifact) => artifact.type))],
  artifacts: request.artifacts,
});
const paths = core.policyPaths(
  model,
  request.rootId,
  request.rules,
  request.hops,
).map(({ from, to, rel, direction, depth }) => ({
  from,
  to,
  rel,
  direction,
  depth,
}));
process.stdout.write(JSON.stringify(paths));
