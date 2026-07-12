"use strict";

const crypto = require("node:crypto");
const path = require("node:path");
const { pathToFileURL } = require("node:url");
const { test, expect } = require("@playwright/test");

function sourceHash(text) {
  return crypto.createHash("sha256")
    .update(String(text).replace(/\r\n/g, "\n").replace(/\r/g, "\n"), "utf8")
    .digest("hex");
}

function withRootSource(index, text) {
  const copy = structuredClone(index);
  copy.artifacts.find((artifact) => artifact.id === "root").sourceSha256 = sourceHash(text);
  return copy;
}

test("generated Explorer opens directly from file URLs", async ({ page }) => {
  const explorerUrl = pathToFileURL(path.join(process.cwd(), "docs", "index.html")).href;

  await page.goto(explorerUrl);

  await expect(page.locator("#app")).toHaveAttribute("data-state", "ready");
  await expect(page.getByRole("heading", { name: /Docs Explorer/ })).toBeVisible();
});

test("loading shell exposes stable navigation and Browse skeleton rows", async ({ page }) => {
  await page.route("**/docs-index.js", async (route) => {
    await new Promise((resolve) => setTimeout(resolve, 500));
    await route.fulfill({
      contentType: "application/javascript",
      body: `window.DOCS_INDEX = ${JSON.stringify(fixtureIndex())};`,
    });
  });

  await page.goto("/docs/index.html", { waitUntil: "commit" });

  await expect(page.locator("#app")).toHaveAttribute("data-state", "loading");
  await expect(page.getByRole("tablist", { name: "Explorer projection" })).toBeVisible();
  await expect(page.getByRole("tab", { name: "Index" })).toHaveAttribute(
    "aria-selected",
    "true",
  );
  await expect(page.getByRole("heading", { name: "Knowledge index" })).toBeVisible();
  await expect(page.locator("[data-skeleton-row]")).toHaveCount(4);
});

test("ready state is published only after the initial Browse control is rendered", async ({
  page,
}) => {
  await page.addInitScript(() => {
    const observeApp = () => {
      const app = document.getElementById("app");
      if (!app) {
        requestAnimationFrame(observeApp);
        return;
      }
      new MutationObserver(() => {
        if (app.dataset.state === "ready") {
          window.__docsExplorerReadyHadBrowse = Boolean(
            document.querySelector('[role="tab"][aria-selected="true"]'),
          );
        }
      }).observe(app, { attributes: true, attributeFilter: ["data-state"] });
    };
    observeApp();
  });
  await serveIndex(page, fixtureIndex());

  await page.goto("/docs/index.html");

  await expect(page.locator("#app")).toHaveAttribute("data-state", "ready");
  expect(await page.evaluate(() => window.__docsExplorerReadyHadBrowse)).toBe(true);
});

function fixtureIndex(overrides = {}) {
  return {
    schemaVersion: "docs-index/v2",
    project: "Fixture",
    rootId: "root",
    artifactTypes: ["architecture", "design"],
    relationRegistry: { "depends-on": "dependency" },
    traversalPolicies: {
      "explore-neighborhood": [
        { rel: "depends-on", direction: "outbound", priority: 0 },
        { rel: "depends-on", direction: "inbound", priority: 0 },
      ],
      grounding: [{ rel: "depends-on", direction: "outbound", priority: 0 }],
      impact: [{ rel: "depends-on", direction: "inbound", priority: 0 }],
      proof: [],
    },
    limits: {
      indexBytes: 5 * 1024 * 1024,
      artifacts: 1000,
      relationships: 5000,
      spatialNodes: 500,
      spatialEdges: 1000,
      visibleLabels: 150,
      surfaces: 100,
    },
    surfaces: [
      {
        id: "surface-audit",
        path: "docs/audit/index.html",
        title: "Audit and change timeline",
        kind: "audit",
        description: "Browse the committed project history.",
      },
      {
        id: "surface-docs",
        path: "docs/_site/index.html",
        title: "Documentation bundle",
        kind: "documentation",
        description: "Read the generated documentation bundle.",
      },
      {
        id: "surface-design",
        path: "docs/design/preview.html",
        title: "Design preview",
        kind: "design-preview",
        description: "Inspect the product design language.",
        artifactId: "child",
      },
    ],
    artifacts: [
      {
        id: "root",
        path: "docs/root.md",
        title: "Root",
        type: "architecture",
        status: "accepted",
        links: [{ to: "child", rel: "depends-on" }],
      },
      {
        id: "child",
        path: "docs/child.md",
        title: "Child",
        type: "design",
        status: "accepted",
        links: [],
      },
    ],
    ...overrides,
  };
}

async function serveIndex(page, index) {
  await page.route("**/docs-index.js", async (route) => {
    await route.fulfill({
      contentType: "text/javascript",
      body: `window.DOCS_INDEX = ${JSON.stringify(index)};`,
    });
  });
}

async function serveAuditData(page) {
  await page.route("**/audit-data.js", async (route) => {
    await route.fulfill({
      contentType: "text/javascript",
      body: `window.AUDIT_DATA = ${JSON.stringify({
        project: "Fixture",
        generated: "2026-07-11T00:00:00Z",
        audit: [
          {
            id: "al-0001",
            shortname: "explorer-review",
            datetime: "2026-07-11T10:30:00Z",
            session: "session-a",
            prompt: "Review the Docs Explorer.",
            summary: "Reviewed the Explorer.",
            kind: "skill",
            skill: "forensicreview",
            outcome: "success",
            artifacts: ["docs/design/docs-explorer-grounding-and-spatial-navigation.md"],
            tags: ["explorer"],
          },
        ],
        changes: [
          {
            id: "cl-0001",
            title: "Use deterministic layouts",
            datetime: "2026-07-11T10:35:00Z",
            session: "session-a",
            prompt: "Make graph layouts deterministic.",
            summary: "Adopted deterministic graph layouts.",
            rationale: "Stable projections improve grounding and review.",
            kind: "design",
            artifacts: ["docs/design/docs-explorer-grounding-and-spatial-navigation.md"],
          },
        ],
      })};`,
    });
  });
}

test("Audit Explorer executes disclosure, filtering, copy feedback, and view switching", async ({
  page,
}) => {
  await serveAuditData(page);
  await page.goto("/docs/audit/index.html");

  await expect(page.getByRole("heading", { name: "Fixture — Audit Log" })).toBeVisible();
  const disclosure = page.getByRole("button", { name: "Review entry explorer-review" });
  await disclosure.focus();
  await disclosure.press("Enter");
  await expect(disclosure).toHaveAttribute("aria-expanded", "true");
  await expect(page.getByRole("region", { name: "explorer-review details" })).toBeVisible();

  await page.getByRole("button", { name: "copy prompt" }).click();
  await expect(page.locator('.sr-only[role="status"]')).toHaveText("Prompt copied");

  await page.getByRole("searchbox", { name: "Search audit history" }).fill("not-present");
  await expect(page.getByText("No actions match the filters.")).toBeVisible();
  await page.getByRole("button", { name: "Clear filters" }).click();

  await page.getByRole("button", { name: "Changes" }).click();
  await expect(page.getByRole("heading", { name: "Fixture — Change Log" })).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Review entry Use deterministic layouts" }),
  ).toBeVisible();
});

test("Audit Explorer exposes an alert when its data file cannot load", async ({ page }) => {
  await page.route("**/audit-data.js", (route) => route.abort());
  await page.goto("/docs/audit/index.html");

  await expect(page.getByRole("alert")).toHaveText("Audit data could not be loaded.");
});

test("Browse is the default and selection does not explore", async ({ page }) => {
  await page.goto("/docs/index.html");

  await expect(page.getByRole("tab", { name: "Index" })).toHaveAttribute(
    "aria-selected",
    "true",
  );
  const firstArtifact = page.locator('[data-artifact-card] [data-action="select"]').first();
  await firstArtifact.click();
  await expect(page.getByRole("button", { name: "Explore neighborhood" })).toBeEnabled();
  await expect(page.locator("body")).not.toHaveAttribute("data-context");

  await page.getByRole("button", { name: "Explore neighborhood" }).click();
  await expect(page.locator("body")).toHaveAttribute("data-context", /.+/);
});

test("search highlights without removing graph nodes", async ({ page }) => {
  await page.goto("/docs/index.html#view=graph");
  const before = await page.locator("[data-node-id]").count();
  await page.getByRole("searchbox", { name: "Search artifacts and knowledge surfaces" }).fill("architecture");
  const after = await page.locator("[data-node-id]").count();

  expect(after).toBe(before);
  await expect(page.locator("[data-search-match='true']")).not.toHaveCount(0);
});

test("core tasks remain usable with network blocked", async ({ page }) => {
  await page.route("**/*", async (route) => {
    const url = new URL(route.request().url());
    if (url.hostname === "127.0.0.1" || url.hostname === "localhost") {
      await route.continue();
    } else {
      await route.abort();
    }
  });

  await page.goto("/docs/index.html");
  await expect(page.locator("[data-artifact-card]").first()).toBeVisible();
  await page.getByRole("tab", { name: "Graph" }).click();
  await expect(page.getByRole("region", { name: "Project graph" })).toBeVisible();
});

test("keyboard selection and Escape preserve the selected artifact", async ({ page }) => {
  await page.goto("/docs/index.html#view=graph");
  const firstNode = page.locator("[data-node-id]").first();
  await firstNode.focus();
  await firstNode.press("Enter");
  await page.getByRole("button", { name: "Explore neighborhood" }).click();
  await firstNode.focus();
  await firstNode.press("Escape");

  await expect(page.locator("body")).not.toHaveAttribute("data-context");
  await expect(page.locator("[data-selected='true']")).not.toHaveCount(0);
  await expect(page.getByRole("toolbar", { name: "Projection controls" })).toBeFocused();
});

test("narrow layout exposes route navigation without horizontal overflow", async ({
  page,
}) => {
  await page.setViewportSize({ width: 320, height: 800 });
  await page.goto("/docs/index.html");
  await page.locator('[data-artifact-card] [data-action="select"]').first().click();
  await page.getByRole("button", { name: "Open details" }).click();

  await expect(page.getByRole("button", { name: "Back" })).toBeVisible();
  const overflow = await page.evaluate(
    () => document.documentElement.scrollWidth > document.documentElement.clientWidth,
  );
  expect(overflow).toBe(false);
});

