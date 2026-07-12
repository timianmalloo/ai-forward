"use strict";

const crypto = require("node:crypto");
const fs = require("node:fs");
const http = require("node:http");
const os = require("node:os");
const path = require("node:path");
const { execFileSync } = require("node:child_process");
const { chromium } = require("playwright");

const ROOT = path.resolve(__dirname, "..", "..");
const SEED = 20260710;
const ARTIFACTS = 500;
const RELATIONSHIPS = 1000;
const SURFACES = 100;
const COLD_RUNS = 5;
const WARM_RUNS = 5;
const VIEWPORT = Object.freeze({ width: 1366, height: 768 });
const DEVICE_SCALE_FACTOR = 1;
const ORBIT_FRAME_WINDOW_MILLISECONDS = 1000;
const CHROMIUM_ARGS = Object.freeze([
  "--disable-background-timer-throttling",
  "--disable-backgrounding-occluded-windows",
  "--disable-extensions",
  "--disable-renderer-backgrounding",
  "--use-angle=swiftshader",
]);
const DEADLINES = Object.freeze({
  serverStartMilliseconds: 10000,
  browserLaunchMilliseconds: 30000,
  browserConnectMilliseconds: 10000,
  pageMilliseconds: 30000,
  contextCloseMilliseconds: 10000,
  browserCloseMilliseconds: 15000,
  browserServerCloseMilliseconds: 15000,
  serverCloseMilliseconds: 10000,
});
const THRESHOLDS = Object.freeze({
  usable2dShellP75Milliseconds: 2000,
  selectionSearchP75Milliseconds: 100,
  initial2dLayoutP75Milliseconds: 500,
  initialSpatialP75Milliseconds: 500,
  minimumOrbitFramesPerSecond: 30,
});

function createBenchmarkIndex() {
  const artifacts = Array.from({ length: ARTIFACTS }, (_, index) => ({
    id: `bench-${String(index).padStart(4, "0")}`,
    path: `docs/bench/bench-${String(index).padStart(4, "0")}.md`,
    title: `Benchmark artifact ${index}`,
    type: index % 2 ? "design" : "architecture",
    status: "accepted",
    summary: `Deterministic browser benchmark artifact ${index}.`,
    tags: [`lane-${index % 10}`],
    links: [],
  }));
  for (let edge = 0; edge < RELATIONSHIPS; edge += 1) {
    const sourceIndex = edge % ARTIFACTS;
    const relationshipSet = Math.floor(edge / ARTIFACTS);
    const source = artifacts[sourceIndex];
    const target = artifacts[(sourceIndex * 37 + relationshipSet * 101 + 11) % ARTIFACTS];
    source.links.push({ to: target.id, rel: "depends-on" });
  }
  return {
    schemaVersion: "docs-index/v2",
    project: "Docs Explorer Browser Benchmark",
    rootId: artifacts[0].id,
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
      spatialNodes: ARTIFACTS,
      spatialEdges: RELATIONSHIPS,
      visibleLabels: 150,
      surfaces: SURFACES,
    },
    surfaces: Array.from({ length: SURFACES }, (_, index) => ({
      id: `surface-${String(index).padStart(3, "0")}`,
      title: `Surface ${index}`,
      path: `docs/surfaces/surface-${index}.html`,
      description: `Benchmark surface ${index}.`,
    })),
    artifacts,
  };
}

function corpusFingerprint(index) {
  return crypto.createHash("sha256").update(JSON.stringify(index), "utf8").digest("hex");
}

function percentile(values, quantile) {
  const sorted = [...values].sort((left, right) => left - right);
  if (!sorted.length) return 0;
  const position = (sorted.length - 1) * quantile;
  const lower = Math.floor(position);
  const upper = Math.ceil(position);
  if (lower === upper) return sorted[lower];
  return sorted[lower] + (sorted[upper] - sorted[lower]) * (position - lower);
}

