"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const crypto = require("node:crypto");
const fs = require("node:fs");
const path = require("node:path");
const core = require("../../pack/scripts/docs-explorer-core.js");

const index = {
  project: "Fixture",
  rootId: "root",
  artifactTypes: ["architecture", "design"],
  artifacts: [
    {
      id: "root",
      title: "Root",
      type: "architecture",
      status: "accepted",
      links: [{ to: "child", rel: "depends-on" }],
    },
    {
      id: "child",
      title: "Child",
      type: "design",
      status: "accepted",
      links: [{ to: "root", rel: "tested-by" }],
    },
  ],
};

test("initialState defaults to Browse with separate selection and context", () => {
  const state = core.initialState(index);
  assert.equal(state.projection, "browse");
  assert.equal(state.selectedNodeId, null);
  assert.equal(state.contextNodeId, null);
});

test("runWithDeadline returns a completed operation and leaves its signal active", async () => {
  let observedSignal;
  const result = await core.runWithDeadline(async (signal) => {
    observedSignal = signal;
    return "complete";
  }, 50);

  assert.equal(result, "complete");
  assert.equal(observedSignal.aborted, false);
});

test("runWithDeadline aborts and rejects an operation that exceeds its deadline", async () => {
  let observedSignal;
  await assert.rejects(
    core.runWithDeadline(
      (signal) => {
        observedSignal = signal;
        return new Promise(() => {});
      },
      5,
    ),
    { name: "TimeoutError", message: "operation deadline exceeded" },
  );
  assert.equal(observedSignal.aborted, true);
  assert.equal(observedSignal.reason.name, "TimeoutError");
});

test("runWithDeadline rejects invalid timeout values before invoking the operation", async () => {
  let invoked = false;
  await assert.rejects(
    core.runWithDeadline(() => {
      invoked = true;
    }, Number.NaN),
    { name: "RangeError" },
  );
  assert.equal(invoked, false);
});

test("SELECT_NODE never changes context or mind-map root", () => {
  const start = { ...core.initialState(index), contextNodeId: "root" };
  const next = core.reduceState(start, { type: "SELECT_NODE", id: "child" }, index);
  assert.equal(next.selectedNodeId, "child");
  assert.equal(next.contextNodeId, "root");
  assert.equal(core.mindMapRoot(next, index), "root");
});

test("SET_PATH_MODE toggles the trace and routes narrow layouts to Graph", () => {
  const start = { ...core.initialState(index), selectedNodeId: "root" };

  const enabled = core.reduceState(
    start,
    { type: "SET_PATH_MODE", value: "grounding" },
    index,
    { narrow: true },
  );
  assert.equal(enabled.pathMode, "grounding");
  assert.equal(enabled.projection, "graph");
  assert.equal(enabled.route, "visualization");

  const disabled = core.reduceState(
    enabled,
    { type: "SET_PATH_MODE", value: "grounding" },
    index,
    { narrow: true },
  );
  assert.equal(disabled.pathMode, "none");
});

test("RESTORE_STATE normalizes invalid and filtered navigation targets", () => {
  const restored = core.reduceState(
    core.initialState(index),
    {
      type: "RESTORE_STATE",
      state: {
        ...core.initialState(index),
        projection: "mindmap",
        route: "visualization",
        selectedNodeId: "missing",
        contextNodeId: "child",
        filters: { types: ["architecture"], statuses: [], health: [], relations: [] },
      },
    },
    index,
    { narrow: true },
  );

  assert.equal(restored.projection, "browse");
  assert.equal(restored.route, "browse");
  assert.equal(restored.selectedNodeId, null);
  assert.equal(restored.contextNodeId, null);
  assert.match(restored.notice, /filters exclude|no longer available/);
});

test("EXPLORE_CONTEXT rejects artifacts excluded by active filters", () => {
  const start = {
    ...core.initialState(index),
    filters: { types: ["architecture"], statuses: [], health: [], relations: [] },
  };
  const next = core.reduceState(start, { type: "EXPLORE_CONTEXT", id: "child" }, index);

  assert.equal(next.contextNodeId, null);
  assert.match(next.notice, /current filters/);
});