test("320 CSS pixels preserves route and focus lifecycle at the 400 percent reflow equivalent", async ({
  page,
}) => {
  await page.setViewportSize({ width: 320, height: 720 });
  await serveIndex(page, fixtureIndex());
  await page.goto("/docs/index.html");
  const artifact = page.locator('[data-artifact-card] [data-action="select"]').first();
  await artifact.click();
  await page.getByRole("button", { name: "Open details" }).click();
  await expect(page.locator("body")).toHaveAttribute("data-route", "details");
  await expect(page.locator("#details-heading")).toBeFocused();
  await page.getByRole("button", { name: "Back" }).click();
  await expect(page.locator("body")).toHaveAttribute("data-route", "browse");
  await expect(page.locator('[data-focus-key="open-details-narrow"]')).toBeFocused();
  expect(await page.evaluate(
    () => document.documentElement.scrollWidth <= document.documentElement.clientWidth,
  )).toBe(true);
});

test("app-owned Back falls back to Browse when no Explorer history entry exists", async ({
  page,
}) => {
  await page.setViewportSize({ width: 320, height: 720 });
  await serveIndex(page, fixtureIndex());
  await page.goto("/docs/index.html#route=visualization&view=graph");

  await page.getByRole("button", { name: "Back" }).click();

  await expect(page.locator("body")).toHaveAttribute("data-route", "browse");
  await expect(page.getByRole("tab", { name: "Index" })).toHaveAttribute(
    "aria-selected",
    "true",
  );
  await expect(page.locator("#browse-heading")).toBeFocused();
});

test("malformed URL state recovers to the canonical Browse route", async ({ page }) => {
  await page.goto(
    "/docs/index.html#view=unknown&route=missing&selected=absent&context=absent&path=invalid",
  );

  await expect(page.getByRole("tab", { name: "Index" })).toHaveAttribute(
    "aria-selected",
    "true",
  );
  await expect(page.locator("body")).toHaveAttribute("data-route", "browse");
  await expect(page.locator("body")).not.toHaveAttribute("data-context");
});

test("projection choices use tab semantics and keyboard navigation", async ({ page }) => {
  await serveIndex(page, fixtureIndex());
  await page.goto("/docs/index.html");

  const tablist = page.getByRole("tablist", { name: "Explorer projection" });
  await expect(tablist.getByRole("tab")).toHaveCount(4);
  const browse = tablist.getByRole("tab", { name: "Index" });
  const graph = tablist.getByRole("tab", { name: "Graph" });
  await expect(browse).toHaveAttribute("aria-selected", "true");
  await expect(graph).toHaveAttribute("aria-selected", "false");
  await browse.focus();
  await browse.press("ArrowRight");
  await expect(graph).toHaveAttribute("aria-selected", "true");
  await expect(graph).toBeFocused();
});

test("browser Back restores selected state and keyboard focus", async ({ page }) => {
  await page.setViewportSize({ width: 320, height: 800 });
  await page.goto("/docs/index.html");
  const firstArtifact = page.locator('[data-artifact-card] [data-action="select"]').first();
  const selectedId = await firstArtifact.getAttribute("data-id");
  await firstArtifact.click();
  await page.getByRole("button", { name: "Open details" }).click();
  await expect(page.locator("body")).toHaveAttribute("data-route", "details");

  await page.goBack();

  await expect(page.locator("body")).toHaveAttribute("data-route", "browse");
  await expect(page.locator('[data-focus-key="open-details-narrow"]')).toBeFocused();
});

test("filter-cleared context is restored through browser Back", async ({ page }) => {
  await page.goto("/docs/index.html");
  const firstArtifact = page.locator('[data-artifact-card] [data-action="select"]').first();
  const contextId = await firstArtifact.getAttribute("data-id");
  const contextType = await page.evaluate(
    (id) => window.DOCS_INDEX.artifacts.find((artifact) => artifact.id === id).type,
    contextId,
  );
  const otherType = await page.evaluate(
    (type) => window.DOCS_INDEX.artifacts.find((artifact) => artifact.type !== type).type,
    contextType,
  );
  await firstArtifact.click();
  await page.getByRole("button", { name: "Explore neighborhood" }).click();
  await page.getByLabel(otherType, { exact: true }).check();
  await page.getByRole("button", { name: "Apply filters" }).click();
  await expect(page.locator("body")).not.toHaveAttribute("data-context");
  await expect(page.locator(".notice").filter({ hasText: "context was cleared" })).toHaveCount(1);
  await expect(page.locator('[role="status"]').filter({ hasText: "context was cleared" })).toHaveCount(1);

  await page.goBack();

  await expect(page.locator("body")).toHaveAttribute("data-context", contextId);
});

test("spatial and relationship-list edge IDs stay in parity", async ({ page }) => {
  await page.goto("/docs/index.html#view=graph");

  const spatialIds = await page.locator("line[id^='edge-']").evaluateAll(
    (items) => items.map((item) => item.id.slice(5)).sort(),
  );
  const listIds = await page.locator(".visual-panel li[id^='list-']").evaluateAll((items) =>
    items.map((item) => item.id.slice(5)).sort(),
  );

  expect(listIds).toEqual(spatialIds);
});

test("knowledge surfaces expose audit, documentation, and design destinations", async ({ page }) => {
  await serveIndex(page, fixtureIndex());
  await page.goto("/docs/index.html");

  const surfaces = page.getByRole("navigation", { name: "Knowledge surfaces" });
  await expect(surfaces.getByRole("link", { name: "Open Audit and change timeline" })).toBeVisible();
  await expect(surfaces.getByRole("link", { name: "Open Documentation bundle" })).toBeVisible();
  await expect(surfaces.getByRole("link", { name: "Open Design preview" })).toBeVisible();
  const destinations = await surfaces.locator(".surface-actions a").evaluateAll(
    (links) => links.map((link) => new URL(link.href).pathname),
  );
  expect(destinations).toEqual([
    "/docs/audit/index.html",
    "/docs/_site/index.html",
    "/docs/design/preview.html",
  ]);
  await surfaces.getByRole("button", { name: "Locate in graph" }).click();
  await expect(page.getByRole("tab", { name: "Graph" })).toHaveAttribute("aria-selected", "true");
  await expect(page.locator('[data-node-id="child"]')).toHaveAttribute("data-selected", "true");
});

test("knowledge surfaces stay visible with an empty state and follow project search", async ({ page }) => {
  await serveIndex(page, fixtureIndex({ surfaces: [] }));
  await page.goto("/docs/index.html");

  const emptySurfaces = page.getByRole("navigation", { name: "Knowledge surfaces" });
  await expect(emptySurfaces).toContainText("No standalone knowledge surfaces were discovered.");

  await serveIndex(page, fixtureIndex());
  await page.goto("/docs/index.html?surfaces=search");
  const surfaces = page.getByRole("navigation", { name: "Knowledge surfaces" });
  await page.getByRole("searchbox", { name: "Search artifacts and knowledge surfaces" }).fill("audit");
  await expect(surfaces.getByRole("link", { name: "Open Audit and change timeline" })).toBeVisible();
  await expect(surfaces.getByRole("link", { name: "Open Documentation bundle" })).toHaveCount(0);
  await expect(page.locator(".match-count")).toContainText("1 match");
  await expect(page.locator(".notice", { hasText: "No search results" })).toHaveCount(0);
  await expect(page.getByRole("status")).not.toContainText("No search results");
  await page.getByRole("searchbox", { name: "Search artifacts and knowledge surfaces" }).fill("not-present");
  await expect(surfaces).toContainText("No knowledge surfaces match this search.");
});

test("Browse tree groups explicitly own their artifact treeitems", async ({ page }) => {
  await serveIndex(page, fixtureIndex());
  await page.goto("/docs/index.html#view=graph");

  const groups = page.locator('[role="treeitem"][data-kind="group"]');
  await expect(groups).toHaveCount(2);
  for (const group of await groups.all()) {
    const ownedId = await group.getAttribute("aria-owns");
    expect(ownedId).toBeTruthy();
    const ownedGroup = page.locator(`#${ownedId}`);
    await expect(ownedGroup).toHaveAttribute("role", "group");
    await expect(ownedGroup.locator('[role="treeitem"][data-kind="artifact"]')).not.toHaveCount(0);
  }
});

test("the real generated index exposes the documentation bundle destination", async ({ page }) => {
  const explorerUrl = pathToFileURL(path.join(process.cwd(), "docs", "index.html")).href;
  await page.goto(explorerUrl);

  const surfaces = page.getByRole("navigation", { name: "Knowledge surfaces" });
  const documentation = surfaces.getByRole("link", { name: /Open .*Documentation/i });
  await expect(documentation).toBeVisible();
  const destination = new URL(await documentation.getAttribute("href"), explorerUrl);
  expect(destination.pathname).toMatch(/\/docs\/_site\/index\.html$/);

  await page.goto(destination.href);
  await expect(page.getByRole("heading", { name: "Documentation hub" })).toBeVisible();
  await expect(
    page.getByText(/does not currently[\s\S]*publish a generated[\s\S]*API reference/i),
  ).toBeVisible();
});

test("knowledge surfaces escape titles and reject traversal paths", async ({ page }) => {
  const index = fixtureIndex({
    surfaces: [
      {
        id: "surface-safe",
        path: "docs/tools/safe.html",
        title: "<script>window.__surfaceOwned = true</script>",
        kind: "knowledge-tool",
        description: "Safe title fixture.",
        artifactId: null,
      },
      {
        id: "surface-traversal",
        path: "../outside.html",
        title: "Outside",
        kind: "knowledge-tool",
        description: "Traversal fixture.",
        artifactId: null,
      },
      {
        id: "surface-scheme",
        path: "javascript:alert(1)",
        title: "Scheme",
        kind: "knowledge-tool",
        description: "Scheme fixture.",
        artifactId: null,
      },
    ],
  });
  await serveIndex(page, index);
  await page.goto("/docs/index.html");

  await expect(page.getByText("<script>window.__surfaceOwned = true</script>")).toBeVisible();
  const safeHref = await page
    .getByRole("link", { name: "Open <script>window.__surfaceOwned = true</script>" })
    .getAttribute("href");
  expect(new URL(safeHref, page.url()).pathname).toBe("/docs/tools/safe.html");
  await expect(page.getByText("Outside")).toHaveCount(0);
  await expect(page.getByText("Scheme")).toHaveCount(0);
  expect(await page.evaluate(() => window.__surfaceOwned)).toBeUndefined();
});