function benchmarkPhase(code, timeoutMilliseconds, operation, onTimeout) {
  let timer;
  let settled = false;
  return new Promise((resolve, reject) => {
    timer = setTimeout(async () => {
      if (settled) return;
      settled = true;
      const error = new Error(`${code} exceeded ${timeoutMilliseconds}ms`);
      error.code = code;
      try {
        await onTimeout?.();
      } catch (cleanupError) {
        error.cause = cleanupError;
      }
      reject(error);
    }, timeoutMilliseconds);
    Promise.resolve()
      .then(operation)
      .then(
        (value) => {
          if (settled) return;
          settled = true;
          resolve(value);
        },
        (error) => {
          if (settled) return;
          settled = true;
          reject(error);
        },
      )
      .finally(() => clearTimeout(timer));
  });
}

function windowsCaption() {
  if (process.platform !== "win32") return `${os.type()} ${os.release()}`;
  try {
    return execFileSync(
      "powershell",
      ["-NoProfile", "-Command", "(Get-CimInstance Win32_OperatingSystem).Caption"],
      { encoding: "utf8", windowsHide: true },
    ).trim();
  } catch {
    return `${os.type()} ${os.release()}`;
  }
}

function referenceEnvironment(browser) {
  const caption = windowsCaption();
  const architecture = os.arch() === "x64" ? "X64" : os.arch().toUpperCase();
  const hostCandidate =
    architecture === "X64" &&
    os.cpus().length === 4 &&
    caption.includes("Windows Server 2022");
  const metadata = hostCandidate ? azureInstanceMetadata() : null;
  const matched =
    hostCandidate &&
    metadata?.vmSize === "Standard_D4s_v5" &&
    metadata?.offer === "WindowsServer" &&
    metadata?.osType === "Windows";
  return {
    architecture,
    windowsCaption: caption,
    logicalProcessors: os.cpus().length,
    playwright: require("@playwright/test/package.json").version,
    browserName: "chromium",
    chromiumBuild: browser.version(),
    headless: true,
    gpuMode: "swiftshader",
    launchFlags: CHROMIUM_ARGS,
    viewport: VIEWPORT,
    deviceScaleFactor: DEVICE_SCALE_FACTOR,
    cpuSlowdown: 4,
    orbitFrameWindowMilliseconds: ORBIT_FRAME_WINDOW_MILLISECONDS,
    referenceEnvironmentMatched: matched,
    azureReferenceMetadata: metadata,
  };
}

