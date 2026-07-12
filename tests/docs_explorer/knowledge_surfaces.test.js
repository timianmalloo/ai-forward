"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");

const ROOT = path.resolve(__dirname, "..", "..");

function read(relativePath) {
  return fs.readFileSync(path.join(ROOT, relativePath), "utf8");
}

function assertAccessibleAuditSurface(source) {
  assert.match(source, /head\.setAttribute\("aria-expanded","false"\)/);
  assert.match(source, /head\.setAttribute\("aria-controls",panelId\)/);
  assert.match(source, /searchLabel\.htmlFor="audit-search"/);
  assert.match(source, /fieldLabel\("session","audit-session"\)/);
  assert.match(source, /fieldLabel\("from","audit-from"\)/);
  assert.match(source, /fieldLabel\("to","audit-to"\)/);
  assert.match(source, /setAttribute\("aria-live","polite"\)/);
  assert.match(source, /prefers-reduced-motion: no-preference/);
  assert.match(source, /forced-colors: active/);
  assert.match(source, /window\.__auditExplorerLoadTimer = setTimeout/);
  assert.match(source, /navigator\.clipboard\.writeText/);
  assert.doesNotMatch(source, /unpkg\.com|window\.React|ReactDOM|window\.htm/);
  assert.doesNotMatch(source, /\.innerHTML\s*=/);
  assert.doesNotMatch(source, /--k-skill|--c-architecture|--ok:|--warn:|--bad:/);
}

test("audit viewer template exposes accessible disclosure, filters, feedback, and fallback states", () => {
  assertAccessibleAuditSurface(read("pack/templates/audit-explorer.template.html"));
});

test("rendered audit viewer preserves the template accessibility contract", () => {
  assertAccessibleAuditSurface(read("docs/audit/index.html"));
});

test("documentation hub identifies raw markdown destinations before navigation", () => {
  const source = read("docs/_site/index.html");
  const markdownLinks = [...source.matchAll(/<a class="card" href="([^"]+\.md)">([\s\S]*?)<\/a>/g)];

  assert.equal(markdownLinks.length, 8);
  for (const [, , body] of markdownLinks) {
    assert.match(body, /source<\/strong>/);
    assert.match(body, /View source \(\.md\)/);
  }
  assert.match(source, /forced-colors: active/);
});