test("Spatial 3D selects and focuses a node without changing relationship semantics", async ({ page }) => {
  await serveIndex(page, fixtureIndex());
  await page.goto("/docs/index.html#view=spatial3d");

  const spatial = page.getByRole("region", { name: "Spatial 3D project graph" });
  await expect(spatial).toBeVisible();
  await spatial.locator('[data-action="select"][data-node-id="child"]').click();
  await expect(spatial.locator("[data-spatial-svg]")).toHaveAttribute("data-camera-target-id", "child");
  await expect(spatial.locator("[data-spatial-svg]")).toHaveAttribute("data-camera-transitioning", "true");
  await expect(spatial.locator("[data-spatial-svg]")).toHaveAttribute(
    "data-camera-transitioning",
    "false",
    { timeout: 3_000 },
  );
  await expect(spatial.locator('[data-node-id="child"]')).toHaveAttribute("data-selected", "true");

  const spatialIds = await spatial.locator("[data-spatial-edge]").evaluateAll(
    (items) => items.map((item) => item.dataset.spatialEdge).sort(),
  );
  const listIds = await page.locator(".visual-panel li[id^='list-']").evaluateAll(
    (items) => items.map((item) => item.id.slice(5)).sort(),
  );
  expect(listIds).toEqual(spatialIds);
});

test("Spatial 3D completes canonical focus when a routine render interrupts motion", async ({
  page,
}) => {
  await serveIndex(page, fixtureIndex());
  await page.goto("/docs/index.html#view=spatial3d");
  await page.addStyleTag({ content: ":root { --motion-context: 2000ms !important; }" });

  await page.locator('[data-action="select"][data-node-id="child"]').click();
  await page.waitForTimeout(50);
  await page.evaluate(() => window.dispatchEvent(new Event("resize")));

  const child = page.locator('[data-spatial-node="child"]');
  await expect(page.locator("[data-spatial-svg]")).toHaveAttribute(
    "data-camera-transitioning",
    "false",
  );
  await expect(child).toHaveAttribute("x", "528");
  await expect(child).toHaveAttribute("y", "356");
});

test("Spatial 3D re-establishes canonical focus after manual interruption", async ({ page }) => {
  await serveIndex(page, fixtureIndex());
  await page.goto("/docs/index.html#view=spatial3d");
  await page.addStyleTag({ content: ":root { --motion-context: 2000ms !important; }" });

  await page.locator('[data-action="select"][data-node-id="child"]').click();
  await page.waitForTimeout(50);
  await page.getByRole("button", { name: "Orbit right" }).click();
  await expect(page.locator("[data-spatial-svg]")).toHaveAttribute("data-camera-target-id", "");

  await page.evaluate(() => window.dispatchEvent(new Event("resize")));

  const child = page.locator('[data-spatial-node="child"]');
  await expect(page.locator("[data-spatial-svg]")).toHaveAttribute(
    "data-camera-transitioning",
    "false",
    { timeout: 3_000 },
  );
  await expect(page.locator("[data-spatial-svg]")).toHaveAttribute(
    "data-camera-target-id",
    "child",
  );
  await expect(child).toHaveAttribute("x", "528");
  await expect(child).toHaveAttribute("y", "356");
});

test("Spatial 3D camera supports orbit, zoom, focus, and reset controls", async ({ page }) => {
  await serveIndex(page, fixtureIndex());
  await page.goto("/docs/index.html#view=spatial3d&selected=child");

  const svg = page.locator("[data-spatial-svg]");
  const initialYaw = Number(await svg.getAttribute("data-camera-yaw"));
  const initialPitch = Number(await svg.getAttribute("data-camera-pitch"));
  const initialZoom = Number(await svg.getAttribute("data-camera-zoom"));
  await page.getByRole("button", { name: "Orbit right" }).click();
  expect(Number(await svg.getAttribute("data-camera-yaw"))).toBeGreaterThan(initialYaw);
  await page.getByRole("button", { name: "Orbit down" }).click();
  expect(Number(await svg.getAttribute("data-camera-pitch"))).toBeGreaterThan(initialPitch);
  const box = await svg.boundingBox();
  await page.mouse.move(box.x + 20, box.y + 20);
  await page.mouse.down();
  await page.mouse.move(box.x + 100, box.y + 45);
  await page.mouse.up();
  expect(Number(await svg.getAttribute("data-camera-yaw"))).not.toBe(initialYaw);

  await page.getByRole("button", { name: "Zoom in" }).click();
  expect(Number(await svg.getAttribute("data-camera-zoom"))).toBeGreaterThan(initialZoom);
  await page.getByRole("button", { name: "Zoom out" }).click();
  expect(Number(await svg.getAttribute("data-camera-zoom"))).toBeCloseTo(initialZoom);
  await svg.dispatchEvent("wheel", { deltaY: -100 });
  await expect.poll(async () => Number(await svg.getAttribute("data-camera-zoom")))
    .toBeGreaterThan(initialZoom);
  await page.getByRole("button", { name: "Focus selected" }).click();
  await expect(svg).toHaveAttribute("data-camera-target-id", "child");
  await page.getByRole("button", { name: "Reset camera" }).click();
  await expect(svg).toHaveAttribute("data-camera-target-id", "child");
  expect(Number(await svg.getAttribute("data-camera-zoom"))).toBe(1);
});

test("Spatial 3D retargets selected-node geometry after filters change the layout", async ({
  page,
}) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await serveIndex(page, fixtureIndex());
  await page.goto("/docs/index.html#view=spatial3d&selected=child");

  const child = page.locator('[data-spatial-node="child"]');
  await expect(child).toHaveAttribute("x", "528");
  await expect(child).toHaveAttribute("y", "356");

  await page.getByRole("checkbox", { name: "design", exact: true }).check();
  await page.getByRole("button", { name: "Apply filters" }).click();

  await expect(child).toHaveAttribute("x", "528");
  await expect(child).toHaveAttribute("y", "356");
  await expect(page.locator("[data-spatial-svg]")).toHaveAttribute(
    "data-camera-target-id",
    "child",
  );
});

test("Spatial 3D controls do not target a selected node excluded by filters", async ({
  page,
}) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await serveIndex(page, fixtureIndex());
  await page.goto("/docs/index.html#view=spatial3d&selected=child");

  await page.getByRole("checkbox", { name: "architecture", exact: true }).check();
  await page.getByRole("button", { name: "Apply filters" }).click();

  await expect(page.getByRole("button", { name: "Focus selected" })).toBeDisabled();
  await page.getByRole("button", { name: "Reset camera" }).click();
  await expect(page.locator("[data-spatial-svg]")).toHaveAttribute("data-camera-target-id", "");
  await expect(page.getByRole("status")).toContainText(
    "Spatial camera reset to the project overview.",
  );
});

test("Spatial 3D snaps focus with reduced motion", async ({ page }) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await serveIndex(page, fixtureIndex());
  await page.goto("/docs/index.html#view=spatial3d");

  await page.locator('[data-action="select"][data-node-id="child"]').click();

  await expect(page.locator("[data-spatial-svg]")).toHaveAttribute("data-camera-target-id", "child");
  await expect(page.locator("[data-spatial-svg]")).toHaveAttribute("data-camera-transitioning", "false");
  await expect(page.getByRole("status")).toContainText("Selected Child");
});

test("Spatial 3D unsupported capability fails closed to Graph", async ({ page }) => {
  await page.addInitScript(() => {
    Object.defineProperty(window, "PointerEvent", { configurable: true, value: undefined });
  });
  await serveIndex(page, fixtureIndex());
  await page.goto("/docs/index.html#view=spatial3d&selected=child");

  await expect(page.getByRole("tab", { name: "Graph" })).toHaveAttribute("aria-selected", "true");
  await expect(page.locator(".notice")).toContainText("DOC.SPATIAL3D.UNAVAILABLE");
  await expect(page.locator('[data-node-id="child"]')).toHaveAttribute("data-selected", "true");
});

test("Spatial 3D render failure preserves semantic state in Graph", async ({ page }) => {
  await serveIndex(page, fixtureIndex());
  await page.goto("/docs/index.html#view=graph&selected=child");
  await page.evaluate(() => {
    window.DocsExplorerCore.deterministic3DLayout = () => {
      throw new Error("spatial failed");
    };
  });

  await page.getByRole("tab", { name: "3D" }).click();

  await expect(page.getByRole("tab", { name: "Graph" })).toHaveAttribute("aria-selected", "true");
  await expect(page.locator(".notice")).toContainText("DOC.SPATIAL3D.RENDER_FAILED");
  await expect(page.locator('[data-node-id="child"]')).toHaveAttribute("data-selected", "true");
});

test("relationship actions restore focus to stable selected-node context", async ({ page }) => {
  await serveIndex(page, fixtureIndex());
  await page.goto("/docs/index.html#view=graph&selected=root");
  const relationshipTarget = page.locator(
    '.visual-panel [data-focus-key^="relationship-visible-"][data-focus-key$="-target"]',
  ).first();
  const focusKey = await relationshipTarget.getAttribute("data-focus-key");
  await relationshipTarget.focus();
  await relationshipTarget.click();

  await expect(page.locator(`.visual-panel [data-focus-key="${focusKey}"]`)).toBeFocused();
  await expect(page.locator("#details-heading")).toHaveText("Child");
});

test("path controls expose active, list-parity, and empty states", async ({ page }) => {
  await serveIndex(page, fixtureIndex());
  await page.goto("/docs/index.html#selected=root");

  const grounding = page.getByRole("button", { name: "Trace grounding" });
  await grounding.click();

  await expect(grounding).toHaveAttribute("aria-pressed", "true");
  await expect(page.getByRole("tab", { name: "Graph" })).toHaveAttribute(
    "aria-selected",
    "true",
  );
  await expect(page.locator("line.path")).toHaveCount(1);
  await expect(page.locator(".visual-panel .relationship-list li.path")).toHaveCount(1);
  await expect(page.locator(".visual-panel .relationship-list li.path")).toContainText(
    "On traced path",
  );

  await page.getByRole("button", { name: "Show proofs" }).click();
  await expect(page.getByText("No proof relationships are available from this artifact.")).toBeVisible();
  await expect(page.locator("line.path")).toHaveCount(0);
});

