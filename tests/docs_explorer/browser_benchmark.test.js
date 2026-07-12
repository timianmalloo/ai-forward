"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const test = require("node:test");
const {
  CHROMIUM_ARGS,
  DEVICE_SCALE_FACTOR,
  ORBIT_FRAME_WINDOW_MILLISECONDS,
  THRESHOLDS,
  VIEWPORT,
  benchmarkPhase,
  corpusFingerprint,
  createBenchmarkIndex,
  percentile,
  safeServerFile,
} = require("./benchmark_docs_explorer");

test("browser benchmark corpus is deterministic and ceiling-sized", () => {
  const first = createBenchmarkIndex();
  const second = createBenchmarkIndex();
  const relationships = first.artifacts.reduce(
    (total, artifact) => total + artifact.links.length,
    0,
  );
  const relationshipIds = new Set(first.artifacts.flatMap((artifact) =>
    artifact.links.map((link) => `${artifact.id}|${link.rel}|${link.to}`)));

  assert.equal(first.artifacts.length, 500);
  assert.equal(relationships, 1000);
  assert.equal(relationshipIds.size, relationships);
  assert.equal(first.surfaces.length, 100);
  assert.equal(corpusFingerprint(first), corpusFingerprint(second));
  assert.equal(
    corpusFingerprint(first),
    "f4b34a29d2f836957f7fe24d0424444ac515881b6618cdfdd759a302ccb3cdef",
  );
});

test("browser benchmark percentile interpolates deterministically", () => {
  assert.equal(percentile([10, 20, 30, 40, 50], 0.75), 40);
  assert.equal(percentile([10, 20, 30, 40], 0.75), 32.5);
});

test("browser benchmark thresholds encode the accepted performance budget", () => {
  assert.deepEqual(THRESHOLDS, {
    usable2dShellP75Milliseconds: 2000,
    selectionSearchP75Milliseconds: 100,
    initial2dLayoutP75Milliseconds: 500,
    initialSpatialP75Milliseconds: 500,
    minimumOrbitFramesPerSecond: 30,
  });
});

test("browser benchmark environment encodes the accepted deterministic viewport and renderer", () => {
  assert.deepEqual(VIEWPORT, { width: 1366, height: 768 });
  assert.equal(DEVICE_SCALE_FACTOR, 1);
  assert.equal(ORBIT_FRAME_WINDOW_MILLISECONDS, 1000);
  assert.deepEqual(CHROMIUM_ARGS, [
    "--disable-background-timer-throttling",
    "--disable-backgrounding-occluded-windows",
    "--disable-extensions",
    "--disable-renderer-backgrounding",
    "--use-angle=swiftshader",
  ]);
});

test("browser benchmark phases fail with stable deadline codes", async () => {
  let cleanupFinished = false;
  await assert.rejects(
    benchmarkPhase(
      "DOC.BENCHMARK.TEST_TIMEOUT",
      5,
      () => new Promise(() => {}),
      async () => {
        await new Promise((resolve) => setTimeout(resolve, 5));
        cleanupFinished = true;
      },
    ),
    (error) => {
      assert.equal(error.code, "DOC.BENCHMARK.TEST_TIMEOUT");
      assert.match(error.message, /^DOC\.BENCHMARK\.TEST_TIMEOUT /);
      assert.equal(cleanupFinished, true);
      return true;
    },
  );
});

test("browser benchmark server rejects paths outside its root and linked files", (t) => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "aif-browser-benchmark-"));
  t.after(() => fs.rmSync(root, { force: true, recursive: true }));
  const regular = path.join(root, "index.html");
  fs.writeFileSync(regular, "ok", "utf8");

  assert.equal(safeServerFile(root, regular), fs.realpathSync(regular));
  assert.equal(safeServerFile(root, path.join(root, "..", "outside.html")), null);

  const linked = path.join(root, "linked.html");
  try {
    fs.symlinkSync(regular, linked, "file");
    assert.equal(safeServerFile(root, linked), null);
  } catch (error) {
    if (!["EPERM", "EACCES"].includes(error.code)) throw error;
    t.skip(`Symlink containment check requires link privileges: ${error.code}`);
  }
});