test("unknown events and unsupported path modes cannot mutate state", () => {
  const start = core.initialState(index);
  assert.equal(core.reduceState(start, { type: "UNKNOWN" }, index), start);
  const invalidPath = core.reduceState(
    start,
    { type: "SET_PATH_MODE", value: "invalid" },
    index,
  );
  assert.equal(invalidPath.pathMode, "none");
  assert.match(invalidPath.notice, /unavailable/);
});

test("normalizeState clears stale notices while reducer normalization preserves new notices", () => {
  const stale = core.normalizeState(
    { ...core.initialState(index), notice: "Old notice" },
    index,
    false,
  );
  assert.equal(stale.notice, "");

  const next = core.reduceState(
    {
      ...core.initialState(index),
      contextNodeId: "child",
    },
    {
      type: "APPLY_FILTERS",
      filters: { types: ["architecture"], statuses: [], health: [], relations: [] },
    },
    index,
  );
  assert.match(next.notice, /context was cleared/);
});

test("URL state round-trips sorted explicit fields", () => {
  const state = {
    ...core.initialState(index),
    projection: "graph",
    route: "visualization",
    selectedNodeId: "child",
    contextNodeId: "root",
    pathMode: "impact",
    filters: {
      types: ["design", "architecture"],
      statuses: ["accepted"],
      health: [],
      relations: ["tested-by", "depends-on"],
    },
  };
  const encoded = core.encodeUrlState(state);
  const decoded = core.decodeUrlState(new URLSearchParams(encoded), index);
  assert.equal(decoded.projection, "graph");
  assert.equal(decoded.selectedNodeId, "child");
  assert.equal(decoded.contextNodeId, "root");
  assert.deepEqual(decoded.filters.types, ["architecture", "design"]);
  assert.deepEqual(decoded.filters.relations, ["depends-on", "tested-by"]);
});

test("Spatial 3D is a URL-addressable projection with semantic state only", () => {
  const state = {
    ...core.initialState(index),
    projection: "spatial3d",
    route: "visualization",
    selectedNodeId: "child",
    contextNodeId: "root",
  };

  const encoded = core.encodeUrlState(state);
  const decoded = core.decodeUrlState(new URLSearchParams(encoded), index);

  assert.match(encoded, /view=spatial3d/);
  assert.equal(decoded.projection, "spatial3d");
  assert.equal(decoded.selectedNodeId, "child");
  assert.equal(decoded.contextNodeId, "root");
  assert.equal(encoded.includes("yaw"), false);
  assert.equal(encoded.includes("zoom"), false);
});

test("normalized projection uses deterministic node and edge order", () => {
  const model = core.normalizeProjection(index);
  assert.deepEqual(model.nodes.map((node) => node.id), ["root", "child"]);
  assert.deepEqual(
    model.edges.map((edge) => edge.id),
    ["child|tested-by|root", "root|depends-on|child"],
  );
  assert.throws(
    () =>
      core.normalizeProjection({
        ...index,
        artifacts: [
          {
            ...index.artifacts[0],
            links: [
              { to: "child", rel: "depends-on" },
              { to: "child", rel: "depends-on" },
            ],
          },
          index.artifacts[1],
        ],
      }),
    /duplicate typed link/,
  );
});

test("search highlights without changing topology", () => {
  const model = core.normalizeProjection(index);
  const matches = core.searchMatches(model.nodes, "child");
  assert.deepEqual(matches, ["child"]);
  assert.equal(model.nodes.length, 2);
  assert.equal(model.edges.length, 2);
});

test("canonical JSON and SHA-256 match independent fixtures", () => {
  const fixture = JSON.parse(
    fs.readFileSync(path.join(__dirname, "canonical-hash-v1.json"), "utf8"),
  );
  for (const vector of fixture.vectors) {
    const canonical = core.canonicalJson(vector.value);
    assert.equal(canonical, vector.canonical, vector.name);
    assert.equal(
      crypto.createHash("sha256").update(canonical, "utf8").digest("hex"),
      vector.sha256,
      vector.name,
    );
  }
});