test("narrow match navigation opens Browse before focusing the result", async ({ page }) => {
  await serveIndex(page, fixtureIndex());
  await page.setViewportSize({ width: 320, height: 800 });
  await page.goto("/docs/index.html#route=details&selected=root");
  await page.getByRole("searchbox", { name: "Search artifacts and knowledge surfaces" }).fill("child");

  await page.getByRole("button", { name: "Next" }).click();

  await expect(page.locator("body")).toHaveAttribute("data-route", "browse");
  await expect(page.locator('[data-focus-key="index-child"]')).toBeFocused();
});

test("empty Details route keeps its labelled heading", async ({ page }) => {
  await serveIndex(page, fixtureIndex());
  await page.setViewportSize({ width: 320, height: 800 });
  await page.goto("/docs/index.html#route=details");

  await expect(page.locator('[aria-labelledby="details-heading"]')).toBeVisible();
  await expect(page.locator("#details-heading")).toHaveText("Artifact details");
});

test("duplicate typed links fail closed with a stable recovery code", async ({ page }) => {
  const index = fixtureIndex();
  index.artifacts[0].links.push({ to: "child", rel: "depends-on" });
  await serveIndex(page, index);

  await page.goto("/docs/index.html#view=graph");

  await expect(page.getByRole("alert")).toContainText("DOC.INDEX.INVALID");
});

test("over-limit indexes are rejected before spatial layout", async ({ page }) => {
  await serveIndex(
    page,
    fixtureIndex({
      limits: {
        indexBytes: 5 * 1024 * 1024,
        artifacts: 1,
        relationships: 5000,
        spatialNodes: 500,
        spatialEdges: 1000,
      },
    }),
  );

  await page.goto("/docs/index.html#view=graph");

  await expect(page.getByRole("alert")).toContainText("DOC.INDEX.LIMIT_EXCEEDED");
  await expect(page.getByRole("alert")).toContainText("supported artifacts limit");
  await expect(page.locator("[data-node-id]")).toHaveCount(0);
});

test("source-load failure preserves metadata and relationships", async ({ page }) => {
  await page.route("**/*.md", (route) => route.abort());
  await page.goto("/docs/index.html");
  await page.locator('[data-artifact-card] [data-action="select"]').first().click();
  const title = await page.locator("#details-heading").textContent();

  await page.getByRole("button", { name: "Load source body" }).click();

  await expect(page.getByRole("alert")).toContainText("source body is unavailable");
  await expect(page.locator("#details-heading")).toHaveText(title);
  await expect(
    page.locator(".details-panel").getByRole("heading", { name: "Relationships" }),
  ).toBeVisible();
});

test("hostile metadata is rendered as inert text", async ({ page }) => {
  const index = fixtureIndex();
  index.artifacts[0].title = '<img src=x onerror="window.__explorerInjected=true">';
  index.artifacts[0].summary = '<script>window.__explorerInjected=true</script>';
  await serveIndex(page, index);

  await page.goto("/docs/index.html");
  await page.locator('[data-artifact-card] [data-action="select"]').first().click();

  await expect(page.locator(".details-panel img, .details-panel script")).toHaveCount(0);
  expect(await page.evaluate(() => window.__explorerInjected)).toBeUndefined();
  await expect(page.locator("#details-heading")).toContainText("<img");
});

test("network-enabled Explorer emits no non-loopback requests", async ({ page }) => {
  const remoteRequests = [];
  page.on("request", (request) => {
    const url = new URL(request.url());
    if (!["127.0.0.1", "localhost"].includes(url.hostname)) remoteRequests.push(request.url());
  });

  await page.goto("/docs/index.html");
  await page.getByRole("tab", { name: "Graph" }).click();

  expect(remoteRequests).toEqual([]);
});

test("reference graph renders through the browser integration path", async ({ page }) => {
  await page.goto("/docs/index.html#view=graph");
  await expect(page.getByRole("region", { name: "Project graph" })).toBeVisible();
});

test("tree exposes one tab stop and complete disclosure keyboard semantics", async ({ page }) => {
  await serveIndex(page, fixtureIndex());
  await page.goto("/docs/index.html#view=graph");

  const tree = page.getByRole("tree", { name: "Project artifacts" });
  const firstGroup = tree.locator('[data-kind="group"]').first();
  await expect(tree.locator('[role="treeitem"][tabindex="0"]')).toHaveCount(1);
  await firstGroup.focus();
  await firstGroup.press("ArrowRight");
  await expect(tree.locator('[data-kind="artifact"]').first()).toBeFocused();
  await page.keyboard.press("ArrowLeft");
  await expect(firstGroup).toBeFocused();
  await firstGroup.press(" ");
  await expect(firstGroup).toHaveAttribute("aria-expanded", "false");
  await firstGroup.press("ArrowRight");
  await expect(firstGroup).toHaveAttribute("aria-expanded", "true");
  await firstGroup.press("ArrowRight");
  await expect(tree.locator('[data-kind="artifact"]').first()).toBeFocused();
  await page.keyboard.press("End");
  await expect(tree.locator('[role="treeitem"]:visible').last()).toBeFocused();
  await page.keyboard.press("Home");
  await expect(firstGroup).toBeFocused();
});

test("collapsing a tree group transfers the roving tab stop from its hidden child", async ({
  page,
}) => {
  await serveIndex(page, fixtureIndex());
  await page.goto("/docs/index.html#view=graph");
  const tree = page.getByRole("tree", { name: "Project artifacts" });
  const group = tree.locator('[data-kind="group"]').first();
  const child = tree.locator('[data-kind="artifact"]').first();
  await child.focus();

  await group.click();

  await expect(group).toHaveAttribute("aria-expanded", "false");
  await expect(group).toHaveAttribute("tabindex", "0");
  await expect(child).toBeHidden();
  await expect(tree.locator('[role="treeitem"][tabindex="0"]:visible')).toHaveCount(1);
});

test("spatial arrow navigation transfers the roving tab stop before focus", async ({ page }) => {
  await serveIndex(page, fixtureIndex());
  await page.goto("/docs/index.html#view=graph");
  const root = page.locator('[data-node-id="root"]');
  const child = page.locator('[data-node-id="child"]');
  await root.focus();

  await root.press("ArrowRight");

  await expect(child).toBeFocused();
  await expect(child).toHaveAttribute("tabindex", "0");
  await expect(root).toHaveAttribute("tabindex", "-1");
  await expect(page.locator('[data-node-id][tabindex="0"]')).toHaveCount(1);
});

test("Spatial arrow navigation ignores hidden or off-canvas candidates", async ({ page }) => {
  await serveIndex(page, fixtureIndex());
  await page.goto("/docs/index.html#view=graph");
  await page.evaluate(() => {
    const original = window.DocsExplorerCore.projectSpatialLayout;
    window.DocsExplorerCore.projectSpatialLayout = (...args) => {
      const projection = original(...args);
      projection.nodes = projection.nodes.map((node) =>
        node.id === "child" ? { ...node, visible: false, screenX: -1000 } : node);
      return projection;
    };
  });
  await page.getByRole("tab", { name: "3D" }).click();
  const root = page.locator('[data-node-id="root"]');
  await root.click();
  await root.focus();

  await root.press("ArrowRight");

  await expect(root).toBeFocused();
  await expect(root).toHaveAttribute("tabindex", "0");
});

test("narrow route transitions focus headings and history restores the initiating control", async ({
  page,
}) => {
  await serveIndex(page, fixtureIndex());
  await page.setViewportSize({ width: 320, height: 800 });
  await page.goto("/docs/index.html");
  const artifact = page.locator('[data-artifact-card] [data-action="select"]').first();
  const artifactId = await artifact.getAttribute("data-id");
  await artifact.click();
  await page.getByRole("button", { name: "Open details" }).click();
  await expect(page.locator("#details-heading")).toBeFocused();

  await page.goBack();
  await expect(page.locator('[data-focus-key="open-details-narrow"]')).toBeFocused();

  await page.goForward();
  await expect(page.locator("#details-heading")).toBeFocused();
});

test("resizing to the narrow layout restores focus to a visible artifact control", async ({ page }) => {
  await serveIndex(page, fixtureIndex());
  await page.goto("/docs/index.html");
  const artifact = page.locator('[data-artifact-card] [data-action="select"]').first();
  const artifactId = await artifact.getAttribute("data-id");
  await artifact.click();
  await page.getByRole("button", { name: "Load source body" }).focus();

  await page.setViewportSize({ width: 320, height: 800 });

  await expect(page.locator(`[data-focus-key="index-${artifactId}"]`)).toBeFocused();
  await expect(page.locator(":focus")).toBeVisible();
});

test("exploring on a narrow screen focuses the visualization heading", async ({ page }) => {
  await serveIndex(page, fixtureIndex());
  await page.setViewportSize({ width: 320, height: 800 });
  await page.goto("/docs/index.html");
  await page.locator('[data-artifact-card] [data-action="select"]').first().click();

  await page.getByRole("button", { name: "Explore neighborhood" }).click();

  await expect(page.locator("#visual-heading")).toBeFocused();
  await expect(page.locator("body")).toHaveAttribute("data-route", "visualization");
});

test("persistent live region announces selection, exploration, and context exit", async ({ page }) => {
  await serveIndex(page, fixtureIndex());
  await page.goto("/docs/index.html");
  const artifact = page.locator('[data-artifact-card] [data-action="select"]').first();
  await artifact.click();
  await expect(page.locator("#explorer-status")).toContainText("Selected Root");

  await page.getByRole("button", { name: "Explore neighborhood" }).click();
  await expect(page.locator("#explorer-status")).toContainText("Explored Root");

  await page.getByRole("button", { name: "Leave neighborhood" }).first().click();
  await expect(page.locator("#explorer-status")).toContainText("Left neighborhood context");
  await expect(page.locator("#explorer-status")).toHaveCount(1);
});

test("Explore is disabled with a visible explanation until an artifact is selected", async ({
  page,
}) => {
  await serveIndex(page, fixtureIndex());
  await page.goto("/docs/index.html");

  const explore = page.getByRole("button", { name: "Explore neighborhood" });
  await expect(explore).toBeDisabled();
  await expect(explore).toHaveAttribute("aria-describedby", "explore-disabled-reason");
  await expect(page.locator("#explore-disabled-reason")).toBeVisible();
});

