// mockup_harness_audit.test.js - DC-200: an in-artifact audit that computes while the page is
// hidden reports numbers about nothing.
//
// Measured (D3, 2026-09-13): a harness gating selector matched the element carrying the harness
// state (`[data-restore]{display:none}` on `<body data-restore=...>`); the whole page was
// display:none from D1 to D3 while every contrast pair and target size still computed, and a
// headless sweep that read only the verdict strip passed. The template's audit() must assert a
// non-zero page box BEFORE reading any number, and say so in the verdict when it is zero.
//
// Dependency-free: the template's <script> runs in a vm context over a minimal DOM shim whose
// page box is the one thing the test controls. Same approach as tools/verify-explainer-render.js.
"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const ROOT = path.resolve(__dirname, "..", "..");
const TEMPLATE = path.join(ROOT, "pack", "templates", "mockup-harness.template.html");

function makeElement(id) {
  const el = {
    id, dataset: {}, style: {}, textContent: "", className: "", innerHTML: "", value: "", checked: false,
    listeners: {},
    addEventListener(type, fn) { (this.listeners[type] = this.listeners[type] || []).push(fn); },
    appendChild() {}, remove() {},
    getBoundingClientRect() { return { width: 0, height: 0, top: 0, left: 0 }; },
  };
  return el;
}

function runAudit({ pageBox }) {
  const html = fs.readFileSync(TEMPLATE, "utf8");
  const scripts = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map((m) => m[1]);
  assert.ok(scripts.length >= 1, "the template carries its audit script inline");
  const elements = {};
  const byId = (id) => (elements[id] = elements[id] || makeElement(id));
  const root = makeElement("html");
  const body = makeElement("body");
  const main = makeElement("main");
  main.getBoundingClientRect = () => ({ width: pageBox.width, height: pageBox.height, top: 0, left: 0 });
  body.getBoundingClientRect = main.getBoundingClientRect;
  const sandbox = {
    console,
    document: {
      documentElement: root,
      body,
      getElementById: byId,
      querySelector: (sel) => (sel === "main" ? main : null),
      querySelectorAll: () => [],
      createElement: () => makeElement("span"),
    },
    getComputedStyle: () => ({
      getPropertyValue: (name) => ({ "--ink": "#111", "--canvas": "#fff", "--ink-muted": "#666", "--surface-raised": "#eee",
        "--accent-ink": "#fff", "--accent": "#0055cc", "--danger": "#b00020", "--line": "#ddd" }[name] || ""),
      color: "rgb(17, 17, 17)",
    }),
  };
  sandbox.window = sandbox;
  const context = vm.createContext(sandbox);
  for (const src of scripts) vm.runInContext(src, context, { filename: "mockup-harness", timeout: 5000 });
  return { verdict: byId("h-verdict"), rows: byId("audit-rows"), targets: byId("audit-targets") };
}

test("a zero page box is reported as not rendered and no number is computed", () => {
  const { verdict, rows } = runAudit({ pageBox: { width: 0, height: 0 } });
  assert.match(verdict.textContent, /not rendered|0x0|page box/i, verdict.textContent);
  assert.match(verdict.className, /fail/, "an unrendered page is a FAIL, never a pass");
  assert.equal(rows.innerHTML, "", "no contrast row may be reported for a hidden page");
});

test("a rendered page computes the audit as before", () => {
  const { verdict, rows } = runAudit({ pageBox: { width: 1280, height: 800 } });
  assert.match(verdict.textContent, /contrast fail/, verdict.textContent);
  assert.ok(rows.innerHTML.includes("<tr>"), "contrast rows are computed for a rendered page");
});