test("policy traversal honors direction, priority, and deterministic tie-breaking", () => {
  const model = {
    nodes: ["root", "a", "b", "proof"].map((id) => ({ id })),
    edges: [
      { id: "a|implements|root", source: "a", rel: "implements", target: "root" },
      { id: "root|depends-on|b", source: "root", rel: "depends-on", target: "b" },
      { id: "root|tested-by|proof", source: "root", rel: "tested-by", target: "proof" },
    ],
  };
  const grounding = [
    { rel: "depends-on", direction: "outbound", priority: 0 },
    { rel: "tested-by", direction: "outbound", priority: 1 },
  ];
  const impact = [{ rel: "implements", direction: "inbound", priority: 0 }];

  assert.deepEqual(
    core.policyPaths(model, "root", grounding, 1).map((item) => item.to),
    ["b", "proof"],
  );
  assert.deepEqual(
    core.policyPaths(model, "root", impact, 1).map((item) => item.to),
    ["a"],
  );
});

test("all traversal policies match the shared cross-runtime fixture", () => {
  const fixture = JSON.parse(
    fs.readFileSync(path.join(__dirname, "traversal-policy-v1.json"), "utf8"),
  );
  const model = core.normalizeProjection({
    project: "Traversal fixture",
    rootId: fixture.rootId,
    artifactTypes: [...new Set(fixture.artifacts.map((artifact) => artifact.type))],
    artifacts: fixture.artifacts,
  });
  const expectedAtOneHop = {
    grounding: [
      ["root", "spec", "implements", "outbound", 1],
      ["root", "adr", "depends-on", "outbound", 1],
      ["root", "glossary", "uses-term", "outbound", 1],
      ["root", "proof", "tested-by", "outbound", 1],
    ],
    impact: [
      ["root", "component", "implements", "inbound", 1],
      ["root", "adr", "depends-on", "inbound", 1],
      ["root", "architecture", "depends-on", "inbound", 1],
    ],
    proof: [["root", "proof", "tested-by", "outbound", 1]],
    "explore-neighborhood": [
      ["root", "adr", "depends-on", "outbound", 1],
      ["root", "architecture", "depends-on", "inbound", 1],
      ["root", "document", "documents", "inbound", 1],
      ["root", "component", "implements", "inbound", 1],
      ["root", "spec", "implements", "outbound", 1],
      ["root", "proof", "tested-by", "outbound", 1],
      ["root", "glossary", "uses-term", "outbound", 1],
    ],
  };

  for (const [policy, rules] of Object.entries(fixture.policies)) {
    assert.deepEqual(core.policyPaths(model, fixture.rootId, rules, 0), [], `${policy}:0`);
    const oneHop = core.policyPaths(model, fixture.rootId, rules, 1)
      .map(({ from, to, rel, direction, depth }) => [from, to, rel, direction, depth]);
    assert.deepEqual(oneHop, expectedAtOneHop[policy], `${policy}:1`);
    const twoHop = core.policyPaths(model, fixture.rootId, rules, 2);
    assert.equal(twoHop.every((path) => path.depth >= 1 && path.depth <= 2), true, `${policy}:2`);
    assert.equal(new Set(twoHop.map((path) => path.to)).size, twoHop.length, `${policy}:cycles`);
    assert.equal(twoHop.some((path) => path.to === "missing"), false, `${policy}:missing`);
  }
});

test("radial layout is an honest policy-bounded BFS tree with ghost cross-links", () => {
  const model = {
    nodes: ["root", "a", "b", "outside"].map((id) => ({ id })),
    edges: [
      { id: "root|depends-on|a", source: "root", rel: "depends-on", target: "a" },
      { id: "root|depends-on|b", source: "root", rel: "depends-on", target: "b" },
      { id: "a|depends-on|b", source: "a", rel: "depends-on", target: "b" },
      { id: "root|tested-by|outside", source: "root", rel: "tested-by", target: "outside" },
    ],
  };
  const rules = [
    { rel: "depends-on", direction: "outbound", priority: 0 },
    { rel: "depends-on", direction: "inbound", priority: 0 },
  ];

  const layout = core.radialLayout(model, "root", 1000, 700, rules);

  assert.deepEqual(layout.nodes.map((node) => node.id).sort(), ["a", "b", "root"]);
  assert.deepEqual([...layout.ghostEdgeIds], ["a|depends-on|b"]);
  assert.equal(layout.edges.some((edge) => edge.target === "outside"), false);
});

test("layout dimensions are shared, deterministic, and bounded", () => {
  assert.deepEqual(core.layoutDimensions(0), { width: 1000, height: 700 });
  assert.deepEqual(core.layoutDimensions(10), { width: 1000, height: 700 });
  assert.deepEqual(core.layoutDimensions(500), { width: 12000, height: 12000 });
  assert.deepEqual(core.layoutDimensions(500), core.layoutDimensions(500));
});