test("search preserves focus and caret and exposes a non-color match indicator", async ({ page }) => {
  await serveIndex(page, fixtureIndex());
  await page.goto("/docs/index.html#view=graph");
  const search = page.getByRole("searchbox", { name: "Search artifacts and knowledge surfaces" });
  await search.fill("root child");
  await search.evaluate((element) => {
    element.focus();
    element.value = "rootx child";
    element.setSelectionRange(5, 5);
    element.dispatchEvent(new InputEvent("input", { bubbles: true, inputType: "insertText" }));
  });

  await expect(search).toBeFocused();
  await expect.poll(
    () => search.evaluate((element) => [element.selectionStart, element.selectionEnd]),
    { timeout: 1000 },
  ).toEqual([5, 5]);

  await search.fill("root");
  await expect(page.locator("[data-search-match='true'] .match-indicator").first()).toBeVisible();
});

test("rapid search replacement keeps the live input connected and announcements current", async ({ page }) => {
  await serveIndex(page, fixtureIndex());
  await page.goto("/docs/index.html#view=graph");

  const replacement = await page.evaluate(() => new Promise((resolve) => {
    const first = document.getElementById("search");
    first.focus();
    first.value = "not-present";
    first.setSelectionRange(2, 2);
    first.dispatchEvent(new InputEvent("beforeinput", {
      bubbles: true,
      inputType: "insertText",
    }));
    first.dispatchEvent(new InputEvent("input", {
      bubbles: true,
      inputType: "insertText",
    }));

    requestAnimationFrame(() => {
      const second = document.getElementById("search");
      second.value = "root";
      second.setSelectionRange(4, 4);
      second.dispatchEvent(new InputEvent("beforeinput", {
        bubbles: true,
        inputType: "insertReplacementText",
      }));
      second.dispatchEvent(new InputEvent("input", {
        bubbles: true,
        inputType: "insertReplacementText",
      }));
      resolve({
        sameNode: first === second,
        connected: second.isConnected,
        selection: [second.selectionStart, second.selectionEnd],
        value: second.value,
      });
    });
  }));

  expect(replacement).toEqual({
    sameNode: true,
    connected: true,
    selection: [4, 4],
    value: "root",
  });
  const search = page.getByRole("searchbox", {
    name: "Search artifacts and knowledge surfaces",
  });
  await expect(search).toHaveValue("root");
  await expect(search).toBeFocused();
  await expect.poll(
    () => search.evaluate((element) => [element.selectionStart, element.selectionEnd]),
    { timeout: 1000 },
  ).toEqual([4, 4]);
  await expect(page.locator("[data-search-match='true']")).not.toHaveCount(0);
  await expect(page.getByRole("status")).toHaveText('Search results available for "root"');
});

test("popstate restoration synchronizes a preserved focused search input with restored state", async ({
  page,
}) => {
  await serveIndex(page, fixtureIndex());
  await page.goto("/docs/index.html#view=graph");
  const search = page.getByRole("searchbox", {
    name: "Search artifacts and knowledge surfaces",
  });

  await search.fill("root");
  await search.focus();
  await page.evaluate(() => {
    const restored = { docsExplorerDepth: 0, focusKey: "search" };
    history.replaceState(restored, "", "#view=graph");
    dispatchEvent(new PopStateEvent("popstate", { state: restored }));
  });

  await expect(search).toBeFocused();
  await expect(search).toHaveValue("");
  await expect(page.locator("[data-search-match='true']")).toHaveCount(0);
  await expect(page.locator(".notice").filter({ hasText: "No search results" })).toHaveCount(0);
});

test("search announces zero-result transitions but not positive counts on every keystroke", async ({
  page,
}) => {
  await serveIndex(page, fixtureIndex());
  await page.goto("/docs/index.html#view=graph");
  const before = await page.locator("[data-node-id]").count();
  const search = page.getByRole("searchbox", {
    name: "Search artifacts and knowledge surfaces",
  });

  await search.fill("root");
  await expect(page.locator("[data-search-match='true']")).not.toHaveCount(0);
  await expect(page.getByRole("status")).not.toContainText("search match");
  await search.fill("not-present");
  await search.fill("not-present");

  await expect(page.locator(".notice")).toContainText(
    'No search results for "not-present"',
  );
  await expect(page.getByRole("button", { name: "Clear filters" })).toBeVisible();
  await expect(page.getByRole("status")).toContainText(
    'No search results for "not-present"',
  );
  await expect(page.locator("[data-node-id]")).toHaveCount(before);
  await page.getByRole("button", { name: "Clear search" }).click();
  await expect(search).toHaveValue("");
  await expect(page.locator("[data-search-match='true']")).toHaveCount(0);
  await expect(page.getByRole("status")).toContainText("Search cleared");
});

test("reduced-motion mode removes control transitions and focused controls retain a visible floor", async ({
  page,
}) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await serveIndex(page, fixtureIndex());
  await page.goto("/docs/index.html");
  const browseTab = page.getByRole("tab", { name: "Index" });
  await browseTab.focus();

  const styles = await browseTab.evaluate((element) => {
    const computed = getComputedStyle(element);
    return {
      transitionDuration: computed.transitionDuration,
      outlineStyle: computed.outlineStyle,
      outlineWidth: computed.outlineWidth,
    };
  });

  expect(styles.transitionDuration).toBe("0s");
  expect(styles.outlineStyle).not.toBe("none");
  expect(Number.parseFloat(styles.outlineWidth)).toBeGreaterThanOrEqual(2);
  await page.getByRole("tab", { name: "3D" }).click();
  await expect.poll(() =>
    page.locator(".spatial-node-wrap").first().evaluate(
      (element) => getComputedStyle(element).transitionDuration,
    ))
    .toBe("0s");
});

test("sticky header does not obscure a focused explorer control", async ({ page }) => {
  await serveIndex(page, fixtureIndex());
  await page.goto("/docs/index.html");
  const browseTab = page.getByRole("tab", { name: "Index" });
  await browseTab.focus();

  const bounds = await page.evaluate(() => {
    const header = document.querySelector("header").getBoundingClientRect();
    const focused = document.activeElement.getBoundingClientRect();
    return { headerBottom: header.bottom, focusedTop: focused.top };
  });
  expect(bounds.focusedTop).toBeGreaterThanOrEqual(bounds.headerBottom);
});

test("screen text contrast and interactive target sizes meet the declared floors", async ({ page }) => {
  await serveIndex(page, fixtureIndex());
  await page.goto("/docs/index.html#view=graph");

  const audit = await page.evaluate(() => {
    const parse = (value) => {
      const channels = value.match(/[\d.]+/g).slice(0, 3).map(Number);
      return channels.map((channel) => {
        const normalized = channel / 255;
        return normalized <= 0.04045
          ? normalized / 12.92
          : ((normalized + 0.055) / 1.055) ** 2.4;
      });
    };
    const luminance = (rgb) => 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2];
    const contrast = (foreground, background) => {
      const light = Math.max(luminance(parse(foreground)), luminance(parse(background)));
      const dark = Math.min(luminance(parse(foreground)), luminance(parse(background)));
      return (light + 0.05) / (dark + 0.05);
    };
    const textPairs = ["body", ".panel", "button:not(:disabled)", "input"].map((selector) => {
      const element = document.querySelector(selector);
      const style = getComputedStyle(element);
      let background = style.backgroundColor;
      if (background === "rgba(0, 0, 0, 0)") {
        background = getComputedStyle(document.documentElement).backgroundColor;
      }
      return { selector, ratio: contrast(style.color, background) };
    });
    const opaqueBackground = (element) => {
      let current = element;
      while (current) {
        const color = getComputedStyle(current).backgroundColor;
        if (color !== "rgba(0, 0, 0, 0)") return color;
        current = current.parentElement;
      }
      return getComputedStyle(document.documentElement).backgroundColor;
    };
    const nonTextPairs = [".panel", ".visualization", "[data-node-id]"].map((selector) => {
      const element = document.querySelector(selector);
      return {
        selector,
        ratio: contrast(getComputedStyle(element).borderColor, opaqueBackground(element)),
      };
    });
    const edge = document.querySelector(".edge");
    nonTextPairs.push({
      selector: ".edge",
      ratio: contrast(getComputedStyle(edge).stroke, opaqueBackground(edge.closest(".visualization"))),
    });
    const undersized = [...document.querySelectorAll("button:not(:disabled), input:not([type='checkbox']), a[href], summary")].filter((element) => {
      const box = element.getBoundingClientRect();
      return box.width > 0 && box.height > 0 && (box.width < 44 || box.height < 44);
    }).map((element) => element.outerHTML);
    const undersizedCheckboxTargets = [...document.querySelectorAll(".filter-options label")].filter((element) => {
      const box = element.getBoundingClientRect();
      return box.width > 0 && box.height > 0 && (box.width < 44 || box.height < 44);
    }).map((element) => element.outerHTML);
    return { textPairs, nonTextPairs, undersized, undersizedCheckboxTargets };
  });

  for (const pair of audit.textPairs) {
    expect(pair.ratio, pair.selector).toBeGreaterThanOrEqual(4.5);
  }
  for (const pair of audit.nonTextPairs) {
    expect(pair.ratio, pair.selector).toBeGreaterThanOrEqual(3);
  }
  expect(audit.undersized).toEqual([]);
  expect(audit.undersizedCheckboxTargets).toEqual([]);

  const surfaceAudit = await page.locator(".surface-card").evaluateAll((elements) => {
    const parse = (value) => {
      const channels = value.match(/[\d.]+/g).slice(0, 3).map(Number);
      return channels.map((channel) => {
        const normalized = channel / 255;
        return normalized <= 0.04045
          ? normalized / 12.92
          : ((normalized + 0.055) / 1.055) ** 2.4;
      });
    };
    const luminance = (rgb) => 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2];
    const contrast = (foreground, background) => {
      const light = Math.max(luminance(parse(foreground)), luminance(parse(background)));
      const dark = Math.min(luminance(parse(foreground)), luminance(parse(background)));
      return (light + 0.05) / (dark + 0.05);
    };
    return elements.map((element) => {
      const link = element.querySelector("a");
      const background = getComputedStyle(element).backgroundColor;
      return {
        title: element.querySelector("strong").textContent,
        textRatio: contrast(getComputedStyle(element).color, background),
        linkRatio: contrast(getComputedStyle(link).color, background),
        linkHeight: link.getBoundingClientRect().height,
      };
    });
  });
  for (const surface of surfaceAudit) {
    expect(surface.textRatio, `${surface.title} text`).toBeGreaterThanOrEqual(4.5);
    expect(surface.linkRatio, `${surface.title} link`).toBeGreaterThanOrEqual(4.5);
    expect(surface.linkHeight, `${surface.title} target`).toBeGreaterThanOrEqual(44);
  }

  await page.getByRole("tab", { name: "3D" }).click();
  const spatialAudit = await page.locator(".projection-toolbar button, [data-spatial-svg]").evaluateAll(
    (elements) => elements.map((element) => ({
      name: element.getAttribute("aria-label"),
      width: element.getBoundingClientRect().width,
      height: element.getBoundingClientRect().height,
    })),
  );
  for (const control of spatialAudit) {
    expect(control.width, `${control.name} width`).toBeGreaterThanOrEqual(44);
    expect(control.height, `${control.name} height`).toBeGreaterThanOrEqual(44);
  }
});