function azureInstanceMetadata() {
  if (process.platform !== "win32") return null;
  try {
    const raw = execFileSync(
      "powershell",
      [
        "-NoProfile",
        "-Command",
        "$m = Invoke-RestMethod -Uri 'http://169.254.169.254/metadata/instance?api-version=2021-02-01' -Headers @{ Metadata = 'true' } -TimeoutSec 2; " +
          "[ordered]@{ vmSize = [string]$m.compute.vmSize; offer = [string]$m.compute.offer; sku = [string]$m.compute.sku; osType = [string]$m.compute.osType } | ConvertTo-Json -Compress",
      ],
      { encoding: "utf8", windowsHide: true },
    );
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

async function forceKillBrowser(browserServer) {
  if (!browserServer) return;
  try {
    await browserServer.kill();
  } catch (error) {
    if (browserServer.process().exitCode === null) throw error;
  }
}

function startServer() {
  const server = http.createServer((request, response) => {
    const pathname = decodeURIComponent(new URL(request.url, "http://127.0.0.1").pathname);
    const candidate = path.resolve(ROOT, `.${pathname}`);
    const safeCandidate = safeServerFile(ROOT, candidate);
    if (!safeCandidate) {
      response.writeHead(404);
      response.end("Not found");
      return;
    }
    const extension = path.extname(safeCandidate);
    const contentTypes = {
      ".html": "text/html; charset=utf-8",
      ".js": "text/javascript; charset=utf-8",
      ".css": "text/css; charset=utf-8",
    };
    response.writeHead(200, {
      "Content-Type": contentTypes[extension] || "application/octet-stream",
      "Cache-Control": "public, max-age=3600",
    });
    fs.createReadStream(safeCandidate).pipe(response);
  });
  return new Promise((resolve, reject) => {
    server.once("error", reject);
    server.listen(0, "127.0.0.1", () => {
      resolve({
        server,
        url: `http://127.0.0.1:${server.address().port}/docs/index.html`,
      });
    });
  });
}

function safeServerFile(root, candidate) {
  try {
    const relative = path.relative(root, candidate);
    if (!relative || relative.startsWith(`..${path.sep}`) || path.isAbsolute(relative)) {
      return null;
    }
    let current = root;
    for (const segment of relative.split(path.sep)) {
      current = path.join(current, segment);
      if (fs.lstatSync(current).isSymbolicLink()) return null;
    }
    if (!fs.statSync(candidate).isFile()) return null;
    const realRoot = fs.realpathSync(root);
    const realCandidate = fs.realpathSync(candidate);
    return realCandidate.startsWith(`${realRoot}${path.sep}`) ? realCandidate : null;
  } catch {
    return null;
  }
}

async function measurePage(browser, url, index, cacheMode, onTimeout) {
  let context;
  try {
    context = await benchmarkPhase(
      "DOC.BENCHMARK.CONTEXT_CREATE_TIMEOUT",
      DEADLINES.pageMilliseconds,
      () => browser.newContext({
        viewport: VIEWPORT,
        deviceScaleFactor: DEVICE_SCALE_FACTOR,
      }),
    );
    const page = await context.newPage();
    await page.route("**/docs-index.js", async (route) => {
      await route.fulfill({
        contentType: "text/javascript",
        body: `window.DOCS_INDEX = ${JSON.stringify(index)};`,
      });
    });
    const cdp = await context.newCDPSession(page);
    await cdp.send("Emulation.setCPUThrottlingRate", { rate: 4 });
    await cdp.send("Network.setCacheDisabled", { cacheDisabled: cacheMode === "cold" });
    const heapBefore = await cdp.send("Runtime.getHeapUsage");
    await page.addInitScript(() => {
      window.__docsExplorerBenchmarkStart = performance.now();
    });
    await page.goto(url, { waitUntil: "domcontentloaded" });
    await page.locator("#app[data-state='ready']").waitFor();
    await page.getByRole("tab", { name: "Browse" }).waitFor();
    const usable2dShellMilliseconds = await page.evaluate(
      () => performance.now() - window.__docsExplorerBenchmarkStart,
    );

    const initial2dLayoutMilliseconds = await measureProjection(page, "Graph", "Project graph");
    const selectionSearchMilliseconds = await page.evaluate(async () => {
      const search = document.querySelector('[type="search"]');
      const start = performance.now();
      search.value = "Benchmark artifact 499";
      search.dispatchEvent(new Event("input", { bubbles: true }));
      await new Promise((resolve) =>
        requestAnimationFrame(() => requestAnimationFrame(resolve)));
      return performance.now() - start;
    });
    const initialSpatialMilliseconds = await measureProjection(
      page,
      "Spatial 3D",
      "Spatial 3D project graph",
    );
    const minimumOrbitFramesPerSecond = await measureOrbitFrames(page);
    const heapAfter = await cdp.send("Runtime.getHeapUsage");
    return {
      cacheMode,
      usable2dShellMilliseconds,
      selectionSearchMilliseconds,
      initial2dLayoutMilliseconds,
      initialSpatialMilliseconds,
      minimumOrbitFramesPerSecond,
      heapDeltaBytes: heapAfter.usedSize - heapBefore.usedSize,
    };
  } finally {
    if (context) {
      await benchmarkPhase(
        "DOC.BENCHMARK.CONTEXT_CLOSE_TIMEOUT",
        DEADLINES.contextCloseMilliseconds,
        () => context.close(),
        onTimeout,
      );
    }
  }
}

async function measureProjection(page, tabName, regionName) {
  const start = await page.evaluate(() => performance.now());
  await page.getByRole("tab", { name: tabName }).click();
  await page.getByRole("region", { name: regionName }).waitFor();
  return page.evaluate((started) => performance.now() - started, start);
}

async function measureOrbitFrames(page) {
  return page.evaluate(async () => {
    const region = document.querySelector('[aria-label="Spatial 3D project graph"]');
    const rect = region.getBoundingClientRect();
    const centerX = rect.left + rect.width / 2;
    const centerY = rect.top + rect.height / 2;
    region.dispatchEvent(new PointerEvent("pointerdown", {
      bubbles: true,
      pointerId: 1,
      clientX: centerX,
      clientY: centerY,
    }));
    const frames = [];
    const started = performance.now();
    await new Promise((resolve) => {
      const tick = (time) => {
        frames.push(time);
        region.dispatchEvent(new PointerEvent("pointermove", {
          bubbles: true,
          pointerId: 1,
          clientX: centerX + Math.sin(time / 80) * 120,
          clientY: centerY + Math.cos(time / 90) * 80,
        }));
        if (time - started >= 1500) {
          region.dispatchEvent(new PointerEvent("pointerup", {
            bubbles: true,
            pointerId: 1,
            clientX: centerX,
            clientY: centerY,
          }));
          resolve();
          return;
        }
        requestAnimationFrame(tick);
      };
      requestAnimationFrame(tick);
    });
    let minimum = Number.POSITIVE_INFINITY;
    const frameWindowMilliseconds = 1000;
    for (let start = frames[0]; start <= frames.at(-1) - frameWindowMilliseconds; start += 100) {
      const count = frames.filter(
        (time) => time >= start && time < start + frameWindowMilliseconds,
      ).length;
      minimum = Math.min(minimum, count);
    }
    return Number.isFinite(minimum) ? minimum : 0;
  });
}

async function runBenchmark(outputPath) {
  const index = createBenchmarkIndex();
  let environment;
  let server;
  let browser;
  let browserServer;
  const cold = [];
  const warm = [];
  try {
    const started = await benchmarkPhase(
      "DOC.BENCHMARK.SERVER_START_TIMEOUT",
      DEADLINES.serverStartMilliseconds,
      startServer,
    );
    server = started.server;
    const url = started.url;
    browserServer = await benchmarkPhase(
      "DOC.BENCHMARK.BROWSER_LAUNCH_TIMEOUT",
      DEADLINES.browserLaunchMilliseconds,
      () => chromium.launchServer({
        args: CHROMIUM_ARGS,
        headless: true,
        timeout: DEADLINES.browserLaunchMilliseconds,
      }),
    );
    const killBrowser = () => forceKillBrowser(browserServer);
    browser = await benchmarkPhase(
      "DOC.BENCHMARK.BROWSER_CONNECT_TIMEOUT",
      DEADLINES.browserConnectMilliseconds,
      () => chromium.connect(browserServer.wsEndpoint()),
      killBrowser,
    );
    environment = referenceEnvironment(browser);
    for (let run = 0; run < COLD_RUNS; run += 1) {
      cold.push(await benchmarkPhase(
        "DOC.BENCHMARK.PAGE_TIMEOUT",
        DEADLINES.pageMilliseconds,
        () => measurePage(browser, url, index, "cold", killBrowser),
        killBrowser,
      ));
    }
    for (let run = 0; run < WARM_RUNS; run += 1) {
      warm.push(await benchmarkPhase(
        "DOC.BENCHMARK.PAGE_TIMEOUT",
        DEADLINES.pageMilliseconds,
        () => measurePage(browser, url, index, "warm", killBrowser),
        killBrowser,
      ));
    }
  } finally {
    if (browser) {
      await benchmarkPhase(
        "DOC.BENCHMARK.BROWSER_CLOSE_TIMEOUT",
        DEADLINES.browserCloseMilliseconds,
        () => browser.close(),
        () => forceKillBrowser(browserServer),
      );
    }
    if (browserServer) {
      await benchmarkPhase(
        "DOC.BENCHMARK.BROWSER_SERVER_CLOSE_TIMEOUT",
        DEADLINES.browserServerCloseMilliseconds,
        () => browserServer.close(),
        () => forceKillBrowser(browserServer),
      );
    }
    if (server) {
      await benchmarkPhase(
        "DOC.BENCHMARK.SERVER_CLOSE_TIMEOUT",
        DEADLINES.serverCloseMilliseconds,
        () => new Promise((resolve, reject) => {
          server.close((error) => error ? reject(error) : resolve());
          server.closeAllConnections?.();
        }),
      );
    }
  }
  const runs = [...cold, ...warm];
  const distribution = (values) => ({
    p50: percentile(values, 0.5),
    p75: percentile(values, 0.75),
    max: Math.max(...values),
  });
  const usable2dShell = cold.map((run) => run.usable2dShellMilliseconds);
  const selectionSearch = runs.map((run) => run.selectionSearchMilliseconds);
  const initial2dLayout = runs.map((run) => run.initial2dLayoutMilliseconds);
  const initialSpatial = runs.map((run) => run.initialSpatialMilliseconds);
  const summary = {
    usable2dShellP75Milliseconds: percentile(usable2dShell, 0.75),
    selectionSearchP75Milliseconds: percentile(selectionSearch, 0.75),
    initial2dLayoutP75Milliseconds: percentile(initial2dLayout, 0.75),
    initialSpatialP75Milliseconds: percentile(initialSpatial, 0.75),
    minimumOrbitFramesPerSecond: Math.min(
      ...runs.map((run) => run.minimumOrbitFramesPerSecond),
    ),
    distributions: {
      usable2dShellMilliseconds: distribution(usable2dShell),
      selectionSearchMilliseconds: distribution(selectionSearch),
      initial2dLayoutMilliseconds: distribution(initial2dLayout),
      initialSpatialMilliseconds: distribution(initialSpatial),
      heapDeltaBytes: distribution(runs.map((run) => run.heapDeltaBytes)),
    },
  };
  const localThresholdsPassed =
    summary.usable2dShellP75Milliseconds <= THRESHOLDS.usable2dShellP75Milliseconds &&
    summary.selectionSearchP75Milliseconds <= THRESHOLDS.selectionSearchP75Milliseconds &&
    summary.initial2dLayoutP75Milliseconds <= THRESHOLDS.initial2dLayoutP75Milliseconds &&
    summary.initialSpatialP75Milliseconds <= THRESHOLDS.initialSpatialP75Milliseconds &&
    summary.minimumOrbitFramesPerSecond >= THRESHOLDS.minimumOrbitFramesPerSecond;
  const proof = {
    schemaVersion: "docs-explorer-browser-benchmark/v1",
    passed: localThresholdsPassed && environment.referenceEnvironmentMatched,
    localThresholdsPassed,
    referenceBudgetProved: localThresholdsPassed && environment.referenceEnvironmentMatched,
    environment,
    corpus: {
      artifacts: ARTIFACTS,
      relationships: RELATIONSHIPS,
      surfaces: SURFACES,
      seed: SEED,
      sha256: corpusFingerprint(index),
    },
    runs: { cold: COLD_RUNS, warm: WARM_RUNS },
    thresholds: THRESHOLDS,
    summary,
    samples: { cold, warm },
  };
  fs.mkdirSync(path.dirname(outputPath), { recursive: true });
  fs.writeFileSync(outputPath, `${JSON.stringify(proof, null, 2)}\n`, "utf8");
  return proof;
}

if (require.main === module) {
  const outputIndex = process.argv.indexOf("--output");
  const outputPath = path.resolve(
    outputIndex >= 0 && process.argv[outputIndex + 1]
      ? process.argv[outputIndex + 1]
      : path.join(ROOT, "docs", "proof", "docs-explorer-browser-benchmark.local.json"),
  );
  runBenchmark(outputPath)
    .then((proof) => {
      process.stdout.write(`${JSON.stringify(proof.summary)}\n`);
      process.exitCode = proof.localThresholdsPassed ? 0 : 1;
    })
    .catch((error) => {
      console.error(error);
      process.exitCode = 1;
    });
}

module.exports = {
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
};