test("500-node and 1000-edge layout stays structurally bounded", () => {
  const nodes = Array.from({ length: 500 }, (_, ordinal) => ({
    id: `node-${String(ordinal).padStart(3, "0")}`,
    lane: `lane-${ordinal % 10}`,
    laneRank: ordinal % 10,
  }));
  const edges = Array.from({ length: 1000 }, (_, ordinal) => ({
    id: `edge-${ordinal}`,
    source: nodes[ordinal % nodes.length].id,
    rel: "relates-to",
    target: nodes[(ordinal * 17 + 1) % nodes.length].id,
  }));
  const dimensions = core.layoutDimensions(nodes.length);
  const layout = core.deterministicLayout({ nodes, edges }, dimensions.width, dimensions.height);

  assert.equal(layout.nodes.length, 500);
  assert.equal(layout.edges.length, 1000);
  assert.deepEqual(layout.work, { nodeVisits: 1000, edgeVisits: 1000 });
});

test("Spatial 3D world coordinates are deterministic under shuffled input", () => {
  const nodes = [
    { id: "zeta", lane: "design", laneRank: 1 },
    { id: "root", lane: "architecture", laneRank: 0 },
    { id: "alpha", lane: "design", laneRank: 1 },
  ];
  const edges = [
    { id: "root|depends-on|alpha", source: "root", rel: "depends-on", target: "alpha" },
    { id: "zeta|tested-by|root", source: "zeta", rel: "tested-by", target: "root" },
  ];

  const first = core.deterministic3DLayout({ nodes, edges });
  const second = core.deterministic3DLayout({
    nodes: [nodes[2], nodes[0], nodes[1]],
    edges: [edges[1], edges[0]],
  });
  const coordinates = (layout) => Object.fromEntries(
    layout.nodes.map(({ id, x, y, z }) => [id, { x, y, z }]),
  );

  assert.deepEqual(coordinates(first), coordinates(second));
  assert.deepEqual(first.edges.map((edge) => edge.id), second.edges.map((edge) => edge.id));
  assert.deepEqual(first.center, second.center);
});

test("Spatial camera targets selection before context and graph centroid", () => {
  const layout = core.deterministic3DLayout({
    nodes: [
      { id: "root", lane: "architecture", laneRank: 0 },
      { id: "child", lane: "design", laneRank: 1 },
    ],
    edges: [],
  });

  const selected = core.canonicalSpatialCamera(layout, "child", "root");
  const context = core.canonicalSpatialCamera(layout, null, "root");
  const centroid = core.canonicalSpatialCamera(layout, null, null);

  assert.deepEqual(selected.target, layout.nodes.find((node) => node.id === "child"));
  assert.deepEqual(context.target, layout.nodes.find((node) => node.id === "root"));
  assert.deepEqual(centroid.target, layout.center);
});

test("Spatial camera transforms presentation without changing graph semantics", () => {
  const layout = core.deterministic3DLayout({
    nodes: [
      { id: "root", lane: "architecture", laneRank: 0 },
      { id: "child", lane: "design", laneRank: 1 },
    ],
    edges: [
      { id: "root|depends-on|child", source: "root", rel: "depends-on", target: "child" },
    ],
  });
  const camera = core.canonicalSpatialCamera(layout, "root", null);
  const first = core.projectSpatialLayout(layout, camera, 1000, 700);
  const second = core.projectSpatialLayout(
    layout,
    { ...camera, yaw: camera.yaw + 0.5, zoom: 1.25 },
    1000,
    700,
  );

  assert.deepEqual(first.edges.map((edge) => edge.id), ["root|depends-on|child"]);
  assert.deepEqual(second.edges.map((edge) => edge.id), ["root|depends-on|child"]);
  assert.deepEqual(
    first.nodes.map((node) => node.id).sort(),
    second.nodes.map((node) => node.id).sort(),
  );
  assert.notDeepEqual(
    first.nodes.map(({ id, screenX, screenY }) => ({ id, screenX, screenY })),
    second.nodes.map(({ id, screenX, screenY }) => ({ id, screenX, screenY })),
  );
});