test("light mode uses the accepted accessible token pairs", async ({ page }) => {
  await page.emulateMedia({ colorScheme: "light" });
  await serveIndex(page, fixtureIndex());
  await page.goto("/docs/index.html#view=graph");

  const tokens = await page.evaluate(() => {
    const style = getComputedStyle(document.documentElement);
    return {
      background: style.getPropertyValue("--color-bg").trim(),
      surface: style.getPropertyValue("--color-surface").trim(),
      text: style.getPropertyValue("--color-text").trim(),
      border: style.getPropertyValue("--color-border").trim(),
      primary: style.getPropertyValue("--color-primary").trim(),
      focus: style.getPropertyValue("--color-focus").trim(),
    };
  });
  expect(tokens).toEqual({
    background: "#f7f4ef",
    surface: "#fcfbf8",
    text: "#242424",
    border: "#8a8886",
    primary: "#b11f4b",
    focus: "#006cbe",
  });
});

test("dark mode follows the browser preference and ignores legacy query overrides", async ({ page }) => {
  await page.emulateMedia({ colorScheme: "dark" });
  await serveIndex(page, fixtureIndex());
  await page.goto("/docs/index.html?clawpilotTheme=light#view=graph");

  const tokens = await page.evaluate(() => {
    const style = getComputedStyle(document.documentElement);
    return {
      colorScheme: style.colorScheme,
      background: style.getPropertyValue("--color-bg").trim(),
      text: style.getPropertyValue("--color-text").trim(),
      primary: style.getPropertyValue("--color-primary").trim(),
      focus: style.getPropertyValue("--color-focus").trim(),
    };
  });
  const accessibility = await page.evaluate(() => {
    const channels = (value) => value.match(/[\d.]+/g).slice(0, 3).map(Number).map((channel) => {
      const normalized = channel / 255;
      return normalized <= 0.04045
        ? normalized / 12.92
        : ((normalized + 0.055) / 1.055) ** 2.4;
    });
    const luminance = (rgb) => 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2];
    const contrast = (foreground, background) => {
      const values = [luminance(channels(foreground)), luminance(channels(background))];
      return (Math.max(...values) + 0.05) / (Math.min(...values) + 0.05);
    };
    const opaqueBackground = (element) => {
      let current = element;
      while (current) {
        const color = getComputedStyle(current).backgroundColor;
        if (color !== "rgba(0, 0, 0, 0)") return color;
        current = current.parentElement;
      }
      return getComputedStyle(document.documentElement).backgroundColor;
    };
    const textRatios = ["body", ".panel", "button:not(:disabled)", "input", ".surface-card a"]
      .map((selector) => {
        const element = document.querySelector(selector);
        return {
          selector,
          ratio: contrast(getComputedStyle(element).color, opaqueBackground(element)),
        };
      });
    const nonTextRatios = [".panel", ".visualization", "[data-node-id]"].map((selector) => {
      const element = document.querySelector(selector);
      return {
        selector,
        ratio: contrast(getComputedStyle(element).borderColor, opaqueBackground(element)),
      };
    });
    const undersized = [...document.querySelectorAll(
      "button:not(:disabled), input:not([type='checkbox']), a[href], summary",
    )].filter((element) => {
      const box = element.getBoundingClientRect();
      return box.width > 0 && box.height > 0 && (box.width < 44 || box.height < 44);
    }).map((element) => element.outerHTML);
    return { textRatios, nonTextRatios, undersized };
  });

  expect(tokens).toEqual({
    colorScheme: "dark",
    background: "#3d3b3a",
    text: "#dedede",
    primary: "#fd8ea1",
    focus: "#62b0ff",
  });
  for (const pair of accessibility.textRatios) {
    expect(pair.ratio, `dark ${pair.selector}`).toBeGreaterThanOrEqual(4.5);
  }
  for (const pair of accessibility.nonTextRatios) {
    expect(pair.ratio, `dark ${pair.selector}`).toBeGreaterThanOrEqual(3);
  }
  expect(accessibility.undersized).toEqual([]);
});

test("authored high-contrast mode is reachable through prefers-contrast", async ({
  page,
  browserName,
}) => {
  test.skip(browserName !== "chromium", "prefers-contrast emulation is exercised in Chromium");
  await page.emulateMedia({ contrast: "more" });
  await serveIndex(page, fixtureIndex());
  await page.goto("/docs/index.html#view=graph");

  const audit = await page.evaluate(() => {
    const style = getComputedStyle(document.documentElement);
    const body = getComputedStyle(document.body);
    const channels = (value) => value.match(/[\d.]+/g).slice(0, 3).map(Number).map((channel) => {
      const normalized = channel / 255;
      return normalized <= 0.04045
        ? normalized / 12.92
        : ((normalized + 0.055) / 1.055) ** 2.4;
    });
    const luminance = (rgb) => 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2];
    const foreground = luminance(channels(body.color));
    const background = luminance(channels(body.backgroundColor));
    return {
      tokens: {
        background: style.getPropertyValue("--color-bg").trim(),
        text: style.getPropertyValue("--color-text").trim(),
        border: style.getPropertyValue("--color-border").trim(),
        primary: style.getPropertyValue("--color-primary").trim(),
      },
      bodyBackground: body.backgroundColor,
      bodyContrast: (Math.max(foreground, background) + 0.05)
        / (Math.min(foreground, background) + 0.05),
    };
  });

  expect(audit.tokens).toEqual({
    background: "#000000",
    text: "#ffffff",
    border: "#ffffff",
    primary: "#ffff00",
  });
  expect(audit.bodyBackground).toBe("rgb(0, 0, 0)");
  expect(audit.bodyContrast).toBeGreaterThanOrEqual(7);
});

test("source loading states use the single announcement channel", async ({ page }) => {
  const source = "# Root source";
  await serveIndex(page, withRootSource(fixtureIndex(), source));
  await page.route("**/root.md", async (route) => {
    await new Promise((resolve) => setTimeout(resolve, 100));
    await route.fulfill({ contentType: "text/markdown", body: source });
  });
  await page.goto("/docs/index.html");

  await page.getByRole("searchbox", { name: "Search artifacts and knowledge surfaces" }).fill("root");
  await expect(page.locator('[role="status"]')).toHaveCount(1);
  await expect(page.locator("#explorer-status")).toHaveText('Search results available for "root"');

  await page.locator('[data-artifact-card] [data-action="select"][data-id="root"]').click();
  await page.getByRole("button", { name: "Load source body" }).click();
  await expect(page.locator("#explorer-status")).toHaveText("Loading source for Root");
  await expect(page.locator("#explorer-status")).toHaveText("Source loaded for Root");
});

test("the context node has a visible non-color marker", async ({ page }) => {
  await serveIndex(page, fixtureIndex());
  await page.goto("/docs/index.html#view=graph&selected=root");
  await page.getByRole("button", { name: "Explore neighborhood" }).click();

  await expect(page.locator('[data-node-id="root"] .context-indicator')).toHaveText("◆");
});

test("design tokens and the narrow breakpoint match the accepted design language", async ({
  page,
}) => {
  await serveIndex(page, fixtureIndex());
  await page.setViewportSize({ width: 721, height: 800 });
  await page.goto("/docs/index.html");

  expect(await page.evaluate(() => matchMedia("(max-width: 720px)").matches)).toBe(false);
  const tokens = await page.evaluate(() => {
    const style = getComputedStyle(document.documentElement);
    return {
      border: style.getPropertyValue("--color-border").trim(),
      ghost: style.getPropertyValue("--color-graph-ghost").trim(),
      body: style.getPropertyValue("--font-body").trim(),
      mono: style.getPropertyValue("--font-mono").trim(),
    };
  });
  expect(tokens.border).toMatch(/^#(8a8886|797775)$/i);
  expect(tokens.ghost).toMatch(/^#(8a8886|797775)$/i);
  expect(tokens.body).toContain("Segoe UI");
  expect(tokens.mono).toContain("Consolas");
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth > document.documentElement.clientWidth,
    ),
  ).toBe(false);

  await page.setViewportSize({ width: 720, height: 800 });
  expect(await page.evaluate(() => matchMedia("(max-width: 720px)").matches)).toBe(true);
});

test("IME composition defers rerender until composition ends", async ({ page }) => {
  await serveIndex(page, fixtureIndex());
  await page.goto("/docs/index.html");
  let search = page.getByRole("searchbox", { name: "Search artifacts and knowledge surfaces" });
  await search.fill("root");
  await expect(page.locator("[data-search-match='true']")).not.toHaveCount(0);
  search = page.getByRole("searchbox", { name: "Search artifacts and knowledge surfaces" });
  const identityBefore = await search.evaluate((element) => {
    window.__searchElement = element;
    return true;
  });
  expect(identityBefore).toBe(true);
  const statusBeforeComposition = await page.getByRole("status").textContent();

  await search.evaluate((element) => {
    element.dispatchEvent(new CompositionEvent("compositionstart", { bubbles: true }));
    element.value = "設計なし";
    element.dispatchEvent(new InputEvent("input", { bubbles: true, isComposing: true }));
  });
  expect(await page.evaluate(() => window.__searchElement === document.getElementById("search"))).toBe(
    true,
  );
  await expect(page.getByRole("status")).toHaveText(statusBeforeComposition);

  await search.evaluate((element) => {
    element.dispatchEvent(new CompositionEvent("compositionend", { bubbles: true, data: "計" }));
    element.dispatchEvent(new InputEvent("input", { bubbles: true, inputType: "insertCompositionText" }));
  });
  await expect(page.getByRole("searchbox", { name: "Search artifacts and knowledge surfaces" })).toHaveValue("設計なし");
  await expect(page.getByRole("searchbox", { name: "Search artifacts and knowledge surfaces" })).toBeFocused();
  await expect(page.getByRole("status")).toContainText('No search results for "設計なし"');
});

test("context styling, fitting, and label ceilings preserve the highest-priority labels", async ({
  page,
}) => {
  const index = fixtureIndex({
    limits: {
      indexBytes: 5 * 1024 * 1024,
      artifacts: 1000,
      relationships: 5000,
      spatialNodes: 500,
      spatialEdges: 1000,
      visibleLabels: 1,
    },
    artifacts: [
      ...fixtureIndex().artifacts,
      {
        id: "outside",
        path: "docs/outside.md",
        title: "Outside",
        type: "design",
        status: "accepted",
        reviewSuggested: [{ by: "root", on: "2026-07-10", reason: "changed" }],
        links: [],
      },
    ],
  });
  await serveIndex(page, index);
  await page.goto("/docs/index.html#view=graph");
  await page.locator('[data-node-id="root"]').click();
  await page.getByRole("button", { name: "Explore neighborhood" }).click();

  await expect(page.locator('[data-node-id="root"]')).toHaveClass(/context/);
  await expect(page.locator('[data-node-id="child"]')).toHaveClass(/depth-1/);
  await expect(page.locator('[data-node-id="outside"]')).toHaveClass(/unrelated/);
  await page.locator('[data-node-id="outside"]').evaluate((element) => {
    element.tabIndex = 0;
    element.focus();
  });
  await expect(page.locator('[data-node-id="outside"]')).toBeFocused();
  const deEmphasizedFocus = await page.locator('[data-node-id="outside"]').evaluate((element) => {
    const computed = getComputedStyle(element);
    return {
      outlineStyle: computed.outlineStyle,
      outlineWidth: computed.outlineWidth,
      outlineOffset: computed.outlineOffset,
      boxShadow: computed.boxShadow,
    };
  });
  const visibleFocus =
    deEmphasizedFocus.outlineStyle !== "none" ||
    deEmphasizedFocus.boxShadow !== "none";
  expect(visibleFocus).toBe(true);
  if (deEmphasizedFocus.outlineStyle !== "none") {
    expect(Number.parseFloat(deEmphasizedFocus.outlineWidth)).toBeGreaterThanOrEqual(2);
    expect(Number.parseFloat(deEmphasizedFocus.outlineOffset)).toBeGreaterThanOrEqual(2);
  }
  await expect(page.locator('[data-node-id="root"] .visual-label')).toHaveText("Root");
  await expect(page.locator('[data-node-id="child"] .visual-label')).toHaveText("•");
  expect(await page.locator(".visualization svg").getAttribute("viewBox")).not.toBe("0 0 1000 700");

  const svg = page.locator("[data-graph-svg]");
  const fitViewBox = await svg.getAttribute("data-fit-viewbox");
  const fullViewBox = await svg.getAttribute("data-full-viewbox");
  await expect(svg).toHaveAttribute("data-zoom-tier", "neighborhood");
  await page.getByRole("button", { name: "Reset project view" }).click();
  await expect(svg).toHaveAttribute("viewBox", fullViewBox);
  await expect(svg).toHaveAttribute("data-zoom-tier", "overview");
  await page.getByRole("button", { name: "Fit neighborhood" }).click();
  await expect(svg).toHaveAttribute("viewBox", fitViewBox);
  await expect(svg).toHaveAttribute("data-zoom-tier", "neighborhood");
  expect(fitViewBox).not.toBe(fullViewBox);
  await page.getByRole("button", { name: "Show detail" }).click();
  await expect(svg).toHaveAttribute("data-zoom-tier", "detail");
  await expect(page.locator(".edge-label").first()).toBeVisible();
  await expect(page.locator('[data-node-id="outside"] .health-marker')).toBeVisible();
});

test("selected and context titles remain visible without relying on clipped node labels", async ({
  page,
}) => {
  const title = "A deliberately long architecture title that must remain fully readable";
  const index = fixtureIndex();
  index.artifacts[0].title = title;
  await serveIndex(page, index);
  await page.goto("/docs/index.html#view=graph");

  await page.locator('[data-node-id="root"]').click();
  await expect(page.locator(".current-title")).toContainText(title);
  await page.getByRole("button", { name: "Explore neighborhood" }).click();
  await expect(page.getByRole("toolbar", { name: "Projection controls" })).toContainText(
    `Context: ${title}`,
  );
});

test("an empty index renders a stable first-run recovery state", async ({ page }) => {
  await serveIndex(
    page,
    fixtureIndex({ rootId: null, artifactTypes: [], artifacts: [], surfaces: [] }),
  );
  await page.goto("/docs/index.html");

  const emptyState = page.locator(".notice");
  await expect(emptyState).toContainText("No indexed artifacts yet");
  await expect(emptyState).toContainText("docs-graph.py derive");
  await expect(page.getByText("No standalone knowledge surfaces were discovered.")).toBeVisible();
  await expect(page.locator("#app")).toHaveAttribute("data-state", "ready");
  await expect(page.locator("#app")).toHaveAttribute("data-load-state", "empty");
  await expect(page.locator('[role="status"]')).toHaveCount(1);
  await expect(page.getByRole("alert")).toHaveCount(0);
});

test("a spatial layout failure preserves Browse recovery and relationship access", async ({
  page,
}) => {
  await serveIndex(page, fixtureIndex());
  await page.goto("/docs/index.html");
  await page.evaluate(() => {
    window.DocsExplorerCore.deterministicLayout = () => {
      throw new Error("layout failed");
    };
  });

  await page.getByRole("tab", { name: "Graph" }).click();

  await expect(page.getByRole("alert")).toContainText("DOC.LAYOUT.UNAVAILABLE");
  await expect(page.getByRole("heading", { name: /Visible relationships/ })).toBeVisible();
  await page.getByRole("button", { name: "Return to Browse" }).click();
  await expect(page.getByRole("tab", { name: "Index" })).toHaveAttribute(
    "aria-selected",
    "true",
  );
});

test("forced-colors mode preserves focus, selection, and search-match affordances", async ({
  page,
  browserName,
}) => {
  test.skip(browserName !== "chromium", "Forced-colors emulation is Chromium-only.");
  await page.emulateMedia({ forcedColors: "active" });
  await serveIndex(page, fixtureIndex());
  await page.goto("/docs/index.html#view=graph");
  const auditSurface = page.locator('.surface-card[data-kind="audit"]');
  await expect(auditSurface).toHaveCSS("border-style", "double");
  await expect(auditSurface.getByText("audit", { exact: true })).toBeVisible();
  const search = page.getByRole("searchbox", { name: "Search artifacts and knowledge surfaces" });
  await search.fill("root");
  const match = page.locator(".node-control[data-search-match='true']").first();
  await match.click();

  await expect(match).toBeFocused();
  expect(await match.evaluate((element) => getComputedStyle(element).outlineStyle)).toBe("double");
  await expect(match.locator(".match-indicator")).toBeVisible();
  await page.getByRole("button", { name: "Explore neighborhood" }).click();
  const contextNode = page.locator('[data-node-id="root"].node-control.context');
  await expect(contextNode).toHaveCSS("border-style", "double");
  await expect(contextNode.locator(".context-indicator")).toBeVisible();
  const selectedTab = page.getByRole("tab", { name: "Graph" });
  expect(await selectedTab.evaluate((element) => getComputedStyle(element).outlineStyle)).not.toBe("double");
  expect(await selectedTab.evaluate((element) => getComputedStyle(element, "::after").content)).not.toBe("none");

  await page.getByRole("tab", { name: "3D" }).click();
  const spatial = page.getByRole("region", { name: "Spatial 3D project graph" });
  expect(
    await spatial.evaluate((element) => getComputedStyle(element).outlineStyle),
  ).not.toBe("double");
  await expect(page.locator("[data-spatial-node] .node-control[data-selected='true']")).toHaveCount(1);
  await expect(page.locator("[data-spatial-node] .node-control.context")).toHaveCount(1);
});

test("each browser resource ceiling fails closed at the correct layer", async ({ page }) => {
  let activeIndex = fixtureIndex();
  await page.route("**/docs-index.js", async (route) => {
    await route.fulfill({
      contentType: "text/javascript",
      body: `window.DOCS_INDEX = ${JSON.stringify(activeIndex)};`,
    });
  });
  const cases = [
    ["indexBytes", { indexBytes: 1 }, "DOC.INDEX.LIMIT_EXCEEDED"],
    ["artifacts", { artifacts: 1 }, "DOC.INDEX.LIMIT_EXCEEDED"],
    ["relationships", { relationships: 0 }, "DOC.INDEX.LIMIT_EXCEEDED"],
    ["surfaces", { surfaces: 2 }, "DOC.INDEX.LIMIT_EXCEEDED"],
    ["spatialNodes", { spatialNodes: 1 }, "DOC.INDEX.LIMIT_EXCEEDED"],
    ["spatialEdges", { spatialEdges: 0 }, "DOC.INDEX.LIMIT_EXCEEDED"],
  ];
  for (const [name, limit, code] of cases) {
    activeIndex = fixtureIndex({
      limits: { ...fixtureIndex().limits, ...limit },
    });
    await page.goto(`/docs/index.html?limit=${name}#view=graph`);
    await expect(page.getByRole("alert")).toContainText(code);
    if (name.startsWith("spatial")) {
      await expect(page.getByRole("tree", { name: "Project artifacts" })).toBeVisible();
    } else {
      await expect(page.locator("[data-node-id]")).toHaveCount(0);
    }
  }
});

test("oversized source bodies fail without replacing metadata", async ({ page }) => {
  await serveIndex(page, fixtureIndex());
  await page.route("**/root.md", (route) =>
    route.fulfill({ contentType: "text/markdown", body: "x".repeat(1024 * 1024 + 1) }),
  );
  await page.goto("/docs/index.html");
  await page.locator('[data-artifact-card] [data-action="select"][data-id="root"]').click();
  await page.getByRole("button", { name: "Load source body" }).click();

  await expect(page.getByRole("alert")).toContainText("DOC.SOURCE.TOO_LARGE");
  await expect(page.locator("#details-heading")).toHaveText("Root");
});

test("source bodies at the exact byte ceiling remain loadable", async ({ page, browserName }) => {
  test.skip(browserName !== "chromium", "The exact 1 MiB DOM boundary is covered once; overflow remains cross-browser.");
  const source = "x".repeat(1024 * 1024);
  await serveIndex(page, withRootSource(fixtureIndex(), source));
  await page.route("**/root.md", (route) =>
    route.fulfill({ contentType: "text/markdown", body: source }),
  );
  await page.goto("/docs/index.html");
  await page.locator('[data-artifact-card] [data-action="select"][data-id="root"]').click();
  await page.getByRole("button", { name: "Load source body" }).click();

  await expect.poll(
    () => page.locator(".details-panel pre").textContent().then((text) => text.length),
    { timeout: 15_000 },
  )
    .toBe(1024 * 1024);
  await expect(page.getByRole("alert")).toHaveCount(0);
});

test("source byte ceiling is enforced when content length understates the body", async ({ page }) => {
  await serveIndex(page, fixtureIndex());
  await page.route("**/root.md", (route) =>
    route.fulfill({
      headers: { "content-type": "text/markdown", "content-length": "1" },
      body: "x".repeat(1024 * 1024 + 1),
    }),
  );
  await page.goto("/docs/index.html");
  await page.locator('[data-artifact-card] [data-action="select"][data-id="root"]').click();
  await page.getByRole("button", { name: "Load source body" }).click();

  await expect(page.getByRole("alert")).toContainText("DOC.SOURCE.TOO_LARGE");
  await expect(page.locator("#details-heading")).toHaveText("Root");
});

test("hostile source is rendered inert as text", async ({ page }) => {
  const source = '<img src="x" onerror="window.__sourceExecuted=true">';
  await serveIndex(page, withRootSource(fixtureIndex(), source));
  await page.route("**/root.md", (route) =>
    route.fulfill({
      contentType: "text/markdown",
      body: source,
    }),
  );
  await page.goto("/docs/index.html");
  await page.locator('[data-artifact-card] [data-action="select"][data-id="root"]').click();
  await page.getByRole("button", { name: "Load source body" }).click();

  await expect(page.locator(".details-panel pre")).toContainText("<img");
  await expect(page.locator(".details-panel img")).toHaveCount(0);
  expect(await page.evaluate(() => window.__sourceExecuted)).toBeUndefined();
});

test("late source results are ignored after selection changes", async ({ page }) => {
  await page.addInitScript(() => {
    const nativeFetch = window.fetch;
    window.__sourceAbortCount = 0;
    window.fetch = (input, init = {}) => {
      init.signal?.addEventListener("abort", () => { window.__sourceAbortCount += 1; }, {
        once: true,
      });
      return nativeFetch(input, init);
    };
  });
  await serveIndex(page, fixtureIndex());
  let release;
  let requestStarted;
  const started = new Promise((resolve) => { requestStarted = resolve; });
  const released = new Promise((resolve) => { release = resolve; });
  let requestCompleted;
  const completed = new Promise((resolve) => { requestCompleted = resolve; });
  await page.route("**/root.md", async (route) => {
    requestStarted();
    await released;
    await route.fulfill({ contentType: "text/markdown", body: "late root source" }).catch(() => {});
    requestCompleted();
  });
  await page.goto("/docs/index.html");
  await page.locator('[data-artifact-card] [data-action="select"][data-id="root"]').click();
  await page.getByRole("button", { name: "Load source body" }).click();
  await started;
  await page.locator('[data-artifact-card] [data-action="select"][data-id="child"]').click();
  await expect.poll(() => page.evaluate(() => window.__sourceAbortCount)).toBe(1);
  release();
  await completed;

  await expect(page.locator("#details-heading")).toHaveText("Child");
  await expect(page.locator(".details-panel pre")).toHaveCount(0);
});

test("a same-artifact retry cannot be overwritten by an older request", async ({ page }) => {
  await page.addInitScript(() => {
    const nativeFetch = window.fetch;
    window.__sourceAbortCount = 0;
    window.fetch = (input, init = {}) => {
      init.signal?.addEventListener("abort", () => { window.__sourceAbortCount += 1; }, {
        once: true,
      });
      return nativeFetch(input, init);
    };
  });
  await serveIndex(page, withRootSource(fixtureIndex(), "newer source"));
  let releaseFirst;
  const firstReleased = new Promise((resolve) => { releaseFirst = resolve; });
  let firstStarted;
  const started = new Promise((resolve) => { firstStarted = resolve; });
  let firstCompleted;
  const completed = new Promise((resolve) => { firstCompleted = resolve; });
  let requests = 0;
  await page.route("**/root.md", async (route) => {
    requests += 1;
    if (requests === 1) {
      firstStarted();
      await firstReleased;
      await route.fulfill({ contentType: "text/markdown", body: "older source" }).catch(() => {});
      firstCompleted();
      return;
    }
    await route.fulfill({ contentType: "text/markdown", body: "newer source" });
  });
  await page.goto("/docs/index.html");
  await page.locator('[data-artifact-card] [data-action="select"][data-id="root"]').click();
  await page.getByRole("button", { name: "Load source body" }).click();
  await started;
  await page.locator('[data-artifact-card] [data-action="select"][data-id="child"]').click();
  await expect.poll(() => page.evaluate(() => window.__sourceAbortCount)).toBe(1);
  await page.locator('[data-artifact-card] [data-action="select"][data-id="root"]').click();
  await page.getByRole("button", { name: "Load source body" }).click();
  await expect(page.locator(".details-panel pre")).toContainText("newer source");
  releaseFirst();
  await completed;
  await expect(page.locator(".details-panel pre")).toContainText("newer source");
  await expect(page.locator(".details-panel pre")).not.toContainText("older source");
});

test("source fetch deadline aborts and preserves metadata", async ({ page, browserName }) => {
  test.skip(browserName !== "chromium", "The browser deadline integration path is covered once.");
  test.setTimeout(12000);
  await serveIndex(page, fixtureIndex());
  await page.route("**/root.md", async (route) => {
    await new Promise((resolve) => setTimeout(resolve, 6000));
    await route.fulfill({ contentType: "text/markdown", body: "too late" }).catch(() => {});
  });
  await page.goto("/docs/index.html");
  await page.locator('[data-artifact-card] [data-action="select"][data-id="root"]').click();
  await page.getByRole("button", { name: "Load source body" }).click();

  await expect(page.getByRole("alert")).toContainText("DOC.SOURCE.TIMEOUT", {
    timeout: 7000,
  });
  await expect(page.locator("#details-heading")).toHaveText("Root");
});

test("source hash mismatch and unapproved source paths are rejected before render", async ({ page }) => {
  const badHash = withRootSource(fixtureIndex(), "expected source");
  await serveIndex(page, badHash);
  await page.route("**/root.md", (route) =>
    route.fulfill({ contentType: "text/markdown", body: "tampered source" }),
  );
  await page.goto("/docs/index.html");
  await page.locator('[data-artifact-card] [data-action="select"][data-id="root"]').click();
  await page.getByRole("button", { name: "Load source body" }).click();
  await expect(page.getByRole("alert")).toContainText("DOC.SOURCE.INTEGRITY_MISMATCH");
  await expect(page.locator(".details-panel pre")).toHaveCount(0);

  const escaped = fixtureIndex();
  escaped.artifacts[0].path = "../outside.md";
  escaped.artifacts[0].sourceSha256 = sourceHash("outside");
  await serveIndex(page, escaped);
  await page.goto("/docs/index.html");
  await page.locator('[data-artifact-card] [data-action="select"][data-id="root"]').click();
  await page.getByRole("button", { name: "Load source body" }).click();
  await expect(page.getByRole("alert")).toContainText("DOC.SOURCE.PATH_REJECTED");
});

test("index bootstrap deadline produces a stable local recovery code", async ({
  page,
  browserName,
}) => {
  test.skip(browserName !== "chromium", "Deadline wall-clock proof is pinned to Chromium.");
  test.setTimeout(15000);
  await page.route("**/docs-index.js", () => new Promise(() => {}));
  await page.goto("/docs/index.html", { waitUntil: "commit" });

  await expect(page.getByRole("alert")).toContainText("DOC.INDEX.UNAVAILABLE", {
    timeout: 10000,
  });
  await expect(page.locator("main#main")).toBeVisible();
  await expect(page.getByRole("button", { name: "Retry loading" })).toBeVisible();
});

test("late index completion cannot replace the bootstrap timeout recovery shell", async ({
  page,
  browserName,
}) => {
  test.skip(browserName !== "chromium", "Deadline wall-clock proof is pinned to Chromium.");
  test.setTimeout(15000);
  await page.route("**/docs-index.js", async (route) => {
    await new Promise((resolve) => setTimeout(resolve, 5500));
    await route.fulfill({
      contentType: "application/javascript",
      body: `window.DOCS_INDEX = ${JSON.stringify(fixtureIndex())};`,
    }).catch(() => {});
  });
  await page.goto("/docs/index.html", { waitUntil: "commit" });

  await expect(page.getByRole("alert")).toContainText("DOC.INDEX.UNAVAILABLE", {
    timeout: 7000,
  });
  await page.waitForTimeout(1500);
  await expect(page.getByRole("alert")).toContainText("DOC.INDEX.UNAVAILABLE");
  await expect(page.getByRole("tab", { name: "Index" })).toHaveCount(0);
});

test("index recovery shell retries loading without losing the main landmark", async ({
  page,
}) => {
  let attempts = 0;
  await page.route("**/docs-index.js", async (route) => {
    attempts += 1;
    if (attempts === 1) {
      await route.abort();
      return;
    }
    await route.fulfill({
      contentType: "application/javascript",
      body: `window.DOCS_INDEX = ${JSON.stringify(fixtureIndex())};`,
    });
  });
  await page.goto("/docs/index.html");
  await expect(page.getByRole("alert")).toContainText("DOC.INDEX.UNAVAILABLE");
  await expect(page.locator("main#main")).toBeVisible();

  await page.getByRole("button", { name: "Retry loading" }).click();

  await expect(page.getByRole("tab", { name: "Index" })).toHaveAttribute(
    "aria-selected",
    "true",
  );
  await expect(page.locator("main#main")).toBeVisible();
});
